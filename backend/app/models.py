"""Pydantic models for all graph node and relationship types."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


# ─── Node Models ───────────────────────────────────────────────────────────────

class GeneNode(BaseModel):
    """Gene node with genomic identifiers."""
    symbol: str = Field(..., description="HGNC gene symbol, e.g. BRCA1")
    name: str = Field(..., description="Full gene name")
    ensembl_id: Optional[str] = Field(None, description="Ensembl gene ID")
    chromosome: Optional[str] = Field(None, description="Chromosome location")


class MutationNode(BaseModel):
    """Genetic mutation / variant."""
    id: str = Field(..., description="ClinVar variation ID")
    hgvs: Optional[str] = Field(None, description="HGVS nomenclature")
    type: Optional[str] = Field(None, description="Variant type (SNV, deletion, etc.)")
    clinical_significance: Optional[str] = Field(None, description="Pathogenic, benign, etc.")


class ProteinNode(BaseModel):
    """Protein encoded by a gene."""
    uniprot_id: str = Field(..., description="UniProt accession")
    name: str = Field(..., description="Protein name")
    function: Optional[str] = Field(None, description="Functional description")


class DiseaseNode(BaseModel):
    """Disease or phenotype."""
    id: str = Field(..., description="Disease identifier (OMIM, DOID, etc.)")
    name: str = Field(..., description="Disease name")
    description: Optional[str] = Field(None, description="Description")


class PathwayNode(BaseModel):
    """Biological pathway."""
    reactome_id: str = Field(..., description="Reactome pathway ID")
    name: str = Field(..., description="Pathway name")


class PublicationNode(BaseModel):
    """PubMed publication."""
    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Paper title")
    abstract: Optional[str] = Field(None, description="Paper abstract")
    year: Optional[int] = Field(None, description="Publication year")


# ─── Relationship Models ──────────────────────────────────────────────────────

class InteractsWithRel(BaseModel):
    """Protein-protein interaction."""
    score: float = Field(..., ge=0, le=1, description="Interaction confidence score")


class AssociatedWithRel(BaseModel):
    """Gene-disease association."""
    score: float = Field(..., ge=0, le=1, description="Association score")


# ─── API Response Models ──────────────────────────────────────────────────────

class NodeResponse(BaseModel):
    """Generic node returned from the API."""
    id: str
    type: str  # Gene, Protein, Disease, Mutation, Pathway, Publication
    label: str  # Display label
    properties: dict = Field(default_factory=dict)


class EdgeResponse(BaseModel):
    """Generic edge returned from the API."""
    source: str
    target: str
    type: str  # Relationship type
    properties: dict = Field(default_factory=dict)


class SubgraphResponse(BaseModel):
    """A subgraph of nodes and edges."""
    nodes: list[NodeResponse] = Field(default_factory=list)
    edges: list[EdgeResponse] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Search result item."""
    id: str
    type: str
    label: str
    score: float = 1.0
    properties: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response for search queries."""
    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0


class PathResponse(BaseModel):
    """Path between two nodes."""
    paths: list[SubgraphResponse] = Field(default_factory=list)
    explanation: Optional[str] = None


class MutationImpactResponse(BaseModel):
    """Mutation impact analysis."""
    mutation: NodeResponse
    affected_gene: Optional[NodeResponse] = None
    affected_protein: Optional[NodeResponse] = None
    linked_diseases: list[NodeResponse] = Field(default_factory=list)
    affected_pathways: list[NodeResponse] = Field(default_factory=list)
    subgraph: SubgraphResponse = Field(default_factory=SubgraphResponse)


class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_genes: int = 0
    total_proteins: int = 0
    total_diseases: int = 0
    total_mutations: int = 0
    total_pathways: int = 0
    total_publications: int = 0
    total_relationships: int = 0
    hub_genes: list[dict] = Field(default_factory=list)
    disease_clusters: list[dict] = Field(default_factory=list)


class AIAskRequest(BaseModel):
    """Request for AI question answering."""
    question: str = Field(..., min_length=1, max_length=2000)
    context_node_ids: list[str] = Field(default_factory=list)


class AIAskResponse(BaseModel):
    """Response from AI question answering."""
    answer: str
    cypher_query: Optional[str] = None
    citations: list[dict] = Field(default_factory=list)
    subgraph: SubgraphResponse = Field(default_factory=SubgraphResponse)
    disclaimer: str = "⚠️ For research use only. Not medical advice."


class ExplainPathRequest(BaseModel):
    """Request to explain a graph path."""
    path_nodes: list[str] = Field(..., min_length=2)
    path_edges: list[str] = Field(default_factory=list)


class ExplainPathResponse(BaseModel):
    """AI explanation of a graph path."""
    explanation: str
    disclaimer: str = "⚠️ For research use only. Not medical advice."


class IngestPubmedRequest(BaseModel):
    """Request to ingest a PubMed paper."""
    pmid: str = Field(..., description="PubMed ID to ingest")


class IngestReviewItem(BaseModel):
    """An extracted entity or relationship pending review."""
    id: str
    type: str  # entity or relationship
    label: str
    source: Optional[str] = None
    target: Optional[str] = None
    properties: dict = Field(default_factory=dict)
    approved: bool = False


class IngestReviewResponse(BaseModel):
    """Extracted entities and relationships pending approval."""
    pmid: str
    title: str
    entities: list[IngestReviewItem] = Field(default_factory=list)
    relationships: list[IngestReviewItem] = Field(default_factory=list)


class IngestApproveRequest(BaseModel):
    """Approve extracted entities for ingestion into the graph."""
    pmid: str
    approved_entity_ids: list[str] = Field(default_factory=list)
    approved_relationship_ids: list[str] = Field(default_factory=list)


# ─── Graph CRUD Models ────────────────────────────────────────────────────────

class CreateNodeRequest(BaseModel):
    """Request to create a new graph node."""
    type: Literal["Gene", "Protein", "Disease", "Mutation", "Pathway", "Publication"]
    id: str = Field(..., min_length=1, description="Unique primary identifier")
    label: Optional[str] = Field(None, description="Display label / name")
    properties: dict = Field(default_factory=dict, description="Arbitrary node metadata")


class UpdateNodeRequest(BaseModel):
    """Request to update properties of an existing graph node."""
    label: Optional[str] = None
    properties: dict = Field(default_factory=dict)


class CreateEdgeRequest(BaseModel):
    """Request to create a relationship between two nodes."""
    source_id: str = Field(..., description="Source node identifier")
    target_id: str = Field(..., description="Target node identifier")
    type: str = Field(..., description="Relationship type, e.g. ASSOCIATED_WITH, ENCODES, HAS_MUTATION")
    properties: dict = Field(default_factory=dict, description="Edge properties, e.g. score")


class DeleteEdgeRequest(BaseModel):
    """Request to delete a relationship between two nodes."""
    source_id: str
    target_id: str
    type: Optional[str] = None


# ─── AI / ML Models ───────────────────────────────────────────────────────────

class LinkPredictionRequest(BaseModel):
    """Request for graph ML link prediction between nodes or whole graph."""
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    node_type: Optional[str] = None
    top_k: int = Field(default=8, ge=1, le=50)


class PredictedLink(BaseModel):
    """A link predicted using topological network metrics & semantic similarity."""
    source_id: str
    source_label: str
    source_type: str
    target_id: str
    target_label: str
    target_type: str
    predicted_type: str
    confidence_score: float
    common_neighbors: list[str] = Field(default_factory=list)
    algorithm: str = "Jaccard / Resource Allocation"
    rationale: str


class LinkPredictionResponse(BaseModel):
    """Results from AI/ML link prediction."""
    predictions: list[PredictedLink] = Field(default_factory=list)
    total_evaluated: int = 0


class ClusterModule(BaseModel):
    """A biological network community/cluster discovered by modularity."""
    cluster_id: int
    name: str
    description: str
    lead_genes: list[str] = Field(default_factory=list)
    total_nodes: int = 0
    density_score: float = 0.0


class ClusterAnalysisResponse(BaseModel):
    """Network community detection / cluster analysis."""
    clusters: list[ClusterModule] = Field(default_factory=list)
    modularity_score: float = 0.0


class HypothesisRequest(BaseModel):
    """Request to generate a disease mechanism hypothesis."""
    gene_symbol: str
    disease_id_or_name: str


class HypothesisResponse(BaseModel):
    """AI-synthesized biomedical hypothesis."""
    gene: str
    disease: str
    confidence_score: float
    hypothesis: str
    pathway_involvement: list[str] = Field(default_factory=list)
    suggested_experiments: list[str] = Field(default_factory=list)
    disclaimer: str = "⚠️ For research use only. Not medical advice."


class CentralityNode(BaseModel):
    """Centrality and topological importance metrics for a graph node."""
    id: str
    label: str
    type: str
    degree: int
    degree_centrality: float
    pagerank_score: float
    betweenness_approx: float
    role: str  # e.g. "Global Hub", "Bottleneck Bridge", "Peripheral Module"


class CentralityResponse(BaseModel):
    """Network centrality and bottleneck vulnerability ranking."""
    nodes: list[CentralityNode] = Field(default_factory=list)
    network_diameter_approx: int = 4
    average_degree: float = 0.0


# ─── Mutation Simulation Models ───────────────────────────────────────────────

class MutationSimulationRequest(BaseModel):
    """Request to simulate a mutation's impact on protein structure and pathways."""
    gene_symbol: str = Field(..., description="Gene symbol, e.g. TP53, BRCA1")
    mutation_hgvs: str = Field(default="", description="HGVS notation, e.g. p.Arg248Trp")
    mutation_type: str = Field(default="missense", description="Mutation type: missense, nonsense, frameshift, etc.")


class ProteinDomain(BaseModel):
    """A protein structural/functional domain."""
    name: str
    start_residue: int
    end_residue: int
    function: str
    impact_score: float = Field(ge=0, le=1, description="How much the mutation disrupts this domain")
    is_mutation_site: bool = False


class PathwayCascadeEffect(BaseModel):
    """A downstream pathway effect caused by the mutation."""
    pathway_name: str
    pathway_id: str = ""
    effect_type: str  # "loss_of_function", "gain_of_function", "reduced_activity", "hyperactivation"
    severity: float = Field(ge=0, le=1)
    description: str
    downstream_targets: list[str] = Field(default_factory=list)


class DiseaseRiskChange(BaseModel):
    """Change in disease risk due to this mutation."""
    disease_name: str
    disease_id: str = ""
    baseline_risk: float
    mutated_risk: float
    fold_change: float
    mechanism: str


class MutationSimulationResponse(BaseModel):
    """Full mutation impact simulation result."""
    gene: str
    protein_name: str
    mutation: str
    mutation_type: str
    protein_length: int = 393
    mutation_position: int = 248
    structural_impact_summary: str
    stability_score_wt: float = Field(ge=0, le=1, description="Wild-type protein stability")
    stability_score_mut: float = Field(ge=0, le=1, description="Mutant protein stability")
    folding_energy_change: float  # ΔΔG in kcal/mol
    domains: list[ProteinDomain] = Field(default_factory=list)
    pathway_effects: list[PathwayCascadeEffect] = Field(default_factory=list)
    disease_risk_changes: list[DiseaseRiskChange] = Field(default_factory=list)
    interaction_partners_lost: list[str] = Field(default_factory=list)
    interaction_partners_gained: list[str] = Field(default_factory=list)
    clinical_significance: str = "Pathogenic"
    therapeutic_implications: list[str] = Field(default_factory=list)
    disclaimer: str = "⚠️ For research use only. This is a computational simulation, not clinical evidence."

