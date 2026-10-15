"""Neo4j schema setup: constraints, indexes, and vector index."""

from app.database import write_query
import logging

logger = logging.getLogger(__name__)

SCHEMA_STATEMENTS = [
    # ─── Uniqueness Constraints ───────────────────────────────────────────────
    "CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE",
    "CREATE CONSTRAINT protein_uniprot IF NOT EXISTS FOR (p:Protein) REQUIRE p.uniprot_id IS UNIQUE",
    "CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT mutation_id IF NOT EXISTS FOR (m:Mutation) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT pathway_reactome IF NOT EXISTS FOR (pw:Pathway) REQUIRE pw.reactome_id IS UNIQUE",
    "CREATE CONSTRAINT publication_pmid IF NOT EXISTS FOR (pub:Publication) REQUIRE pub.pmid IS UNIQUE",

    # ─── Indexes for Search ───────────────────────────────────────────────────
    "CREATE INDEX gene_name IF NOT EXISTS FOR (g:Gene) ON (g.name)",
    "CREATE INDEX protein_name IF NOT EXISTS FOR (p:Protein) ON (p.name)",
    "CREATE INDEX disease_name IF NOT EXISTS FOR (d:Disease) ON (d.name)",
    "CREATE INDEX mutation_hgvs IF NOT EXISTS FOR (m:Mutation) ON (m.hgvs)",
    "CREATE INDEX pathway_name IF NOT EXISTS FOR (pw:Pathway) ON (pw.name)",
    "CREATE INDEX publication_title IF NOT EXISTS FOR (pub:Publication) ON (pub.title)",
    "CREATE INDEX publication_year IF NOT EXISTS FOR (pub:Publication) ON (pub.year)",

    # ─── Full-Text Search Indexes ─────────────────────────────────────────────
    # These are created separately since they use different syntax
]

FULLTEXT_INDEXES = [
    """CREATE FULLTEXT INDEX gene_fulltext IF NOT EXISTS
       FOR (g:Gene) ON EACH [g.symbol, g.name]""",
    """CREATE FULLTEXT INDEX disease_fulltext IF NOT EXISTS
       FOR (d:Disease) ON EACH [d.name, d.description]""",
    """CREATE FULLTEXT INDEX protein_fulltext IF NOT EXISTS
       FOR (p:Protein) ON EACH [p.name, p.uniprot_id]""",
    """CREATE FULLTEXT INDEX mutation_fulltext IF NOT EXISTS
       FOR (m:Mutation) ON EACH [m.id, m.hgvs]""",
    """CREATE FULLTEXT INDEX publication_fulltext IF NOT EXISTS
       FOR (pub:Publication) ON EACH [pub.title, pub.abstract]""",
]

# Vector index for publication embeddings (Neo4j 5.11+)
VECTOR_INDEX = """
CREATE VECTOR INDEX publication_embedding IF NOT EXISTS
FOR (pub:Publication)
ON (pub.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}
"""


async def setup_schema():
    """Create all constraints, indexes, and vector index in Neo4j."""
    logger.info("Setting up Neo4j schema...")

    for stmt in SCHEMA_STATEMENTS:
        try:
            await write_query(stmt)
            logger.info(f"  ✓ {stmt[:60]}...")
        except Exception as e:
            logger.warning(f"  ⚠ Schema statement skipped: {e}")

    for stmt in FULLTEXT_INDEXES:
        try:
            await write_query(stmt)
            logger.info(f"  ✓ Fulltext index created")
        except Exception as e:
            logger.warning(f"  ⚠ Fulltext index skipped: {e}")

    try:
        await write_query(VECTOR_INDEX)
        logger.info("  ✓ Vector index created")
    except Exception as e:
        logger.warning(f"  ⚠ Vector index skipped (may need Neo4j 5.11+): {e}")

    logger.info("Schema setup complete!")
