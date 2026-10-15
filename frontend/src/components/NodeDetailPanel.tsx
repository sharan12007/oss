import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { GraphNode, Subgraph } from '../types';
import { 
  X, 
  ExternalLink, 
  GitBranch, 
  Sparkles, 
  Database, 
  Edit3, 
  Trash2, 
  Save, 
  Check, 
  AlertTriangle 
} from 'lucide-react';
import { updateGraphNode, deleteGraphNode, deleteGraphEdge } from '../api';

interface NodeDetailPanelProps {
  node: GraphNode | null;
  onClose: () => void;
  onExpand: (node: GraphNode) => void;
  onAskAI: (prompt: string) => void;
  graphData: Subgraph;
  onNodeUpdated?: (node: GraphNode) => void;
  onNodeDeleted?: (nodeId: string) => void;
  onEdgeDeleted?: (sourceId: string, targetId: string) => void;
}

export const NodeDetailPanel: FC<NodeDetailPanelProps> = ({
  node,
  onClose,
  onExpand,
  onAskAI,
  graphData,
  onNodeUpdated,
  onNodeDeleted,
  onEdgeDeleted
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editLabel, setEditLabel] = useState('');
  const [editProperties, setEditProperties] = useState<Record<string, string>>({});
  const [isDeleting, setIsDeleting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (node) {
      setIsEditing(false);
      setIsDeleting(false);
      setMessage(null);
      setEditLabel(node.label);
      const strProps: Record<string, string> = {};
      Object.entries(node.properties || {}).forEach(([k, v]) => {
        if (k !== 'embedding' && typeof v !== 'object') {
          strProps[k] = String(v);
        }
      });
      setEditProperties(strProps);
    }
  }, [node]);

  if (!node) return null;

  // Find direct connections in current graph
  const connectedEdges = graphData.edges.filter(
    e => e.source === node.id || e.target === node.id
  );

  const neighbors = connectedEdges.map(e => {
    const isOut = e.source === node.id;
    const targetId = isOut ? e.target : e.source;
    const targetNode = graphData.nodes.find(n => n.id === targetId);
    return {
      edge: e,
      isOut,
      targetId,
      targetNode,
      relType: e.type
    };
  });

  const getBadgeClass = (type: string) => {
    const t = type.toLowerCase();
    return `badge badge-${t}`;
  };

  // Handle Save Update
  const handleSaveEdit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const updated = await updateGraphNode(node.type, node.id, {
        label: editLabel,
        properties: editProperties
      });
      setIsEditing(false);
      setMessage('Node updated successfully!');
      if (onNodeUpdated) {
        onNodeUpdated(updated);
      }
    } catch (err: any) {
      // In offline/mock mode, update locally
      const localUpdated: GraphNode = {
        ...node,
        label: editLabel,
        properties: { ...node.properties, ...editProperties }
      };
      setIsEditing(false);
      setMessage('Node updated locally.');
      if (onNodeUpdated) {
        onNodeUpdated(localUpdated);
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle Delete Node
  const handleDeleteNode = async () => {
    setLoading(true);
    try {
      await deleteGraphNode(node.type, node.id);
      if (onNodeDeleted) {
        onNodeDeleted(node.id);
      }
      onClose();
    } catch (err: any) {
      // Fallback local deletion
      if (onNodeDeleted) {
        onNodeDeleted(node.id);
      }
      onClose();
    } finally {
      setLoading(false);
    }
  };

  // Handle Delete Specific Edge
  const handleDeleteEdge = async (sourceId: string, targetId: string, relType: string) => {
    try {
      await deleteGraphEdge(sourceId, targetId, relType);
      if (onEdgeDeleted) {
        onEdgeDeleted(sourceId, targetId);
      }
    } catch (err) {
      if (onEdgeDeleted) {
        onEdgeDeleted(sourceId, targetId);
      }
    }
  };

  return (
    <aside className="detail-panel animate-slide-in">
      {/* Header */}
      <div className="detail-panel-header">
        <div>
          <span className={getBadgeClass(node.type)}>{node.type}</span>
          {!isEditing ? (
            <h2 style={{ fontSize: 20, fontWeight: 700, marginTop: 6, color: 'var(--text-primary)' }}>
              {node.label}
            </h2>
          ) : (
            <input
              type="text"
              className="input"
              style={{ marginTop: 6, fontWeight: 600, fontSize: 16 }}
              value={editLabel}
              onChange={(e) => setEditLabel(e.target.value)}
            />
          )}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onClose} title="Close panel">
          <X size={16} />
        </button>
      </div>

      {message && (
        <div style={{
          padding: '6px 12px',
          background: 'rgba(52, 211, 153, 0.1)',
          border: '1px solid rgba(52, 211, 153, 0.3)',
          borderRadius: 6,
          color: 'var(--color-success)',
          fontSize: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginBottom: 12
        }}>
          <Check size={14} />
          <span>{message}</span>
        </div>
      )}

      {/* Primary Action Buttons */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 'var(--space-md)', flexWrap: 'wrap' }}>
        <button
          className="btn btn-primary btn-sm"
          style={{ flex: 1 }}
          onClick={() => onExpand(node)}
          title="Expand 1-hop neighborhood"
        >
          <GitBranch size={13} />
          Expand
        </button>
        <button
          className="btn btn-secondary btn-sm"
          style={{ flex: 1 }}
          onClick={() => onAskAI(`Explain the biological role of ${node.type} ${node.label} and its significance.`)}
          title="Query GraphRAG Assistant"
        >
          <Sparkles size={13} />
          Ask AI
        </button>
        {!isEditing ? (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setIsEditing(true)}
            title="Edit node properties (CRUD)"
          >
            <Edit3 size={13} />
            Edit
          </button>
        ) : (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleSaveEdit}
            disabled={loading}
          >
            <Save size={13} />
            Save
          </button>
        )}
      </div>

      {/* Properties Section (Read & Edit Mode) */}
      <div className="detail-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div className="detail-section-title" style={{ marginBottom: 0 }}>Properties & Metadata</div>
          {isEditing && (
            <button
              className="btn btn-ghost btn-sm"
              style={{ fontSize: 11, padding: '2px 6px' }}
              onClick={() => {
                const key = prompt('Enter property name:');
                if (key && !editProperties[key]) {
                  setEditProperties(prev => ({ ...prev, [key]: '' }));
                }
              }}
            >
              + Add Property
            </button>
          )}
        </div>

        <div className="card" style={{ padding: 'var(--space-md)' }}>
          <div className="detail-prop">
            <span className="detail-prop-key">ID</span>
            <span className="detail-prop-value">{node.id}</span>
          </div>

          {!isEditing ? (
            Object.entries(node.properties || {}).map(([key, val]) => {
              if (key === 'embedding' || typeof val === 'object') return null;
              return (
                <div key={key} className="detail-prop">
                  <span className="detail-prop-key">{key}</span>
                  <span className="detail-prop-value" title={String(val)}>{String(val)}</span>
                </div>
              );
            })
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {Object.entries(editProperties).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)', width: 90, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {k}:
                  </span>
                  <input
                    type="text"
                    className="input"
                    style={{ padding: '4px 8px', fontSize: 12, flex: 1 }}
                    value={v}
                    onChange={(e) => setEditProperties({ ...editProperties, [k]: e.target.value })}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Connected Entities & Edge Deletion Section */}
      <div className="detail-section">
        <div className="detail-section-title">
          Connected Entities ({neighbors.length})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {neighbors.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              No connected neighbors in current view.
            </div>
          ) : (
            neighbors.map((item, idx) => (
              <div
                key={idx}
                className="search-result-item"
                style={{
                  background: 'var(--bg-glass)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-glass)',
                  padding: '8px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                  <Database size={13} style={{ color: 'var(--text-muted)' }} />
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>
                        {item.targetNode?.label || item.targetId}
                      </span>
                      <span className={getBadgeClass(item.targetNode?.type || 'Unknown')}>
                        {item.targetNode?.type || 'Unknown'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {item.isOut ? '──▶' : '◀──'} {item.relType}
                    </div>
                  </div>
                </div>

                {/* Disconnect Relationship Button */}
                <button
                  className="btn btn-ghost btn-sm"
                  style={{ padding: 4, color: 'var(--text-muted)' }}
                  onClick={() => handleDeleteEdge(item.edge.source, item.edge.target, item.relType)}
                  title="Remove relationship"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Danger Zone: Delete Node */}
      <div className="detail-section" style={{ marginTop: 'var(--space-xl)', borderTop: '1px solid var(--border-glass)', paddingTop: 16 }}>
        {!isDeleting ? (
          <button
            className="btn btn-secondary btn-sm"
            style={{ width: '100%', color: 'var(--color-error)', borderColor: 'rgba(248, 113, 113, 0.3)' }}
            onClick={() => setIsDeleting(true)}
          >
            <Trash2 size={13} />
            Delete Node from Database
          </button>
        ) : (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: 12
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-error)', fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
              <AlertTriangle size={14} />
              Confirm Node Deletion
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
              Are you sure? This will delete <strong>{node.label}</strong> and detach all connected relationships from the graph database.
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary btn-sm"
                style={{ flex: 1, background: '#ef4444', borderColor: '#dc2626' }}
                onClick={handleDeleteNode}
                disabled={loading}
              >
                Yes, Delete
              </button>
              <button
                className="btn btn-secondary btn-sm"
                style={{ flex: 1 }}
                onClick={() => setIsDeleting(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* External Links */}
      <div className="detail-section">
        <div className="detail-section-title">External Resources</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {node.type === 'Gene' && (
            <a
              href={`https://www.ncbi.nlm.nih.gov/gene/?term=${node.label}`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between' }}
            >
              <span>NCBI Gene Database</span>
              <ExternalLink size={12} />
            </a>
          )}
          {node.type === 'Protein' && (
            <a
              href={`https://www.uniprot.org/uniprotkb/${node.id}/entry`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
              style={{ justifyContent: 'space-between' }}
            >
              <span>UniProtKB Entry</span>
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
    </aside>
  );
};
