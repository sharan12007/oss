import { useState } from 'react';
import type { FC } from 'react';
import { fetchPubmedAbstract } from '../api';
import type { IngestReview } from '../types';
import { FileText, Search, CheckCircle, BookOpen, Database } from 'lucide-react';

interface PubMedIngestProps {
  onIngestComplete?: () => void;
}

export const PubMedIngest: FC<PubMedIngestProps> = ({ onIngestComplete }) => {
  const [pmid, setPmid] = useState('25741868');
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState<IngestReview | null>(null);
  const [approved, setApproved] = useState(false);

  const handleFetch = async (targetPmid?: string) => {
    const id = targetPmid || pmid;
    if (!id.trim() || loading) return;
    setLoading(true);
    setApproved(false);
    try {
      const data = await fetchPubmedAbstract(id);
      setReview(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = () => {
    setApproved(true);
    if (onIngestComplete) {
      onIngestComplete();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      <div className="page-header">
        <h1 className="page-title">PubMed Literature Ingestion</h1>
        <p className="page-description">
          Ingest peer-reviewed biomedical literature directly from NCBI PubMed via E-utilities API.
          Extract Gene, Disease, and Variant associations with human-in-the-loop validation.
        </p>
      </div>

      {/* Query Bar */}
      <div className="card" style={{ padding: 'var(--space-lg)' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div className="input-with-icon" style={{ flex: 1, maxWidth: 360 }}>
            <FileText size={16} />
            <input
              type="text"
              className="input"
              placeholder="Enter PubMed ID (e.g., 25741868, 30510156)..."
              value={pmid}
              onChange={(e) => setPmid(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={() => handleFetch()}
            disabled={loading || !pmid.trim()}
          >
            <Search size={14} />
            {loading ? 'Fetching from NCBI...' : 'Fetch & Extract'}
          </button>
        </div>

        {/* Quick sample chips */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 12, fontSize: 12 }}>
          <span style={{ color: 'var(--text-muted)' }}>Try PMIDs:</span>
          {['25741868', '30510156', '31744836'].map((id) => (
            <button
              key={id}
              className="btn btn-secondary btn-sm"
              onClick={() => { setPmid(id); handleFetch(id); }}
            >
              PMID:{id}
            </button>
          ))}
        </div>
      </div>

      {/* Results & Extracted Entities */}
      {review && (
        <div className="card animate-fade-in" style={{ padding: 'var(--space-xl)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <span className="badge badge-publication" style={{ marginBottom: 8 }}>
                PubMed Article • Year {review.year || '2024'}
              </span>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                {review.title}
              </h2>
            </div>
            <a
              href={`https://pubmed.ncbi.nlm.nih.gov/${review.pmid}/`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
            >
              <span>View on NCBI</span>
              <BookOpen size={12} />
            </a>
          </div>

          <div style={{
            background: 'var(--bg-tertiary)',
            padding: 'var(--space-md)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-glass)',
            fontSize: 14,
            lineHeight: 1.6,
            color: 'var(--text-secondary)',
            marginBottom: 'var(--space-lg)'
          }}>
            {review.abstract}
          </div>

          {/* Extracted Entities Table */}
          <div style={{ marginBottom: 'var(--space-lg)' }}>
            <div style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              AI-Extracted Biomedical Entities ({review.entities.length})
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {review.entities.map((ent, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-glass)',
                    border: '1px solid var(--border-glass)',
                    fontSize: 13
                  }}
                >
                  <span className={`node-dot node-dot-${ent.type.toLowerCase()}`} />
                  <span style={{ fontWeight: 600 }}>{ent.name}</span>
                  <span className={`badge badge-${ent.type.toLowerCase()}`}>{ent.type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Extracted Relationships */}
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <div style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              Candidate Graph Triples ({review.relationships.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {review.relationships.map((rel, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-glass)',
                    border: '1px solid var(--border-glass)',
                    fontSize: 13,
                    fontFamily: 'var(--font-mono)'
                  }}
                >
                  <span style={{ color: 'var(--color-gene)' }}>({rel.source})</span>
                  <span style={{ color: 'var(--text-muted)' }}>-[:{rel.type}]-&gt;</span>
                  <span style={{ color: 'var(--color-disease)' }}>({rel.target})</span>
                </div>
              ))}
            </div>
          </div>

          {/* Approval Action */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            {approved ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-success)', fontWeight: 600 }}>
                <CheckCircle size={18} />
                <span>Merged into Active Knowledge Graph</span>
              </div>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={handleApprove}>
                <Database size={16} />
                Approve & Merge into Neo4j
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
