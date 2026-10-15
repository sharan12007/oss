import { useState } from 'react';
import type { FC } from 'react';
import type { GraphNode, GraphEdge } from '../types';
import { createGraphEdge } from '../api';
import { X, Link2, AlertCircle } from 'lucide-react';

interface CreateEdgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: GraphNode[];
  onEdgeCreated: (edge: GraphEdge) => void;
}

const REL_TYPES = [
  'ASSOCIATED_WITH',
  'ENCODES',
  'HAS_MUTATION',
  'INTERACTS_WITH',
  'PART_OF',
  'MENTIONS',
  'LINKED_TO'
];

export const CreateEdgeModal: FC<CreateEdgeModalProps> = ({
  isOpen,
  onClose,
  nodes,
  onEdgeCreated
}) => {
  const [sourceId, setSourceId] = useState(nodes[0]?.id || '');
  const [targetId, setTargetId] = useState(nodes[1]?.id || '');
  const [relType, setRelType] = useState('ASSOCIATED_WITH');
  const [score, setScore] = useState(0.85);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId || !targetId) {
      setError('Please select both source and target entities');
      return;
    }
    if (sourceId === targetId) {
      setError('Source and target must be different nodes');
      return;
    }

    setLoading(true);
    setError(null);

    const properties = { score };

    try {
      await createGraphEdge({
        source_id: sourceId,
        target_id: targetId,
        type: relType,
        properties
      });
      onEdgeCreated({
        source: sourceId,
        target: targetId,
        type: relType,
        properties
      });
      onClose();
    } catch (err: any) {
      // Fallback local creation
      onEdgeCreated({
        source: sourceId,
        target: targetId,
        type: relType,
        properties
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="card animate-fade-in" style={{ width: 480, maxWidth: '90vw', padding: 0 }}>
        {/* Header */}
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="sidebar-brand-icon" style={{ width: 28, height: 28, fontSize: 13 }}>
              <Link2 size={15} />
            </div>
            <div>
              <div className="card-title">Connect Graph Entities</div>
              <div className="card-subtitle">Establish a typed relationship in the Neo4j database</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: 'var(--space-lg)' }}>
          {error && (
            <div style={{
              padding: '8px 12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 6,
              color: 'var(--color-error)',
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 16
            }}>
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}

          {/* Source Node */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Source Entity
            </label>
            <select
              className="input"
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              required
            >
              {nodes.map(n => (
                <option key={n.id} value={n.id}>
                  [{n.type}] {n.label} ({n.id})
                </option>
              ))}
            </select>
          </div>

          {/* Relationship Type */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Relationship Type
            </label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {REL_TYPES.map(rt => (
                <button
                  type="button"
                  key={rt}
                  className={`filter-pill ${relType === rt ? 'active' : ''}`}
                  onClick={() => setRelType(rt)}
                  style={{ fontSize: 11, padding: '3px 8px' }}
                >
                  {rt}
                </button>
              ))}
            </div>
          </div>

          {/* Target Node */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Target Entity
            </label>
            <select
              className="input"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              required
            >
              {nodes.map(n => (
                <option key={n.id} value={n.id}>
                  [{n.type}] {n.label} ({n.id})
                </option>
              ))}
            </select>
          </div>

          {/* Score Slider */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Confidence / Association Score</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-accent)' }}>{score.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={score}
              onChange={(e) => setScore(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--color-gene)' }}
            />
          </div>

          {/* Footer Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Link2 size={14} />
              {loading ? 'Connecting...' : 'Connect Entities'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
