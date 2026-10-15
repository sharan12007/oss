import type { FC } from 'react';
import { 
  Network, 
  Sparkles, 
  Dna, 
  BarChart3, 
  FileText, 
  Cpu
} from 'lucide-react';

export type TabType = 'graph' | 'ai' | 'aiml' | 'catalog' | 'stats' | 'pubmed';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  neo4jStatus?: string;
}

export const Sidebar: FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="app-sidebar" style={{
      width: 'var(--sidebar-width)',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-glass)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      top: 0,
      bottom: 0,
      left: 0,
      zIndex: 50
    }}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Dna size={22} color="#ffffff" />
        </div>
        <div>
          <div className="sidebar-brand-text">GeneGraph</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            KNOWLEDGE EXPLORER
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Exploration</div>
        
        <button
          className={`sidebar-link ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <Network size={18} />
          <span>Graph Canvas</span>
        </button>

        <button
          className={`sidebar-link ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          <Sparkles size={18} />
          <span>GraphRAG AI Assistant</span>
        </button>

        <button
          className={`sidebar-link ${activeTab === 'aiml' ? 'active' : ''}`}
          onClick={() => setActiveTab('aiml')}
        >
          <Cpu size={18} />
          <span>AI / ML Studio</span>
        </button>

        <button
          className={`sidebar-link ${activeTab === 'catalog' ? 'active' : ''}`}
          onClick={() => setActiveTab('catalog')}
        >
          <Dna size={18} />
          <span>Gene & Variant Catalog</span>
        </button>

        <div className="sidebar-section-label" style={{ marginTop: 12 }}>Data & Ingestion</div>

        <button
          className={`sidebar-link ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          <BarChart3 size={18} />
          <span>Database Analytics</span>
        </button>

        <button
          className={`sidebar-link ${activeTab === 'pubmed' ? 'active' : ''}`}
          onClick={() => setActiveTab('pubmed')}
        >
          <FileText size={18} />
          <span>PubMed E-Utilities</span>
        </button>
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-disclaimer">
          ⚠️ <strong>For Research Use Only</strong><br />
          Not intended for clinical diagnostics or medical guidance.
        </div>
      </div>
    </aside>
  );
};
