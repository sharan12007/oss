import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { AuthPage } from './components/AuthPage';
import { Sidebar } from './components/Sidebar';
import type { TabType } from './components/Sidebar';
import { GraphView } from './components/GraphView';
import { NodeDetailPanel } from './components/NodeDetailPanel';
import { AIChat } from './components/AIChat';
import { StatsDashboard } from './components/StatsDashboard';
import { GeneCatalog } from './components/GeneCatalog';
import { PubMedIngest } from './components/PubMedIngest';
import { AIMLStudio } from './components/AIMLStudio';
import { CreateNodeModal } from './components/CreateNodeModal';
import { CreateEdgeModal } from './components/CreateEdgeModal';
import { 
  FALLBACK_GRAPH, 
  fetchHealth, 
  fetchNeighbors, 
  searchNodes 
} from './api';
import type { Subgraph, GraphNode, GraphEdge, SearchResult } from './types';
import { Search, Sparkles, RefreshCw, Cpu, LogOut, User } from 'lucide-react';
import './index.css';

export function App() {
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('graph');
  const [graphData, setGraphData] = useState<Subgraph>(FALLBACK_GRAPH);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [neo4jStatus, setNeo4jStatus] = useState<string>('checking');
  
  // Modals for CRUD operations
  const [isCreateNodeOpen, setIsCreateNodeOpen] = useState(false);
  const [isCreateEdgeOpen, setIsCreateEdgeOpen] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // Initial Health Check
  useEffect(() => {
    const checkConnection = async () => {
      const health = await fetchHealth();
      setNeo4jStatus(health.neo4j === 'connected' ? 'connected' : 'disconnected');
    };
    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  // Handle global search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      const results = await searchNodes(searchQuery);
      setSearchResults(results);
      setIsSearching(false);
      setShowSearchResults(true);
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Expand node neighbors (1-hop)
  const handleExpandNode = async (node: GraphNode) => {
    try {
      const neighborSubgraph = await fetchNeighbors(node.type, node.id, 1);
      if (neighborSubgraph && neighborSubgraph.nodes.length > 0) {
        setGraphData(prev => {
          const existingNodeIds = new Set(prev.nodes.map(n => n.id));
          const newNodes = neighborSubgraph.nodes.filter(n => !existingNodeIds.has(n.id));
          
          const existingEdgeKeys = new Set(prev.edges.map(e => `${e.source}->${e.target}:${e.type}`));
          const newEdges = neighborSubgraph.edges.filter(
            e => !existingEdgeKeys.has(`${e.source}->${e.target}:${e.type}`)
          );

          return {
            nodes: [...prev.nodes, ...newNodes],
            edges: [...prev.edges, ...newEdges]
          };
        });
      }
    } catch (e) {
      console.error('Failed to expand node:', e);
    }
  };

  // Focus and select node from search or catalog
  const handleExploreNode = async (type: string, id: string) => {
    setActiveTab('graph');
    try {
      const neighborSubgraph = await fetchNeighbors(type, id, 1);
      if (neighborSubgraph && neighborSubgraph.nodes.length > 0) {
        setGraphData(neighborSubgraph);
        const centerNode = neighborSubgraph.nodes.find(n => n.id === id) || neighborSubgraph.nodes[0];
        setSelectedNode(centerNode);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectSearchResult = (result: SearchResult) => {
    setShowSearchResults(false);
    setSearchQuery('');
    handleExploreNode(result.type, result.id);
  };

  // CRUD Event Handlers
  const handleNodeCreated = (newNode: GraphNode) => {
    setGraphData(prev => ({
      ...prev,
      nodes: [newNode, ...prev.nodes.filter(n => n.id !== newNode.id)]
    }));
    setSelectedNode(newNode);
    setActiveTab('graph');
  };

  const handleNodeUpdated = (updatedNode: GraphNode) => {
    setGraphData(prev => ({
      ...prev,
      nodes: prev.nodes.map(n => n.id === updatedNode.id ? updatedNode : n)
    }));
    setSelectedNode(updatedNode);
  };

  const handleNodeDeleted = (deletedNodeId: string) => {
    setGraphData(prev => ({
      nodes: prev.nodes.filter(n => n.id !== deletedNodeId),
      edges: prev.edges.filter(e => e.source !== deletedNodeId && e.target !== deletedNodeId)
    }));
    if (selectedNode?.id === deletedNodeId) {
      setSelectedNode(null);
    }
  };

  const handleEdgeCreated = (newEdge: GraphEdge) => {
    setGraphData(prev => ({
      ...prev,
      edges: [...prev.edges, newEdge]
    }));
  };

  const handleEdgeDeleted = (sourceId: string, targetId: string) => {
    setGraphData(prev => ({
      ...prev,
      edges: prev.edges.filter(e => !(
        (e.source === sourceId && e.target === targetId) ||
        (e.source === targetId && e.target === sourceId)
      ))
    }));
  };

  // Focus a functional community subnetwork
  const handleLoadSubnetwork = (symbols: string[]) => {
    const symbolSet = new Set(symbols);
    const subNodes = FALLBACK_GRAPH.nodes.filter(n => symbolSet.has(n.id) || symbolSet.has(n.label));
    const subEdges = FALLBACK_GRAPH.edges.filter(e => symbolSet.has(e.source) || symbolSet.has(e.target));
    if (subNodes.length > 0) {
      setGraphData({ nodes: subNodes, edges: subEdges });
    }
    setActiveTab('graph');
  };

  // ─── Auth Loading ────────────────────────────────────────────────────────
  if (authLoading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', background: 'var(--bg-primary)',
        color: 'var(--text-muted)', fontFamily: "'Inter', sans-serif",
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 32, height: 32, margin: '0 auto 12px',
            border: '3px solid rgba(99, 102, 241, 0.2)',
            borderTopColor: 'var(--color-gene)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }} />
          Loading GeneGraph...
        </div>
      </div>
    );
  }

  // ─── Auth Gate ──────────────────────────────────────────────────────────
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Left Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />

      {/* Main Content Area */}
      <main style={{
        marginLeft: 'var(--sidebar-width)',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        position: 'relative'
      }}>
        {/* Top Navbar */}
        <header style={{
          height: 64,
          borderBottom: '1px solid var(--border-glass)',
          background: 'var(--bg-glass)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-xl)',
          position: 'sticky',
          top: 0,
          zIndex: 40
        }}>
          {/* Global Search Bar */}
          <div style={{ position: 'relative', width: 440 }}>
            <div className="input-with-icon">
              <Search size={16} />
              <input
                type="text"
                className="input"
                placeholder="Search genes, diseases, proteins, mutations (e.g. TP53, BRCA1, Lung Cancer)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => searchQuery.trim() && setShowSearchResults(true)}
              />
            </div>

            {/* Auto-complete Dropdown */}
            {showSearchResults && (
              <div className="search-results">
                {isSearching ? (
                  <div style={{ padding: 16, fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
                    Searching knowledge graph...
                  </div>
                ) : searchResults.length === 0 ? (
                  <div style={{ padding: 16, fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
                    No matching entities found.
                  </div>
                ) : (
                  searchResults.map((item, idx) => (
                    <div
                      key={idx}
                      className="search-result-item"
                      onClick={() => handleSelectSearchResult(item)}
                    >
                      <span className={`node-dot node-dot-${item.type.toLowerCase()}`} />
                      <div style={{ flex: 1 }}>
                        <div className="search-result-label">{item.label}</div>
                        <div className="search-result-id">{item.id}</div>
                      </div>
                      <span className={`badge badge-${item.type.toLowerCase()}`}>{item.type}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Quick Shortcuts & Action Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setGraphData(FALLBACK_GRAPH);
                setSelectedNode(null);
              }}
              title="Reset graph to default seed view"
            >
              <RefreshCw size={13} />
              Reset
            </button>

            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setActiveTab('aiml')}
              title="Graph Machine Learning Link Predictor"
            >
              <Cpu size={13} />
              AI/ML Studio
            </button>

            <button
              className="btn btn-primary btn-sm"
              onClick={() => setActiveTab('ai')}
            >
              <Sparkles size={13} />
              AI Assistant
            </button>

            {/* User Profile & Logout */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginLeft: 8,
              paddingLeft: 12,
              borderLeft: '1px solid var(--border-glass)',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                background: 'rgba(129, 140, 248, 0.08)',
                borderRadius: 8,
                border: '1px solid rgba(129, 140, 248, 0.12)',
              }}>
                <User size={13} color="var(--color-gene)" />
                <span style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  maxWidth: 100,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {user?.username || 'User'}
                </span>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={logout}
                title="Sign out"
                style={{ padding: '6px 8px', minWidth: 'auto' }}
              >
                <LogOut size={13} />
              </button>
            </div>
          </div>
        </header>

        {/* Tab Body */}
        <div style={{ flex: 1, padding: 'var(--space-lg)', display: 'flex', overflow: 'hidden' }}>
          {activeTab === 'graph' && (
            <div style={{ display: 'flex', flex: 1, gap: 'var(--space-md)', position: 'relative' }}>
              <GraphView
                data={graphData}
                selectedNode={selectedNode}
                onSelectNode={setSelectedNode}
                onExpandNode={handleExpandNode}
                onOpenCreateNodeModal={() => setIsCreateNodeOpen(true)}
                onOpenCreateEdgeModal={() => setIsCreateEdgeOpen(true)}
              />
              <NodeDetailPanel
                node={selectedNode}
                onClose={() => setSelectedNode(null)}
                onExpand={handleExpandNode}
                onAskAI={() => {
                  setActiveTab('ai');
                }}
                graphData={graphData}
                onNodeUpdated={handleNodeUpdated}
                onNodeDeleted={handleNodeDeleted}
                onEdgeDeleted={handleEdgeDeleted}
              />
            </div>
          )}

          {activeTab === 'ai' && (
            <div style={{ flex: 1 }}>
              <AIChat
                onLoadSubgraph={(subgraph) => {
                  setGraphData(subgraph);
                  setActiveTab('graph');
                }}
              />
            </div>
          )}

          {activeTab === 'aiml' && (
            <div style={{ flex: 1 }}>
              <AIMLStudio
                onLoadSubnetwork={handleLoadSubnetwork}
                onEdgeAdded={(sourceId, targetId, type) => {
                  handleEdgeCreated({ source: sourceId, target: targetId, type });
                }}
              />
            </div>
          )}

          {activeTab === 'catalog' && (
            <div style={{ flex: 1 }}>
              <GeneCatalog onExploreGene={(symbol) => handleExploreNode('Gene', symbol)} />
            </div>
          )}

          {activeTab === 'stats' && (
            <div style={{ flex: 1 }}>
              <StatsDashboard onExploreNode={handleExploreNode} />
            </div>
          )}

          {activeTab === 'pubmed' && (
            <div style={{ flex: 1 }}>
              <PubMedIngest onIngestComplete={() => setActiveTab('stats')} />
            </div>
          )}
        </div>
      </main>

      {/* CRUD Modals */}
      <CreateNodeModal
        isOpen={isCreateNodeOpen}
        onClose={() => setIsCreateNodeOpen(false)}
        onNodeCreated={handleNodeCreated}
      />

      <CreateEdgeModal
        isOpen={isCreateEdgeOpen}
        onClose={() => setIsCreateEdgeOpen(false)}
        nodes={graphData.nodes}
        onEdgeCreated={handleEdgeCreated}
      />
    </div>
  );
}

export default App;
