import React from 'react';
import { TableInfo, DependencyInfo } from '../types';
import { IconCheck, IconChevronRight } from './ui/Icons';
import './TableSelector.css';

interface TableSelectorProps {
  tables: TableInfo[];
  onTablesChange: (tables: TableInfo[]) => void;
  /** Dependency metadata from the schema analysis, used for the dependencies column. */
  dependencies?: DependencyInfo[];
}

const TableSelector: React.FC<TableSelectorProps> = ({
  tables,
  onTablesChange,
  dependencies = [],
}) => {
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

  const schemaName = tables.length > 0 ? tables[0].schema_name : '';

  /** Human-readable dependency count for a table, from the analysed schema. */
  const dependencyLabel = (tableName: string): string => {
    const entry = dependencies.find((d) => d.table_name === tableName);
    const count = entry ? entry.depends_on.length : 0;
    if (count === 0) return 'None';
    return count === 1 ? '1 table' : `${count} tables`;
  };

  return (
    <div className="card">
      <div className="card-head bordered">
        <div>
          <h2 className="card-title">Discovered tables</h2>
          <p className="card-subtitle">
            {tables.length} tables found in <strong>{schemaName}</strong>. Select what
            you want to migrate.
          </p>
        </div>
        <div className="row-center">
          <button type="button" className="btn-link" onClick={handleSelectAll}>
            Select all
          </button>
          <span className="link-divider" />
          <button type="button" className="btn-link" onClick={handleDeselectAll}>
            Clear
          </button>
        </div>
      </div>

      <div className="select-summary">
        <div className="summary-facts">
          <span>
            <strong>{selectedCount}</strong> of {tables.length} selected
          </span>
          <span>
            <strong>{totalRows.toLocaleString()}</strong> rows
          </span>
          <span>
            <strong>{totalSize.toFixed(2)}</strong> MB
          </span>
        </div>
        <span className="summary-ok">
          <IconCheck size={14} />
          Dependencies resolved
        </span>
      </div>

      <div className="card-body flush">
        <table className="data-table object-table">
          <thead>
            <tr>
              <th className="col-check" />
              <th>Table name</th>
              <th>Rows</th>
              <th>Size</th>
              <th>Dependencies</th>
              <th className="col-chevron" />
            </tr>
          </thead>
          <tbody>
            {tables.map((table, index) => (
              <tr
                key={table.table_name}
                className={table.selected ? 'is-selected' : ''}
                onClick={() => handleToggleTable(index)}
              >
                <td className="col-check">
                  <input
                    type="checkbox"
                    className="checkbox"
                    checked={table.selected}
                    onChange={() => handleToggleTable(index)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
                <td>
                  <div className="cell-strong">{table.table_name}</div>
                  <div className="cell-sub">{table.schema_name}</div>
                </td>
                <td>{table.row_count.toLocaleString()}</td>
                <td>{table.size_mb.toFixed(2)} MB</td>
                <td>{dependencyLabel(table.table_name)}</td>
                <td className="col-chevron">
                  <IconChevronRight size={15} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TableSelector;
