import { useEffect, useRef, useState } from 'react';
import type { FC } from 'react';
import cytoscape from 'cytoscape';
import type { Core } from 'cytoscape';
import type { Subgraph, GraphNode, NodeType } from '../types';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCcw, 
  Layers, 
  Download, 
  Plus, 
  Link2, 
  Compass,
  Sliders,
  Sparkles
} from 'lucide-react';

interface GraphViewProps {
  data: Subgraph;
  selectedNode: GraphNode | null;
  onSelectNode: (node: GraphNode | null) => void;
  onExpandNode?: (node: GraphNode) => void;
  onOpenCreateNodeModal?: () => void;
  onOpenCreateEdgeModal?: () => void;
}

const NODE_CONFIG: Record<string, { bg: string; border: string; shape: string }> = {
  Gene: { bg: '#818cf8', border: '#4f46e5', shape: 'round-rectangle' },
  Protein: { bg: '#34d399', border: '#059669', shape: 'ellipse' },
  Disease: { bg: '#f472b6', border: '#db2777', shape: 'diamond' },
  Mutation: { bg: '#fb923c', border: '#ea580c', shape: 'triangle' },
  Pathway: { bg: '#38bdf8', border: '#0284c7', shape: 'hexagon' },
  Publication: { bg: '#a78bfa', border: '#7c3aed', shape: 'round-tag' },
  Unknown: { bg: '#94a3b8', border: '#475569', shape: 'ellipse' }
};

const EDGE_COLORS: Record<string, string> = {
  ASSOCIATED_WITH: '#f472b6',
  ENCODES: '#818cf8',
  HAS_MUTATION: '#fb923c',
  PART_OF: '#38bdf8',
  INTERACTS_WITH: '#34d399',
  MENTIONS: '#a78bfa',
  LINKED_TO: '#f87171',
  DEFAULT: 'rgba(148, 163, 184, 0.4)'
};

export const GraphView: FC<GraphViewProps> = ({
  data,
  selectedNode,
  onSelectNode,
  onExpandNode,
  onOpenCreateNodeModal,
  onOpenCreateEdgeModal
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [layoutName, setLayoutName] = useState<string>('cose');
  const [scaleHubs, setScaleHubs] = useState<boolean>(true);
  const [showEdgeLabels, setShowEdgeLabels] = useState<boolean>(true);
  const [pathFindMode, setPathFindMode] = useState<boolean>(false);
  const [pathSource, setPathSource] = useState<string | null>(null);

  const [activeFilters, setActiveFilters] = useState<Record<NodeType, boolean>>({
    Gene: true,
    Protein: true,
    Disease: true,
    Mutation: true,
    Pathway: true,
    Publication: true,
  });

  const toggleFilter = (type: NodeType) => {
    setActiveFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  // Compute node degree to scale hub nodes visually
  const degreeMap: Record<string, number> = {};
  data.edges.forEach(e => {
    degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
    degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
  });

  // Export high-resolution PNG
  const handleExportPNG = () => {
    if (!cyRef.current) return;
    const png = cyRef.current.png({ full: true, scale: 2, bg: '#0a0e17' });
    const a = document.createElement('a');
    a.href = png;
    a.download = `genegraph-${Date.now()}.png`;
    a.click();
  };

  // Shortest path finder between two clicked nodes
  const handleNodePathSelect = (nodeId: string) => {
    if (!pathSource) {
      setPathSource(nodeId);
      if (cyRef.current) {
        cyRef.current.elements().removeClass('highlighted dimmed path-node path-edge');
        cyRef.current.$(`node[id = "${nodeId}"]`).addClass('path-node');
      }
    } else {
      if (pathSource === nodeId) {
        setPathSource(null);
        cyRef.current?.elements().removeClass('highlighted dimmed path-node path-edge');
        return;
      }
      // Compute dijkstra shortest path
      if (cyRef.current) {
        const dijkstra = cyRef.current.elements().dijkstra({
          root: `node[id = "${pathSource}"]`,
          directed: false
        });
        const pathToTarget = dijkstra.pathTo(cyRef.current.$(`node[id = "${nodeId}"]`));
        if (pathToTarget && pathToTarget.length > 0) {
          cyRef.current.elements().addClass('dimmed');
          pathToTarget.removeClass('dimmed').addClass('highlighted path-edge');
        }
      }
      setPathSource(null);
      setPathFindMode(false);
    }
  };

  // Initialize and update Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    const filteredNodes = data.nodes.filter(n => activeFilters[n.type as NodeType] !== false);
    const validNodeIds = new Set(filteredNodes.map(n => n.id));

    const elements = [
      ...filteredNodes.map(node => {
        const deg = degreeMap[node.id] || 1;
        const size = scaleHubs ? Math.min(Math.max(34 + deg * 3.5, 34), 64) : 38;
        return {
          data: {
            id: node.id,
            label: node.label,
            type: node.type,
            size,
            degree: deg,
            raw: node
          }
        };
      }),
      ...data.edges
        .filter(edge => validNodeIds.has(edge.source) && validNodeIds.has(edge.target))
        .map((edge, idx) => {
          const score = edge.properties?.score ? Number(edge.properties.score) : 1.0;
          const width = Math.min(Math.max(score * 2.5, 1.5), 5.0);
          return {
            data: {
              id: `edge-${idx}-${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
              label: edge.type,
              width,
              raw: edge
            }
          };
        })
    ];

    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'color': '#f8fafc',
              'font-size': '11px',
              'font-family': 'Inter, -apple-system, sans-serif',
              'font-weight': 600,
              'text-valign': 'bottom',
              'text-margin-y': 7,
              'text-outline-color': '#0a0e17',
              'text-outline-width': 3,
              'text-outline-opacity': 0.95,
              'width': 'data(size)',
              'height': 'data(size)',
              'shape': (ele: any) => {
                const t = ele.data('type') || 'Unknown';
                return (NODE_CONFIG[t]?.shape as any) || 'ellipse';
              },
              'background-color': (ele: any) => {
                const t = ele.data('type') || 'Unknown';
                return NODE_CONFIG[t]?.bg || '#818cf8';
              },
              'border-width': 2.5,
              'border-color': (ele: any) => {
                const t = ele.data('type') || 'Unknown';
                return NODE_CONFIG[t]?.border || '#ffffff';
              },
              'border-opacity': 0.9,
              'transition-property': 'background-color, border-color, width, height, opacity',
              'transition-duration': 250
            }
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 4,
              'border-color': '#ffffff',
              'border-opacity': 1.0,
              'overlay-padding': 8,
              'overlay-color': '#6366f1',
              'overlay-opacity': 0.25
            }
          },
          {
            selector: 'node.highlighted',
            style: {
              'border-width': 4,
              'border-color': '#f59e0b',
              'overlay-padding': 10,
              'overlay-color': '#f59e0b',
              'overlay-opacity': 0.3,
              'opacity': 1
            }
          },
          {
            selector: 'node.path-node',
            style: {
              'border-width': 4,
              'border-color': '#10b981',
              'overlay-padding': 8,
              'overlay-color': '#10b981',
              'overlay-opacity': 0.3
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 'data(width)',
              'line-color': (ele: any) => {
                const type = ele.data('label') || '';
                return EDGE_COLORS[type] || EDGE_COLORS.DEFAULT;
              },
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              'target-arrow-color': (ele: any) => {
                const type = ele.data('label') || '';
                return EDGE_COLORS[type] || EDGE_COLORS.DEFAULT;
              },
              'arrow-scale': 0.85,
              'label': showEdgeLabels ? 'data(label)' : '',
              'font-size': '9px',
              'font-family': 'JetBrains Mono, monospace',
              'font-weight': 500,
              'color': '#cbd5e1',
              'text-rotation': 'autorotate',
              'text-background-opacity': 0.9,
              'text-background-color': '#0f172a',
              'text-background-padding': '2.5px',
              'text-background-shape': 'roundrectangle',
              'opacity': 0.85
            }
          },
          {
            selector: 'edge:selected',
            style: {
              'width': 4,
              'line-color': '#818cf8',
              'target-arrow-color': '#818cf8',
              'opacity': 1.0
            }
          },
          {
            selector: 'edge.highlighted',
            style: {
              'width': 4.5,
              'line-color': '#f59e0b',
              'target-arrow-color': '#f59e0b',
              'opacity': 1,
              'line-style': 'dashed'
            }
          },
          {
            selector: '.dimmed',
            style: {
              'opacity': 0.15
            }
          }
        ],
        layout: {
          name: layoutName,
          padding: 60,
          animate: true,
          animationDuration: 600,
          randomize: false
        } as any,
        wheelSensitivity: 0.2
      });

      // Events
      cyRef.current.on('tap', 'node', (evt) => {
        const rawNode = evt.target.data('raw');
        if (pathFindMode) {
          handleNodePathSelect(rawNode.id);
        } else {
          onSelectNode(rawNode);
          // Spotlight 1-hop neighborhood
          cyRef.current?.elements().removeClass('highlighted dimmed');
          const neighborhood = evt.target.neighborhood().add(evt.target);
          cyRef.current?.elements().not(neighborhood).addClass('dimmed');
        }
      });

      cyRef.current.on('tap', (evt) => {
        if (evt.target === cyRef.current) {
          onSelectNode(null);
          cyRef.current?.elements().removeClass('highlighted dimmed path-node path-edge');
        }
      });

      cyRef.current.on('dbltap', 'node', (evt) => {
        const rawNode = evt.target.data('raw');
        if (onExpandNode) {
          onExpandNode(rawNode);
        }
      });
    } else {
      cyRef.current.elements().remove();
      cyRef.current.add(elements);
      cyRef.current.layout({
        name: layoutName,
        padding: 60,
        animate: true,
        animationDuration: 450
      } as any).run();
    }
  }, [data, activeFilters, layoutName, scaleHubs, showEdgeLabels, pathFindMode]);

  // Synchronize selection
  useEffect(() => {
    if (!cyRef.current) return;
    if (selectedNode) {
      cyRef.current.$(`node[id = "${selectedNode.id}"]`).select();
    } else {
      cyRef.current.$(':selected').unselect();
    }
  }, [selectedNode]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 50);
  const handleReset = () => {
    cyRef.current?.elements().removeClass('highlighted dimmed path-node path-edge');
    cyRef.current?.reset();
    cyRef.current?.layout({ name: layoutName, animate: true } as any).run();
  };

  return (
    <div className="graph-container">
      {/* Unified Controls Bar */}
      <div className="graph-controls-bar">
        <div className="graph-controls-row">
          {/* Zoom Controls */}
          <div className="controls-group">
            <button className="btn btn-secondary btn-sm" onClick={handleZoomIn} title="Zoom In">
              <ZoomIn size={14} />
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleZoomOut} title="Zoom Out">
              <ZoomOut size={14} />
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleFit} title="Fit to Screen">
              <Maximize2 size={14} />
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleReset} title="Reset View">
              <RotateCcw size={14} />
            </button>
          </div>

          <div className="controls-divider" />

          {/* Layout Selector */}
          <div className="controls-group">
            <Layers size={14} style={{ color: 'var(--text-muted)' }} />
            <select
              className="input"
              style={{ padding: '3px 8px', fontSize: 12, height: 28, width: 125 }}
              value={layoutName}
              onChange={(e) => setLayoutName(e.target.value)}
            >
              <option value="cose">Force-Directed</option>
              <option value="concentric">Concentric</option>
              <option value="circle">Circular</option>
              <option value="breadthfirst">Hierarchical</option>
              <option value="grid">Grid</option>
            </select>
          </div>

          <div className="controls-divider" />

          {/* View Toggles */}
          <div className="controls-group">
            <button
              className={`btn btn-secondary btn-sm ${scaleHubs ? 'active' : ''}`}
              onClick={() => setScaleHubs(!scaleHubs)}
              title="Scale node size by degree centrality"
              style={{ background: scaleHubs ? 'var(--bg-active)' : undefined, borderColor: scaleHubs ? 'var(--color-gene)' : undefined }}
            >
              <Sliders size={13} />
              Hubs
            </button>
            <button
              className={`btn btn-secondary btn-sm ${showEdgeLabels ? 'active' : ''}`}
              onClick={() => setShowEdgeLabels(!showEdgeLabels)}
              title="Toggle edge labels"
              style={{ background: showEdgeLabels ? 'var(--bg-active)' : undefined, borderColor: showEdgeLabels ? 'var(--color-protein)' : undefined }}
            >
              Labels
            </button>
            <button
              className={`btn btn-secondary btn-sm ${pathFindMode ? 'active' : ''}`}
              onClick={() => {
                setPathFindMode(!pathFindMode);
                setPathSource(null);
                cyRef.current?.elements().removeClass('highlighted dimmed path-node path-edge');
              }}
              title="Interactive path finder between two nodes"
              style={{
                background: pathFindMode ? 'rgba(245, 158, 11, 0.2)' : undefined,
                borderColor: pathFindMode ? '#f59e0b' : undefined,
                color: pathFindMode ? '#f59e0b' : undefined
              }}
            >
              <Compass size={13} />
              {pathFindMode ? (pathSource ? 'Target...' : 'Source...') : 'Path'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleExportPNG} title="Download high-res PNG">
              <Download size={13} />
            </button>
          </div>

          {/* Spacer pushes right section */}
          <div className="controls-spacer" />

          {/* CRUD Actions */}
          <div className="controls-group">
            {onOpenCreateNodeModal && (
              <button className="btn btn-primary btn-sm" onClick={onOpenCreateNodeModal}>
                <Plus size={13} />
                Node
              </button>
            )}
            {onOpenCreateEdgeModal && (
              <button className="btn btn-secondary btn-sm" onClick={onOpenCreateEdgeModal}>
                <Link2 size={13} />
                Edge
              </button>
            )}
          </div>

          <div className="controls-divider" />

          {/* Type Filter Pills */}
          <div className="controls-group" style={{ flexWrap: 'wrap' }}>
            {(Object.keys(activeFilters) as NodeType[]).map(type => (
              <button
                key={type}
                className={`filter-pill ${activeFilters[type] ? 'active' : ''}`}
                onClick={() => toggleFilter(type)}
                style={{ borderColor: activeFilters[type] ? NODE_CONFIG[type]?.bg : undefined }}
              >
                <span className="node-dot" style={{ background: NODE_CONFIG[type]?.bg }} />
                {type}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Interactive Cytoscape Canvas */}
      <div ref={containerRef} className="graph-canvas" />

      {/* Path Finder Banner */}
      {pathFindMode && (
        <div style={{
          position: 'absolute',
          top: 60,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(15, 23, 42, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #f59e0b',
          borderRadius: 20,
          padding: '6px 16px',
          fontSize: 12,
          color: '#f59e0b',
          zIndex: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
        }}>
          <Sparkles size={14} />
          <span>
            {pathSource
              ? `Source '${pathSource}' selected. Click any target node to find shortest path!`
              : 'Click first node to set Path Source.'}
          </span>
          <button
            style={{ background: 'transparent', border: 'none', color: '#cbd5e1', cursor: 'pointer', marginLeft: 8 }}
            onClick={() => { setPathFindMode(false); setPathSource(null); }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Bottom Left Legend */}
      <div className="graph-legend-overlay">
        <div className="graph-legend">
          {Object.entries(NODE_CONFIG).filter(([k]) => k !== 'Unknown').map(([type, cfg]) => (
            <div key={type} className="legend-item">
              <span className="node-dot" style={{ background: cfg.bg }} />
              <span>{type}</span>
            </div>
          ))}
          <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>
            (Double-click to expand • Click to spotlight)
          </span>
        </div>
      </div>
    </div>
  );
};
