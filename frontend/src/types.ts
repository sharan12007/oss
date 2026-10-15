export type NodeType = 'Gene' | 'Protein' | 'Disease' | 'Mutation' | 'Pathway' | 'Publication';

export interface GraphNode {
  id: string;
  type: NodeType | string;
  label: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface Subgraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult {
  id: string;
  type: string;
  label: string;
  score: number;
  properties: Record<string, any>;
}

export interface HubGene {
  symbol: string;
  name: string;
  connections: number;
}

export interface DiseaseCluster {
  disease: string;
  id: string;
  gene_count: number;
}

export interface DashboardStats {
  total_genes: number;
  total_proteins: number;
  total_diseases: number;
  total_mutations: number;
  total_pathways: number;
  total_publications: number;
  total_relationships: number;
  hub_genes: HubGene[];
  disease_clusters: DiseaseCluster[];
}

export interface IngestEntity {
  name: string;
  type: string;
  id?: string;
  relation_to_gene?: string;
}

export interface IngestReview {
  review_id: string;
  pmid: string;
  title: string;
  abstract: string;
  year?: number;
  entities: IngestEntity[];
  relationships: Array<{
    source: string;
    source_type: string;
    target: string;
    target_type: string;
    type: string;
  }>;
}

// ─── CRUD Types ───────────────────────────────────────────────────────────────

export interface CreateNodePayload {
  type: NodeType;
  id: string;
  label?: string;
  properties?: Record<string, any>;
}

export interface UpdateNodePayload {
  label?: string;
  properties: Record<string, any>;
}

export interface CreateEdgePayload {
  source_id: string;
  target_id: string;
  type: string;
  properties?: Record<string, any>;
}

// ─── AI / ML Types ────────────────────────────────────────────────────────────

export interface PredictedLink {
  source_id: string;
  source_label: string;
  source_type: string;
  target_id: string;
  target_label: string;
  target_type: string;
  predicted_type: string;
  confidence_score: number;
  common_neighbors: string[];
  algorithm: string;
  rationale: string;
}

export interface ClusterModule {
  cluster_id: number;
  name: string;
  description: string;
  lead_genes: string[];
  total_nodes: number;
  density_score: number;
}

export interface HypothesisResponse {
  gene: string;
  disease: string;
  confidence_score: number;
  hypothesis: string;
  pathway_involvement: string[];
  suggested_experiments: string[];
  disclaimer: string;
}

