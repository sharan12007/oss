import { useState } from 'react';
import type { FC } from 'react';
import { FALLBACK_GRAPH } from '../api';
import { Search, ArrowRight, Dna } from 'lucide-react';

interface GeneCatalogProps {
  onExploreGene: (symbol: string) => void;
}

export const GeneCatalog: FC<GeneCatalogProps> = ({ onExploreGene }) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Extract all genes from known dataset
  const genes = FALLBACK_GRAPH.nodes.filter(n => n.type === 'Gene');

  const filteredGenes = genes.filter(g => 
    g.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (g.properties.name && g.properties.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (g.properties.chromosome && g.properties.chromosome.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <div className="page-header">
        <h1 className="page-title">Curated Gene & Variant Catalog</h1>
        <p className="page-description">
          Browse oncogenes, tumor suppressors, and neurodegenerative disease markers with direct graph subnetwork exploration.
        </p>
      </div>

      {/* Search Input */}
      <div className="search-bar" style={{ maxWidth: 400 }}>
        <div className="input-with-icon">
          <Search size={16} />
          <input
            type="text"
            className="input"
            placeholder="Filter genes (e.g., TP53, BRCA1, 17p13)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Genes Table Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Available Genes ({filteredGenes.length})</div>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Full Name</th>
                <th>Chromosome</th>
                <th>Ensembl ID</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredGenes.map((g) => (
                <tr key={g.id}>
                  <td>
                    <span className="badge badge-gene" style={{ fontSize: 12 }}>
                      <Dna size={12} style={{ marginRight: 4 }} />
                      {g.label}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                    {g.properties.name || g.label}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    {g.properties.chromosome || '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
                    {g.properties.ensembl_id || '—'}
                  </td>
                  <td>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => onExploreGene(g.label)}
                    >
                      Explore Graph <ArrowRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
