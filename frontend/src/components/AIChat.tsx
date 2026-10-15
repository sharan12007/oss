import { useState } from 'react';
import { askAI } from '../api';
import type { Subgraph } from '../types';
import { Send, Bot, User, Code, Share2, Sparkles, Loader2 } from 'lucide-react';

interface AIChatProps {
  onLoadSubgraph: (subgraph: Subgraph) => void;
  initialPrompt?: string;
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  cypher?: string;
  subgraph?: Subgraph;
  timestamp: string;
}

const PRESET_QUERIES = [
  "What genes are strongly associated with Breast Cancer?",
  "What mutations affect TP53 and what are their clinical impacts?",
  "How are EGFR and MAPK Signaling linked?",
  "Which pathways are associated with Alzheimer Disease and APOE?"
];

export const AIChat: React.FC<AIChatProps> = ({ onLoadSubgraph, initialPrompt }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Hello! I am GeneGraph AI. You can ask me natural language questions about genes, mutations, proteins, pathways, and diseases. I will query the Neo4j knowledge graph using safe Cypher and visualize the results for you.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState(initialPrompt || '');
  const [loading, setLoading] = useState(false);
  const [showCypher, setShowCypher] = useState<Record<string, boolean>>({});

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await askAI(textToSend);
      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: response.answer,
        cypher: response.cypher_query,
        subgraph: response.subgraph,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
      if (response.subgraph && response.subgraph.nodes.length > 0) {
        onLoadSubgraph(response.subgraph);
      }
    } catch (e: any) {
      setMessages(prev => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: `Error processing query: ${e.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleCypher = (msgId: string) => {
    setShowCypher(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="card chat-container" style={{ height: 'calc(100vh - 120px)' }}>
      {/* Header */}
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="sidebar-brand-icon" style={{ width: 32, height: 32, fontSize: 15 }}>
            <Sparkles size={16} />
          </div>
          <div>
            <div className="card-title">GeneGraph GraphRAG AI Assistant</div>
            <div className="card-subtitle">Natural language queries to Cypher & knowledge synthesis</div>
          </div>
        </div>
      </div>

      {/* Suggested prompts if few messages */}
      {messages.length <= 2 && (
        <div style={{ padding: '12px 16px', background: 'var(--bg-glass)', borderBottom: '1px solid var(--border-glass)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            Recommended Research Queries
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {PRESET_QUERIES.map((q, i) => (
              <button
                key={i}
                className="btn btn-secondary btn-sm"
                onClick={() => handleSend(q)}
                style={{ fontSize: 12, borderRadius: 20 }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Stream */}
      <div className="chat-messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`chat-message ${m.sender === 'user' ? 'chat-message-user' : 'chat-message-ai'}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, opacity: 0.8, fontSize: 11 }}>
              {m.sender === 'user' ? <User size={12} /> : <Bot size={12} />}
              <span style={{ fontWeight: 600 }}>{m.sender === 'user' ? 'You' : 'GeneGraph AI'}</span>
              <span>• {m.timestamp}</span>
            </div>

            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{m.text}</div>

            {/* Generated Cypher Query Pill */}
            {m.cypher && (
              <div style={{ marginTop: 12 }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => toggleCypher(m.id)}
                  style={{ fontSize: 11, padding: '3px 8px', marginBottom: 6 }}
                >
                  <Code size={12} />
                  {showCypher[m.id] ? 'Hide Cypher' : 'View Generated Cypher'}
                </button>
                {showCypher[m.id] && (
                  <pre
                    style={{
                      background: 'var(--bg-primary)',
                      padding: 10,
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 12,
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-gene)',
                      overflowX: 'auto',
                      border: '1px solid var(--border-primary)'
                    }}
                  >
                    {m.cypher}
                  </pre>
                )}
              </div>
            )}

            {/* Subgraph button */}
            {m.subgraph && m.subgraph.nodes.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => onLoadSubgraph(m.subgraph!)}
                  style={{ fontSize: 12 }}
                >
                  <Share2 size={12} />
                  Display {m.subgraph.nodes.length} Nodes in Graph Explorer
                </button>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-message chat-message-ai" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Loader2 className="animate-pulse" size={16} />
            <span>Analyzing knowledge graph and formulating Cypher...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <input
          type="text"
          className="input"
          placeholder="Ask a question (e.g., 'What diseases are linked to KRAS mutations?')..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={loading}
        />
        <button
          className="btn btn-primary"
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
        >
          <Send size={15} />
          Send
        </button>
      </div>

      <div className="chat-disclaimer">
        ⚠️ For research use only. This is not medical advice.
      </div>
    </div>
  );
};
