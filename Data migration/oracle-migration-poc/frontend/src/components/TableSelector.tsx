import React from 'react';
import { TableInfo } from '../types';
import './TableSelector.css';

interface TableSelectorProps {
  tables: TableInfo[];
  onTablesChange: (tables: TableInfo[]) => void;
}

const TableSelector: React.FC<TableSelectorProps> = ({ tables, onTablesChange }) => {
  const handleToggleTable = (index: number) => {
    const newTables = [...tables];
    newTables[index].selected = !newTables[index].selected;
    onTablesChange(newTables);
  };

  const handleSelectAll = () => {
    const newTables = tables.map((t) => ({ ...t, selected: true }));
    onTablesChange(newTables);
  };

  const handleDeselectAll = () => {
    const newTables = tables.map((t) => ({ ...t, selected: false }));
    onTablesChange(newTables);
  };

  const selectedCount = tables.filter((t) => t.selected).length;
  const totalSize = tables
    .filter((t) => t.selected)
    .reduce((sum, t) => sum + t.size_mb, 0);
  const totalRows = tables
    .filter((t) => t.selected)
    .reduce((sum, t) => sum + t.row_count, 0);

  return (
    <div className="table-selector">
      <div className="selector-header">
        <div className="selection-summary">
          <span className="summary-badge">
            {selectedCount} of {tables.length} tables selected
          </span>
          <span className="summary-badge">
            {totalSize.toFixed(2)} MB
          </span>
          <span className="summary-badge">
            {totalRows.toLocaleString()} rows
          </span>
        </div>
        <div className="selector-actions">
          <button className="btn btn-secondary btn-sm" onClick={handleSelectAll}>
            Select All
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleDeselectAll}>
            Deselect All
          </button>
        </div>
      </div>

      <div className="tables-grid">
        {tables.map((table, index) => (
          <div
            key={table.table_name}
            className={`table-card ${table.selected ? 'selected' : ''}`}
            onClick={() => handleToggleTable(index)}
          >
            <div className="table-checkbox">
              <input
                type="checkbox"
                checked={table.selected}
                onChange={() => handleToggleTable(index)}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
            <div className="table-info">
              <div className="table-name">{table.table_name}</div>
              <div className="table-schema">{table.schema_name}</div>
              <div className="table-stats">
                <span className="stat">
                  <span className="stat-icon">📊</span>
                  {table.row_count.toLocaleString()} rows
                </span>
                <span className="stat">
                  <span className="stat-icon">💾</span>
                  {table.size_mb.toFixed(2)} MB
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TableSelector;
