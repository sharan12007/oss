"""Graph CRUD and search API routes."""

from fastapi import APIRouter, Query, HTTPException
from app.database import read_query, write_query
from app.models import (
    NodeResponse, SubgraphResponse, EdgeResponse,
    SearchResponse, SearchResult, PathResponse,
    MutationImpactResponse, StatsResponse,
    CreateNodeRequest, UpdateNodeRequest,
    CreateEdgeRequest, DeleteEdgeRequest,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Node type config ─────────────────────────────────────────────────────────

NODE_TYPES = {
    "Gene": {"id_field": "symbol", "label_field": "symbol"},
    "Protein": {"id_field": "uniprot_id", "label_field": "name"},
    "Disease": {"id_field": "id", "label_field": "name"},
    "Mutation": {"id_field": "id", "label_field": "hgvs"},
    "Pathway": {"id_field": "reactome_id", "label_field": "name"},
    "Publication": {"id_field": "pmid", "label_field": "title"},
}


def _node_to_response(record: dict, node_key: str = "n") -> NodeResponse:
    """Convert a Neo4j record to a NodeResponse."""
    node = record[node_key]
    # Detect type from labels
    node_type = "Unknown"
    for label in NODE_TYPES:
        if label.lower() in str(type(node)).lower() or label in record.get("labels", []):
            node_type = label
            break

    props = dict(node) if hasattr(node, '__iter__') else node
    # Try to determine type from record metadata
    if "type" in record:
        node_type = record["type"]

    label = props.get("symbol") or props.get("name") or props.get("hgvs") or props.get("pmid") or props.get("id", "")
    node_id = props.get("symbol") or props.get("uniprot_id") or props.get("id") or props.get("reactome_id") or props.get("pmid") or ""

    return NodeResponse(
        id=str(node_id),
        type=node_type,
        label=str(label),
        properties=props,
    )


# ─── Search ───────────────────────────────────────────────────────────────────

@router.get("/search", response_model=SearchResponse)
async def search_nodes(
    q: str = Query(..., min_length=1, description="Search query"),
    node_type: str | None = Query(None, description="Filter by node type"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search across all node types using full-text and CONTAINS matching."""
    results: list[SearchResult] = []

    search_configs = [
        ("Gene", "symbol", "name"),
        ("Protein", "uniprot_id", "name"),
        ("Disease", "id", "name"),
        ("Mutation", "id", "hgvs"),
        ("Pathway", "reactome_id", "name"),
        ("Publication", "pmid", "title"),
    ]

    for label, id_field, label_field in search_configs:
        if node_type and node_type != label:
            continue

        # Use CONTAINS for flexible matching
        cypher = f"""
            MATCH (n:{label})
            WHERE toLower(n.{label_field}) CONTAINS toLower($q)
               OR toLower(n.{id_field}) CONTAINS toLower($q)
            RETURN n, labels(n) as labels, '{label}' as type
            LIMIT $limit
        """
        try:
            records = await read_query(cypher, {"q": q, "limit": limit})
            for rec in records:
                props = dict(rec["n"])
                results.append(SearchResult(
                    id=str(props.get(id_field, "")),
                    type=label,
                    label=str(props.get(label_field, props.get(id_field, ""))),
                    score=1.0,
                    properties=props,
                ))
        except Exception as e:
            logger.warning(f"Search error for {label}: {e}")

    # Sort by relevance (exact matches first)
    q_lower = q.lower()
    results.sort(key=lambda r: (
        0 if r.label.lower() == q_lower else 1 if q_lower in r.label.lower() else 2
    ))

    return SearchResponse(results=results[:limit], total=len(results))


# ─── Node Detail ──────────────────────────────────────────────────────────────

@router.get("/node/{node_type}/{node_id}", response_model=NodeResponse)
async def get_node(node_type: str, node_id: str):
    """Get a specific node by type and ID."""
    if node_type not in NODE_TYPES:
        raise HTTPException(404, f"Unknown node type: {node_type}")

    id_field = NODE_TYPES[node_type]["id_field"]
    cypher = f"MATCH (n:{node_type} {{{id_field}: $id}}) RETURN n, '{node_type}' as type"
    records = await read_query(cypher, {"id": node_id})

    if not records:
        raise HTTPException(404, f"{node_type} {node_id} not found")

    props = dict(records[0]["n"])
    label_field = NODE_TYPES[node_type]["label_field"]

    return NodeResponse(
        id=node_id,
        type=node_type,
        label=str(props.get(label_field, node_id)),
        properties=props,
    )


# ─── Node Neighbors ──────────────────────────────────────────────────────────

@router.get("/node/{node_type}/{node_id}/neighbors", response_model=SubgraphResponse)
async def get_neighbors(
    node_type: str,
    node_id: str,
    depth: int = Query(1, ge=1, le=3),
):
    """Get neighbors of a node up to specified depth."""
    if node_type not in NODE_TYPES:
        raise HTTPException(404, f"Unknown node type: {node_type}")

    id_field = NODE_TYPES[node_type]["id_field"]

    cypher = f"""
        MATCH (source:{node_type} {{{id_field}: $id}})
        CALL apoc.path.subgraphAll(source, {{maxLevel: $depth, limit: 100}})
        YIELD nodes, relationships
        RETURN nodes, relationships
    """

    # Fallback without APOC
    fallback_cypher = f"""
        MATCH (source:{node_type} {{{id_field}: $id}})-[r]-(neighbor)
        RETURN source, r, neighbor, labels(source) as source_labels,
               labels(neighbor) as neighbor_labels, type(r) as rel_type,
               properties(r) as rel_props
        LIMIT 100
    """

    try:
        records = await read_query(fallback_cypher, {"id": node_id, "depth": depth})
    except Exception as e:
        logger.error(f"Neighbor query error: {e}")
        raise HTTPException(500, "Failed to fetch neighbors")

    nodes_map: dict[str, NodeResponse] = {}
    edges: list[EdgeResponse] = []

    for rec in records:
        # Source node
        source_props = dict(rec["source"])
        source_node_id = str(source_props.get(id_field, ""))
        if source_node_id not in nodes_map:
            nodes_map[source_node_id] = NodeResponse(
                id=source_node_id,
                type=node_type,
                label=str(source_props.get(NODE_TYPES[node_type]["label_field"], source_node_id)),
                properties=source_props,
            )

        # Neighbor node
        neighbor_props = dict(rec["neighbor"])
        neighbor_labels = rec.get("neighbor_labels", [])
        neighbor_type = next((l for l in neighbor_labels if l in NODE_TYPES), "Unknown")
        neighbor_id_field = NODE_TYPES.get(neighbor_type, {}).get("id_field", "id")
        neighbor_label_field = NODE_TYPES.get(neighbor_type, {}).get("label_field", "name")
        neighbor_id = str(
            neighbor_props.get("symbol") or neighbor_props.get("uniprot_id") or
            neighbor_props.get("id") or neighbor_props.get("reactome_id") or
            neighbor_props.get("pmid") or ""
        )

        if neighbor_id not in nodes_map:
            nodes_map[neighbor_id] = NodeResponse(
                id=neighbor_id,
                type=neighbor_type,
                label=str(neighbor_props.get(neighbor_label_field, neighbor_id)),
                properties=neighbor_props,
            )

        # Edge
        edges.append(EdgeResponse(
            source=source_node_id,
            target=neighbor_id,
            type=rec.get("rel_type", "RELATED"),
            properties=rec.get("rel_props", {}),
        ))

    return SubgraphResponse(nodes=list(nodes_map.values()), edges=edges)


# ─── Path Finding ────────────────────────────────────────────────────────────

@router.get("/path", response_model=PathResponse)
async def find_paths(
    from_id: str = Query(..., alias="from", description="Source node ID"),
    to_id: str = Query(..., alias="to", description="Target node ID"),
    k: int = Query(3, ge=1, le=5, description="Number of paths to find"),
):
    """Find shortest and alternative paths between two nodes."""
    # Find node by any ID field
    find_node_cypher = """
        MATCH (n)
        WHERE n.symbol = $id OR n.uniprot_id = $id OR n.id = $id
           OR n.reactome_id = $id OR n.pmid = $id
        RETURN n, labels(n) as labels
        LIMIT 1
    """

    from_result = await read_query(find_node_cypher, {"id": from_id})
    to_result = await read_query(find_node_cypher, {"id": to_id})

    if not from_result:
        raise HTTPException(404, f"Source node '{from_id}' not found")
    if not to_result:
        raise HTTPException(404, f"Target node '{to_id}' not found")

    # Shortest paths
    cypher = """
        MATCH (a), (b)
        WHERE (a.symbol = $from OR a.uniprot_id = $from OR a.id = $from
               OR a.reactome_id = $from OR a.pmid = $from)
          AND (b.symbol = $to OR b.uniprot_id = $to OR b.id = $to
               OR b.reactome_id = $to OR b.pmid = $to)
        MATCH path = allShortestPaths((a)-[*..6]-(b))
        RETURN path, [n IN nodes(path) | labels(n)] as all_labels,
               [r IN relationships(path) | type(r)] as rel_types,
               [r IN relationships(path) | properties(r)] as rel_props
        LIMIT $k
    """

    records = await read_query(cypher, {"from": from_id, "to": to_id, "k": k})

    if not records:
        return PathResponse(paths=[], explanation="No path found between these nodes.")

    paths: list[SubgraphResponse] = []
    for rec in records:
        path = rec["path"]
        all_labels = rec["all_labels"]
        rel_types = rec["rel_types"]
        rel_props = rec["rel_props"]

        nodes_list: list[NodeResponse] = []
        edges_list: list[EdgeResponse] = []

        path_nodes = path if isinstance(path, list) else (path.nodes if hasattr(path, 'nodes') else [])
        # Handle different path return formats
        if isinstance(path, dict):
            # Neo4j returns path as nodes and relationships
            for i, node_data in enumerate(path.get("nodes", path.get("_nodes", []))):
                props = dict(node_data) if hasattr(node_data, '__iter__') else {}
                labels = all_labels[i] if i < len(all_labels) else []
                n_type = next((l for l in labels if l in NODE_TYPES), "Unknown")
                n_id = str(props.get("symbol") or props.get("uniprot_id") or
                          props.get("id") or props.get("reactome_id") or
                          props.get("pmid") or f"node_{i}")
                label_field = NODE_TYPES.get(n_type, {}).get("label_field", "name")
                nodes_list.append(NodeResponse(
                    id=n_id, type=n_type,
                    label=str(props.get(label_field, n_id)),
                    properties=props,
                ))

            for i in range(len(nodes_list) - 1):
                edges_list.append(EdgeResponse(
                    source=nodes_list[i].id,
                    target=nodes_list[i + 1].id,
                    type=rel_types[i] if i < len(rel_types) else "RELATED",
                    properties=rel_props[i] if i < len(rel_props) else {},
                ))

        paths.append(SubgraphResponse(nodes=nodes_list, edges=edges_list))

    return PathResponse(paths=paths)


# ─── Mutation Impact ──────────────────────────────────────────────────────────

@router.get("/mutation/{mutation_id}/impact", response_model=MutationImpactResponse)
async def mutation_impact(mutation_id: str):
    """Analyze the impact of a mutation across genes, proteins, pathways, and diseases."""
    # Get mutation
    mut_result = await read_query(
        "MATCH (m:Mutation {id: $id}) RETURN m", {"id": mutation_id}
    )
    if not mut_result:
        raise HTTPException(404, f"Mutation {mutation_id} not found")

    mut_props = dict(mut_result[0]["m"])
    mutation = NodeResponse(
        id=mutation_id, type="Mutation",
        label=mut_props.get("hgvs", mutation_id),
        properties=mut_props,
    )

    # Gene that has this mutation
    gene_result = await read_query(
        """MATCH (g:Gene)-[:HAS_MUTATION]->(m:Mutation {id: $id})
           RETURN g""",
        {"id": mutation_id},
    )
    affected_gene = None
    if gene_result:
        g_props = dict(gene_result[0]["g"])
        affected_gene = NodeResponse(
            id=g_props["symbol"], type="Gene",
            label=g_props["symbol"], properties=g_props,
        )

    # Protein encoded by that gene
    protein_result = None
    if affected_gene:
        prot = await read_query(
            """MATCH (g:Gene {symbol: $sym})-[:ENCODES]->(p:Protein)
               RETURN p""",
            {"sym": affected_gene.id},
        )
        if prot:
            p_props = dict(prot[0]["p"])
            protein_result = NodeResponse(
                id=p_props["uniprot_id"], type="Protein",
                label=p_props["name"], properties=p_props,
            )

    # Linked diseases
    disease_results = await read_query(
        """MATCH (m:Mutation {id: $id})-[:LINKED_TO]->(d:Disease)
           RETURN d""",
        {"id": mutation_id},
    )
    linked_diseases = [
        NodeResponse(
            id=dict(r["d"])["id"], type="Disease",
            label=dict(r["d"])["name"],
            properties=dict(r["d"]),
        )
        for r in disease_results
    ]

    # Affected pathways (via protein)
    pathway_results = []
    if protein_result:
        pw = await read_query(
            """MATCH (p:Protein {uniprot_id: $uid})-[:PART_OF]->(pw:Pathway)
               RETURN pw""",
            {"uid": protein_result.id},
        )
        pathway_results = [
            NodeResponse(
                id=dict(r["pw"])["reactome_id"], type="Pathway",
                label=dict(r["pw"])["name"],
                properties=dict(r["pw"]),
            )
            for r in pw
        ]

    # Build subgraph
    all_nodes = [mutation]
    all_edges = []

    if affected_gene:
        all_nodes.append(affected_gene)
        all_edges.append(EdgeResponse(source=affected_gene.id, target=mutation.id, type="HAS_MUTATION"))
    if protein_result:
        all_nodes.append(protein_result)
        if affected_gene:
            all_edges.append(EdgeResponse(source=affected_gene.id, target=protein_result.id, type="ENCODES"))
    for d in linked_diseases:
        all_nodes.append(d)
        all_edges.append(EdgeResponse(source=mutation.id, target=d.id, type="LINKED_TO"))
    for pw in pathway_results:
        all_nodes.append(pw)
        if protein_result:
            all_edges.append(EdgeResponse(source=protein_result.id, target=pw.id, type="PART_OF"))

    return MutationImpactResponse(
        mutation=mutation,
        affected_gene=affected_gene,
        affected_protein=protein_result,
        linked_diseases=linked_diseases,
        affected_pathways=pathway_results,
        subgraph=SubgraphResponse(nodes=all_nodes, edges=all_edges),
    )


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics: counts, hub genes, disease clusters."""
    counts = {}
    for label in NODE_TYPES:
        result = await read_query(f"MATCH (n:{label}) RETURN count(n) as cnt")
        counts[label] = result[0]["cnt"] if result else 0

    # Total relationships
    rel_result = await read_query("MATCH ()-[r]->() RETURN count(r) as cnt")
    total_rels = rel_result[0]["cnt"] if rel_result else 0

    # Hub genes (most connections)
    hub_result = await read_query("""
        MATCH (g:Gene)-[r]-()
        RETURN g.symbol as symbol, g.name as name, count(r) as connections
        ORDER BY connections DESC
        LIMIT 10
    """)
    hub_genes = [dict(r) for r in hub_result]

    # Disease clusters (diseases with most gene associations)
    disease_cluster_result = await read_query("""
        MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
        RETURN d.name as disease, d.id as id, count(g) as gene_count
        ORDER BY gene_count DESC
        LIMIT 10
    """)
    disease_clusters = [dict(r) for r in disease_cluster_result]

    return StatsResponse(
        total_genes=counts.get("Gene", 0),
        total_proteins=counts.get("Protein", 0),
        total_diseases=counts.get("Disease", 0),
        total_mutations=counts.get("Mutation", 0),
        total_pathways=counts.get("Pathway", 0),
        total_publications=counts.get("Publication", 0),
        total_relationships=total_rels,
        hub_genes=hub_genes,
        disease_clusters=disease_clusters,
    )


# ─── Graph Database CRUD Operations ──────────────────────────────────────────

@router.post("/node", response_model=NodeResponse)
async def create_node(req: CreateNodeRequest):
    """Create a new node in the Neo4j graph database."""
    if req.type not in NODE_TYPES:
        raise HTTPException(400, f"Unsupported node type: {req.type}")

    id_field = NODE_TYPES[req.type]["id_field"]
    label_field = NODE_TYPES[req.type]["label_field"]

    props = dict(req.properties)
    props[id_field] = req.id
    if req.label and label_field not in props:
        props[label_field] = req.label

    # Check if node already exists
    check_cypher = f"MATCH (n:{req.type} {{{id_field}: $id}}) RETURN n"
    existing = await read_query(check_cypher, {"id": req.id})
    if existing:
        raise HTTPException(409, f"{req.type} with id '{req.id}' already exists")

    cypher = f"""
        CREATE (n:{req.type} $props)
        RETURN n, '{req.type}' as type
    """
    try:
        results = await write_query(cypher, {"props": props})
        if not results:
            raise HTTPException(500, "Failed to create node in database")
        saved_props = dict(results[0]["n"])
        return NodeResponse(
            id=req.id,
            type=req.type,
            label=str(saved_props.get(label_field, req.id)),
            properties=saved_props,
        )
    except Exception as e:
        logger.error(f"Node creation error: {e}")
        raise HTTPException(500, f"Database error creating node: {str(e)}")


@router.put("/node/{node_type}/{node_id}", response_model=NodeResponse)
async def update_node(node_type: str, node_id: str, req: UpdateNodeRequest):
    """Update properties of an existing graph node."""
    if node_type not in NODE_TYPES:
        raise HTTPException(400, f"Unsupported node type: {node_type}")

    id_field = NODE_TYPES[node_type]["id_field"]
    label_field = NODE_TYPES[node_type]["label_field"]

    # Verify existence
    check_cypher = f"MATCH (n:{node_type} {{{id_field}: $id}}) RETURN n"
    existing = await read_query(check_cypher, {"id": node_id})
    if not existing:
        raise HTTPException(404, f"{node_type} with id '{node_id}' not found")

    update_props = dict(req.properties)
    if req.label:
        update_props[label_field] = req.label
    update_props[id_field] = node_id  # protect primary identifier

    cypher = f"""
        MATCH (n:{node_type} {{{id_field}: $id}})
        SET n += $props
        RETURN n, '{node_type}' as type
    """
    try:
        results = await write_query(cypher, {"id": node_id, "props": update_props})
        saved_props = dict(results[0]["n"])
        return NodeResponse(
            id=node_id,
            type=node_type,
            label=str(saved_props.get(label_field, node_id)),
            properties=saved_props,
        )
    except Exception as e:
        logger.error(f"Node update error: {e}")
        raise HTTPException(500, f"Database error updating node: {str(e)}")


@router.delete("/node/{node_type}/{node_id}")
async def delete_node(node_type: str, node_id: str):
    """Delete a node and all its connected relationships from the graph."""
    if node_type not in NODE_TYPES:
        raise HTTPException(400, f"Unsupported node type: {node_type}")

    id_field = NODE_TYPES[node_type]["id_field"]

    # Check existence and relationship count
    check_cypher = f"""
        MATCH (n:{node_type} {{{id_field}: $id}})
        OPTIONAL MATCH (n)-[r]-()
        RETURN n, count(r) as rel_count
    """
    existing = await read_query(check_cypher, {"id": node_id})
    if not existing or not existing[0].get("n"):
        raise HTTPException(404, f"{node_type} with id '{node_id}' not found")

    rel_count = existing[0].get("rel_count", 0)

    cypher = f"""
        MATCH (n:{node_type} {{{id_field}: $id}})
        DETACH DELETE n
    """
    try:
        await write_query(cypher, {"id": node_id})
        return {
            "success": True,
            "message": f"Successfully deleted {node_type} '{node_id}' and {rel_count} relationships",
            "deleted_id": node_id,
            "deleted_type": node_type,
            "relationships_removed": rel_count,
        }
    except Exception as e:
        logger.error(f"Node delete error: {e}")
        raise HTTPException(500, f"Database error deleting node: {str(e)}")


@router.post("/edge", response_model=EdgeResponse)
async def create_edge(req: CreateEdgeRequest):
    """Create a typed relationship between two nodes in the graph."""
    # Sanitize relationship type (letters and underscores only)
    rel_type = "".join(c for c in req.type.upper() if c.isalnum() or c == "_")
    if not rel_type:
        raise HTTPException(400, "Invalid relationship type format")

    cypher = f"""
        MATCH (s) WHERE s.symbol = $source_id OR s.uniprot_id = $source_id OR s.id = $source_id OR s.reactome_id = $source_id OR s.pmid = $source_id
        MATCH (t) WHERE t.symbol = $target_id OR t.uniprot_id = $target_id OR t.id = $target_id OR t.reactome_id = $target_id OR t.pmid = $target_id
        MERGE (s)-[r:{rel_type}]->(t)
        SET r += $props
        RETURN properties(r) as props, type(r) as r_type
    """
    try:
        results = await write_query(cypher, {
            "source_id": req.source_id,
            "target_id": req.target_id,
            "props": req.properties,
        })
        if not results:
            raise HTTPException(404, f"Could not find both source '{req.source_id}' and target '{req.target_id}' nodes")

        return EdgeResponse(
            source=req.source_id,
            target=req.target_id,
            type=rel_type,
            properties=results[0].get("props", {}),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Edge creation error: {e}")
        raise HTTPException(500, f"Database error creating edge: {str(e)}")


@router.delete("/edge")
async def delete_edge(source_id: str = Query(...), target_id: str = Query(...), rel_type: str | None = Query(None)):
    """Delete a relationship between two nodes."""
    type_clause = f":{rel_type}" if rel_type else ""
    cypher = f"""
        MATCH (s)-[r{type_clause}]-(t)
        WHERE (s.symbol = $source_id OR s.uniprot_id = $source_id OR s.id = $source_id OR s.reactome_id = $source_id OR s.pmid = $source_id)
          AND (t.symbol = $target_id OR t.uniprot_id = $target_id OR t.id = $target_id OR t.reactome_id = $target_id OR t.pmid = $target_id)
        DELETE r
        RETURN count(r) as deleted_count
    """
    try:
        results = await write_query(cypher, {"source_id": source_id, "target_id": target_id})
        count = results[0]["deleted_count"] if results else 0
        if count == 0:
            raise HTTPException(404, "No matching relationship found between given nodes")
        return {
            "success": True,
            "message": f"Deleted {count} relationship(s) between '{source_id}' and '{target_id}'",
            "deleted_count": count,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Edge delete error: {e}")
        raise HTTPException(500, f"Database error deleting edge: {str(e)}")

