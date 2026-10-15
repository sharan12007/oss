import { useState } from 'react';
import type { FC } from 'react';
import type { NodeType, GraphNode } from '../types';
import { createGraphNode } from '../api';
import { X, Plus, AlertCircle } from 'lucide-react';

interface CreateNodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNodeCreated: (node: GraphNode) => void;
}

export const CreateNodeModal: FC<CreateNodeModalProps> = ({
  isOpen,
  onClose,
  onNodeCreated
}) => {
  const [nodeType, setNodeType] = useState<NodeType>('Gene');
  const [nodeId, setNodeId] = useState('');
  const [nodeLabel, setNodeLabel] = useState('');
  const [extraProp1Name, setExtraProp1Name] = useState('name');
  const [extraProp1Val, setExtraProp1Val] = useState('');
  const [extraProp2Name, setExtraProp2Name] = useState('chromosome');
  const [extraProp2Val, setExtraProp2Val] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nodeId.trim()) {
      setError('Primary identifier is required');
      return;
    }

    setLoading(true);
    setError(null);

    const properties: Record<string, any> = {};
    if (extraProp1Name && extraProp1Val) properties[extraProp1Name] = extraProp1Val;
    if (extraProp2Name && extraProp2Val) properties[extraProp2Name] = extraProp2Val;

    try {
      const created = await createGraphNode({
        type: nodeType,
        id: nodeId.trim(),
        label: nodeLabel.trim() || nodeId.trim(),
        properties
      });
      onNodeCreated(created);
      onClose();
    } catch (err: any) {
      // Create locally if offline / fallback
      const localNode: GraphNode = {
        id: nodeId.trim(),
        type: nodeType,
        label: nodeLabel.trim() || nodeId.trim(),
        properties: { ...properties, symbol: nodeId.trim(), name: nodeLabel.trim() }
      };
      onNodeCreated(localNode);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (newType: NodeType) => {
    setNodeType(newType);
    if (newType === 'Gene') {
      setExtraProp1Name('name');
      setExtraProp2Name('chromosome');
    } else if (newType === 'Protein') {
      setExtraProp1Name('name');
      setExtraProp2Name('function');
    } else if (newType === 'Disease') {
      setExtraProp1Name('name');
      setExtraProp2Name('description');
    } else if (newType === 'Mutation') {
      setExtraProp1Name('hgvs');
      setExtraProp2Name('clinical_significance');
    } else if (newType === 'Pathway') {
      setExtraProp1Name('name');
      setExtraProp2Name('category');
    } else if (newType === 'Publication') {
      setExtraProp1Name('title');
      setExtraProp2Name('year');
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
              <Plus size={15} />
            </div>
            <div>
              <div className="card-title">Add Graph Entity</div>
              <div className="card-subtitle">Create a node in the Neo4j knowledge database</div>
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

          {/* Node Type Selector */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Entity Type
            </label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {(['Gene', 'Protein', 'Disease', 'Mutation', 'Pathway', 'Publication'] as NodeType[]).map(t => (
                <button
                  type="button"
                  key={t}
                  className={`filter-pill ${nodeType === t ? 'active' : ''}`}
                  onClick={() => handleTypeChange(t)}
                  style={{ fontSize: 12, padding: '4px 10px' }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* ID */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Primary Identifier * {nodeType === 'Gene' && '(e.g. TP53)'} {nodeType === 'Disease' && '(e.g. DOID:1612)'}
            </label>
            <input
              type="text"
              className="input"
              placeholder={nodeType === 'Gene' ? 'TP53' : nodeType === 'Protein' ? 'P04637' : 'ID...'}
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
              required
            />
          </div>

          {/* Label / Name */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Display Label / Name
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g. Tumor Protein P53"
              value={nodeLabel}
              onChange={(e) => setNodeLabel(e.target.value)}
            />
          </div>

          {/* Custom Properties */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                {extraProp1Name}
              </label>
              <input
                type="text"
                className="input"
                style={{ fontSize: 13 }}
                value={extraProp1Val}
                onChange={(e) => setExtraProp1Val(e.target.value)}
                placeholder="Value..."
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                {extraProp2Name}
              </label>
              <input
                type="text"
                className="input"
                style={{ fontSize: 13 }}
                value={extraProp2Val}
                onChange={(e) => setExtraProp2Val(e.target.value)}
                placeholder="Value..."
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Plus size={14} />
              {loading ? 'Creating...' : 'Create Entity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
