import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { fetchStats } from '../api';
import type { DashboardStats } from '../types';
import { 
  Dna, 
  Activity, 
  AlertCircle, 
  GitFork, 
  Share2, 
  BookOpen, 
  ArrowRight
} from 'lucide-react';

interface StatsDashboardProps {
  onExploreNode: (type: string, id: string) => void;
}

export const StatsDashboard: FC<StatsDashboardProps> = ({ onExploreNode }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats().then(data => {
      setStats(data);
      setLoading(false);
    });
  }, []);

  if (loading || !stats) {
    return (
      <div className="loading-overlay">
        <div className="spinner spinner-lg" />
        <span>Loading Knowledge Graph metrics...</span>
      </div>
    );
  }

  const statCards = [
    { label: 'Genes Cataloged', value: stats.total_genes, icon: <Dna size={20} color="#818cf8" />, bg: 'var(--color-gene-bg)' },
    { label: 'Proteins Mapped', value: stats.total_proteins, icon: <Activity size={20} color="#34d399" />, bg: 'var(--color-protein-bg)' },
    { label: 'Diseases Linked', value: stats.total_diseases, icon: <AlertCircle size={20} color="#f472b6" />, bg: 'var(--color-disease-bg)' },
    { label: 'Pathogenic Mutations', value: stats.total_mutations, icon: <GitFork size={20} color="#fb923c" />, bg: 'var(--color-mutation-bg)' },
    { label: 'Biological Pathways', value: stats.total_pathways, icon: <Share2 size={20} color="#38bdf8" />, bg: 'var(--color-pathway-bg)' },
    { label: 'Total Relationships', value: stats.total_relationships, icon: <BookOpen size={20} color="#a78bfa" />, bg: 'var(--color-publication-bg)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Knowledge Graph Analytics</h1>
        <p className="page-description">
          Graph metrics, top interconnected hub genes, and disease association clusters in the active Neo4j database.
        </p>
      </div>

      {/* Primary KPI Grid */}
      <div className="stats-grid">
        {statCards.map((card, idx) => (
          <div key={idx} className="stat-card">
            <div className="stat-icon" style={{ background: card.bg }}>
              {card.icon}
            </div>
            <div className="stat-value">{card.value}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Hub Genes & Disease Clusters */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 'var(--space-lg)' }}>
        {/* Hub Genes */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Top Connected Hub Genes</div>
              <div className="card-subtitle">Highest degree centrality in oncogenic networks</div>
            </div>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Gene Name</th>
                  <th>Connections</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {stats.hub_genes.map((gene, i) => (
                  <tr key={i}>
                    <td>
                      <span className="badge badge-gene">{gene.symbol}</span>
                    </td>
                    <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{gene.name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-accent)' }}>
                      {gene.connections}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onExploreNode('Gene', gene.symbol)}
                      >
                        Explore <ArrowRight size={11} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Disease Clusters */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Disease Clusters</div>
              <div className="card-subtitle">Pathologies with most documented gene linkages</div>
            </div>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Disease</th>
                  <th>DOID</th>
                  <th>Associated Genes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {stats.disease_clusters.map((cluster, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{cluster.disease}</td>
                    <td>
                      <span className="badge badge-disease">{cluster.id}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-disease)' }}>
                      {cluster.gene_count}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onExploreNode('Disease', cluster.id)}
                      >
                        Explore <ArrowRight size={11} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
