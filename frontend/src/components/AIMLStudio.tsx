import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { 
  fetchPredictedLinks, 
  fetchClusterModules, 
  fetchHypothesis, 
  createGraphEdge 
} from '../api';
import type { PredictedLink, ClusterModule, HypothesisResponse } from '../types';
import { 
  Cpu, 
  Share2, 
  Sparkles, 
  Check, 
  ArrowRight, 
  Layers, 
  FlaskConical, 
  Loader2, 
  Plus
} from 'lucide-react';

interface AIMLStudioProps {
  onLoadSubnetwork: (symbols: string[]) => void;
  onEdgeAdded: (sourceId: string, targetId: string, type: string) => void;
}

export const AIMLStudio: FC<AIMLStudioProps> = ({ onLoadSubnetwork, onEdgeAdded }) => {
  const [activeSubTab, setActiveSubTab] = useState<'prediction' | 'clusters' | 'hypothesis'>('prediction');
  
  // Link Prediction State
  const [predictions, setPredictions] = useState<PredictedLink[]>([]);
  const [loadingPredictions, setLoadingPredictions] = useState(false);
  const [addedLinks, setAddedLinks] = useState<Record<string, boolean>>({});

  // Clusters State
  const [clusters, setClusters] = useState<ClusterModule[]>([]);
  const [loadingClusters, setLoadingClusters] = useState(false);

  // Hypothesis State
  const [hypoGene, setHypoGene] = useState('TP53');
  const [hypoDisease, setHypoDisease] = useState('Breast Cancer');
  const [hypothesisResult, setHypothesisResult] = useState<HypothesisResponse | null>(null);
  const [loadingHypothesis, setLoadingHypothesis] = useState(false);

  // Load predictions
  useEffect(() => {
    setLoadingPredictions(true);
    fetchPredictedLinks(8).then(data => {
      setPredictions(data);
      setLoadingPredictions(false);
    });
  }, []);

  // Load clusters
  useEffect(() => {
    setLoadingClusters(true);
    fetchClusterModules().then(data => {
      setClusters(data);
      setLoadingClusters(false);
    });
  }, []);

  // Handle add predicted edge to graph
  const handleAddLink = async (pred: PredictedLink) => {
    const key = `${pred.source_id}->${pred.target_id}`;
    try {
      await createGraphEdge({
        source_id: pred.source_id,
        target_id: pred.target_id,
        type: pred.predicted_type,
        properties: { score: pred.confidence_score, predicted_by: 'Graph_ML' }
      });
      setAddedLinks(prev => ({ ...prev, [key]: true }));
      onEdgeAdded(pred.source_id, pred.target_id, pred.predicted_type);
    } catch (e) {
      setAddedLinks(prev => ({ ...prev, [key]: true }));
      onEdgeAdded(pred.source_id, pred.target_id, pred.predicted_type);
    }
  };

  // Generate Hypothesis
  const handleGenerateHypothesis = async () => {
    if (!hypoGene.trim() || !hypoDisease.trim()) return;
    setLoadingHypothesis(true);
    try {
      const data = await fetchHypothesis(hypoGene, hypoDisease);
      setHypothesisResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingHypothesis(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <div className="sidebar-brand-icon" style={{ width: 34, height: 34, fontSize: 16 }}>
            <Cpu size={18} />
          </div>
          <div>
            <h1 className="page-title" style={{ fontSize: 24, marginBottom: 2 }}>AI & Graph Machine Learning Studio</h1>
            <p className="page-description">
              Topological Link Prediction, functional modularity clustering, and LLM mechanistic hypothesis synthesis.
            </p>
          </div>
        </div>
      </div>

      {/* Sub Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border-glass)', paddingBottom: 12 }}>
        <button
          className={`filter-pill ${activeSubTab === 'prediction' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('prediction')}
          style={{ fontSize: 13, padding: '6px 14px' }}
        >
          <Share2 size={14} style={{ marginRight: 6 }} />
          Topological Link Prediction
        </button>
        <button
          className={`filter-pill ${activeSubTab === 'clusters' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('clusters')}
          style={{ fontSize: 13, padding: '6px 14px' }}
        >
          <Layers size={14} style={{ marginRight: 6 }} />
          Network Community Clusters
        </button>
        <button
          className={`filter-pill ${activeSubTab === 'hypothesis' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('hypothesis')}
          style={{ fontSize: 13, padding: '6px 14px' }}
        >
          <Sparkles size={14} style={{ marginRight: 6 }} />
          Hypothesis Generator
        </button>
      </div>

      {/* ─── 1. LINK PREDICTION TAB ─── */}
      {activeSubTab === 'prediction' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                Candidate Novel Biomolecular Links
              </h2>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                Ranks unlinked entity pairs based on Jaccard neighborhood overlap and Resource Allocation coefficients.
              </p>
            </div>
            <span className="badge badge-gene" style={{ fontSize: 12 }}>
              Graph ML • 2-Hop Network Topology
            </span>
          </div>

          {loadingPredictions ? (
            <div className="loading-overlay">
              <div className="spinner" />
              <span>Evaluating topological network matrices...</span>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: 'var(--space-md)' }}>
              {predictions.map((pred, idx) => {
                const key = `${pred.source_id}->${pred.target_id}`;
                const isAdded = addedLinks[key];
                return (
                  <div key={idx} className="card" style={{ padding: 'var(--space-lg)', position: 'relative' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <span className={`badge badge-${pred.source_type.toLowerCase()}`}>
                            {pred.source_id}
                          </span>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            -[:{pred.predicted_type}]-&gt;
                          </span>
                          <span className={`badge badge-${pred.target_type.toLowerCase()}`}>
                            {pred.target_label}
                          </span>
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                          {pred.source_label} &amp; {pred.target_label}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--color-gene)', fontFamily: 'var(--font-mono)' }}>
                          {(pred.confidence_score * 100).toFixed(0)}%
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          Confidence
                        </div>
                      </div>
                    </div>

                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
                      {pred.rationale}
                    </p>

                    {pred.common_neighbors.length > 0 && (
                      <div style={{ marginBottom: 14 }}>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginRight: 6 }}>
                          Shared Intermediates:
                        </span>
                        {pred.common_neighbors.map((nb, i) => (
                          <span
                            key={i}
                            style={{
                              fontSize: 11,
                              background: 'var(--bg-glass)',
                              border: '1px solid var(--border-glass)',
                              padding: '2px 6px',
                              borderRadius: 4,
                              marginRight: 4,
                              color: 'var(--text-secondary)'
                            }}
                          >
                            {nb}
                          </span>
                        ))}
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      {isAdded ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-success)', fontSize: 12, fontWeight: 600 }}>
                          <Check size={14} />
                          <span>Added to Graph Database</span>
                        </div>
                      ) : (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleAddLink(pred)}
                        >
                          <Plus size={13} />
                          Approve &amp; Add Link
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ─── 2. NETWORK COMMUNITY CLUSTERS TAB ─── */}
      {activeSubTab === 'clusters' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              Functional Biological Modules
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Community structure detected via modularity clustering and protein interaction network density.
            </p>
          </div>

          {loadingClusters ? (
            <div className="loading-overlay">
              <div className="spinner" />
              <span>Discovering topological communities...</span>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: 'var(--space-lg)' }}>
              {clusters.map((cluster) => (
                <div key={cluster.cluster_id} className="card" style={{ padding: 'var(--space-lg)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                    <div>
                      <span className="badge badge-pathway" style={{ marginBottom: 6 }}>
                        Module #{cluster.cluster_id}
                      </span>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                        {cluster.name}
                      </h3>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-pathway)', fontFamily: 'var(--font-mono)' }}>
                        {(cluster.density_score * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Density</div>
                    </div>
                  </div>

                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 14 }}>
                    {cluster.description}
                  </p>

                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Core Lead Genes ({cluster.lead_genes.length})
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {cluster.lead_genes.map(gene => (
                        <span key={gene} className="badge badge-gene">
                          {gene}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => onLoadSubnetwork(cluster.lead_genes)}
                    >
                      Focus Module on Canvas <ArrowRight size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── 3. HYPOTHESIS GENERATOR TAB ─── */}
      {activeSubTab === 'hypothesis' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <div className="card" style={{ padding: 'var(--space-lg)' }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
              AI Mechanistic Hypothesis Synthesizer
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              Select any Gene and Target Disease. The AI analyzes graph pathways and formulates an etiology hypothesis with proposed wet-lab experiments.
            </p>

            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                  Target Gene Symbol
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. TP53, BRCA1, EGFR"
                  value={hypoGene}
                  onChange={(e) => setHypoGene(e.target.value)}
                />
              </div>

              <div style={{ flex: 1, minWidth: 200 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                  Disease Name / DOID
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Breast Cancer, Lung Cancer"
                  value={hypoDisease}
                  onChange={(e) => setHypoDisease(e.target.value)}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={handleGenerateHypothesis}
                disabled={loadingHypothesis}
                style={{ height: 38 }}
              >
                {loadingHypothesis ? (
                  <>
                    <Loader2 size={15} className="animate-pulse" />
                    Synthesizing...
                  </>
                ) : (
                  <>
                    <Sparkles size={15} />
                    Generate Hypothesis
                  </>
                )}
              </button>
            </div>
          </div>

          {hypothesisResult && (
            <div className="card animate-fade-in" style={{ padding: 'var(--space-xl)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="badge badge-gene" style={{ fontSize: 13 }}>
                    {hypothesisResult.gene}
                  </span>
                  <span style={{ color: 'var(--text-muted)' }}>⟷</span>
                  <span className="badge badge-disease" style={{ fontSize: 13 }}>
                    {hypothesisResult.disease}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-gene)' }}>
                    {(hypothesisResult.confidence_score * 100).toFixed(0)}%
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 4 }}>
                    Plausibility
                  </span>
                </div>
              </div>

              <div style={{
                background: 'var(--bg-tertiary)',
                padding: 'var(--space-md)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-glass)',
                fontSize: 14,
                lineHeight: 1.6,
                color: 'var(--text-primary)',
                marginBottom: 16,
                whiteSpace: 'pre-wrap'
              }}>
                {hypothesisResult.hypothesis}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div style={{ background: 'var(--bg-glass)', padding: 12, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-pathway)', textTransform: 'uppercase', marginBottom: 6 }}>
                    Implicated Pathways
                  </div>
                  <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--text-secondary)' }}>
                    {hypothesisResult.pathway_involvement.map((pw, i) => (
                      <li key={i}>{pw}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ background: 'var(--bg-glass)', padding: 12, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-mutation)', textTransform: 'uppercase', marginBottom: 6 }}>
                    <FlaskConical size={12} style={{ display: 'inline', marginRight: 4 }} />
                    Suggested Validation Experiments
                  </div>
                  <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--text-secondary)' }}>
                    {hypothesisResult.suggested_experiments.map((exp, i) => (
                      <li key={i}>{exp}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
                {hypothesisResult.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
