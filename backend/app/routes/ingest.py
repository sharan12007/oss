"""Paper ingestion routes: fetch PubMed abstracts, extract entities, review/approve."""

from fastapi import APIRouter, HTTPException
from app.models import (
    IngestPubmedRequest, IngestReviewResponse, IngestReviewItem,
    IngestApproveRequest,
)
from app.database import read_query, write_query
from app.llm_service import get_llm_provider
from app.config import get_settings
import httpx
import json
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest")

# In-memory store for pending reviews (in production, use a database)
_pending_reviews: dict[str, IngestReviewResponse] = {}


# ─── PubMed Fetch ────────────────────────────────────────────────────────────

async def fetch_pubmed_abstract(pmid: str) -> dict:
    """Fetch title and abstract from PubMed E-utilities."""
    settings = get_settings()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
        "rettype": "abstract",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    xml_text = resp.text

    # Simple XML parsing for title and abstract
    import re

    title_match = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", xml_text, re.DOTALL)
    abstract_match = re.search(r"<AbstractText[^>]*>(.*?)</AbstractText>", xml_text, re.DOTALL)
    year_match = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", xml_text, re.DOTALL)

    title = title_match.group(1).strip() if title_match else f"PubMed Article {pmid}"
    abstract = abstract_match.group(1).strip() if abstract_match else ""
    year = int(year_match.group(1)) if year_match else None

    # Strip XML tags from extracted text
    title = re.sub(r"<[^>]+>", "", title)
    abstract = re.sub(r"<[^>]+>", "", abstract)

    return {"pmid": pmid, "title": title, "abstract": abstract, "year": year}


# ─── Entity Extraction ──────────────────────────────────────────────────────

async def extract_entities(title: str, abstract: str) -> dict:
    """Use LLM to extract biomedical entities and relationships from text."""
    llm = get_llm_provider()

    prompt = f"""Extract biomedical entities and their relationships from this PubMed article.

Title: {title}

Abstract: {abstract}

Return a JSON object with this exact structure:
{{
    "entities": [
        {{
            "type": "Gene|Protein|Disease|Mutation|Pathway",
            "name": "entity name",
            "id": "standard identifier if known (gene symbol, UniProt ID, DOID, etc.)",
            "properties": {{}}
        }}
    ],
    "relationships": [
        {{
            "type": "ASSOCIATED_WITH|HAS_MUTATION|ENCODES|INTERACTS_WITH|LINKED_TO|PART_OF|MENTIONS",
            "source": "source entity name or ID",
            "target": "target entity name or ID",
            "properties": {{}}
        }}
    ]
}}

Rules:
- Use standard gene symbols (BRCA1, TP53, etc.)
- Use standard disease ontology IDs if known
- Only extract entities clearly mentioned in the text
- Do not invent or hallucinate entities
- Be conservative: if unsure, omit the entity
"""

    try:
        result_json = await llm.generate_json(prompt, system="You are a biomedical named entity recognition system. Extract entities precisely from the provided text.")
        return json.loads(result_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM entity extraction: {e}")
        return {"entities": [], "relationships": []}


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/pubmed", response_model=IngestReviewResponse)
async def ingest_pubmed(request: IngestPubmedRequest):
    """Fetch a PubMed paper and extract entities for review."""
    pmid = request.pmid.strip()

    # Check if already in graph
    existing = await read_query(
        "MATCH (p:Publication {pmid: $pmid}) RETURN p", {"pmid": pmid}
    )

    # Fetch from PubMed
    try:
        paper = await fetch_pubmed_abstract(pmid)
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch PubMed article {pmid}: {str(e)}")

    if not paper["abstract"]:
        raise HTTPException(400, f"No abstract found for PubMed article {pmid}")

    # Extract entities using LLM
    extracted = await extract_entities(paper["title"], paper["abstract"])

    # Convert to review items
    entities = []
    for ent in extracted.get("entities", []):
        entities.append(IngestReviewItem(
            id=str(uuid.uuid4())[:8],
            type=ent.get("type", "Unknown"),
            label=ent.get("name", ""),
            properties={
                "extracted_id": ent.get("id", ""),
                **ent.get("properties", {}),
            },
        ))

    relationships = []
    for rel in extracted.get("relationships", []):
        relationships.append(IngestReviewItem(
            id=str(uuid.uuid4())[:8],
            type=rel.get("type", "RELATED"),
            label=f"{rel.get('source', '')} → {rel.get('target', '')}",
            source=rel.get("source", ""),
            target=rel.get("target", ""),
            properties=rel.get("properties", {}),
        ))

    review = IngestReviewResponse(
        pmid=pmid,
        title=paper["title"],
        entities=entities,
        relationships=relationships,
    )

    # Store for later approval
    _pending_reviews[pmid] = review

    return review


@router.post("/approve")
async def approve_ingestion(request: IngestApproveRequest):
    """Approve extracted entities and add them to the graph."""
    pmid = request.pmid

    if pmid not in _pending_reviews:
        raise HTTPException(404, f"No pending review for PMID {pmid}")

    review = _pending_reviews[pmid]

    # Add the publication node
    await write_query(
        """MERGE (pub:Publication {pmid: $pmid})
           SET pub.title = $title""",
        {"pmid": pmid, "title": review.title},
    )

    approved_entities = {e.id: e for e in review.entities if e.id in request.approved_entity_ids}
    approved_rels = {r.id: r for r in review.relationships if r.id in request.approved_relationship_ids}

    # Add approved entities and create MENTIONS relationships
    for ent in approved_entities.values():
        ent_id = ent.properties.get("extracted_id", ent.label)

        if ent.type == "Gene":
            await write_query(
                """MERGE (g:Gene {symbol: $symbol})
                   SET g.name = coalesce(g.name, $name)
                   WITH g
                   MATCH (pub:Publication {pmid: $pmid})
                   MERGE (pub)-[:MENTIONS]->(g)""",
                {"symbol": ent_id or ent.label, "name": ent.label, "pmid": pmid},
            )
        elif ent.type == "Disease":
            await write_query(
                """MERGE (d:Disease {id: $id})
                   SET d.name = coalesce(d.name, $name)
                   WITH d
                   MATCH (pub:Publication {pmid: $pmid})
                   MERGE (pub)-[:MENTIONS]->(d)""",
                {"id": ent_id or ent.label, "name": ent.label, "pmid": pmid},
            )
        elif ent.type == "Mutation":
            await write_query(
                """MERGE (m:Mutation {id: $id})
                   SET m.hgvs = coalesce(m.hgvs, $hgvs)
                   WITH m
                   MATCH (pub:Publication {pmid: $pmid})
                   MERGE (pub)-[:MENTIONS]->(m)""",
                {"id": ent_id or ent.label, "hgvs": ent.label, "pmid": pmid},
            )

    # Add approved relationships
    for rel in approved_rels.values():
        if rel.type == "ASSOCIATED_WITH":
            await write_query(
                """MATCH (g:Gene {symbol: $source}), (d:Disease)
                   WHERE d.name = $target OR d.id = $target
                   MERGE (g)-[:ASSOCIATED_WITH {score: 0.5}]->(d)""",
                {"source": rel.source, "target": rel.target},
            )

    # Clean up
    del _pending_reviews[pmid]

    return {"status": "success", "pmid": pmid, "entities_added": len(approved_entities), "relationships_added": len(approved_rels)}


@router.get("/pending")
async def get_pending_reviews():
    """Get all pending review items."""
    return {pmid: review.model_dump() for pmid, review in _pending_reviews.items()}
