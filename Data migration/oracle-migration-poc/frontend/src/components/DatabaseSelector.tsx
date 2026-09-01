import React, { useEffect, useState } from 'react';
import { DatabaseConfig, DatabaseType } from '../types';
import { discoveryApi } from '../services/api';
import './DatabaseSelector.css';

interface DatabaseSelectorProps {
  onSelect: (databases: {
    source?: DatabaseConfig;
    intermediate?: DatabaseConfig;
    target?: DatabaseConfig;
  }) => void;
}

// Hard-coded connection details matching backend .env
// The /api/discovery/databases endpoint returns metadata; we enrich with credentials here.
const KNOWN_DATABASES: DatabaseConfig[] = [
  {
    db_id: 'source_oracle',
    db_type: DatabaseType.ORACLE_19C_STANDALONE,
    host: 'localhost',
    port: 1521,
    service_name: 'XEPDB1',
    username: 'migration_user',
    password: 'MigrationPwd123',
    description: 'Oracle XE 21c – Source DB (16 500 rows)',
  },
  {
    db_id: 'target_oracle',
    db_type: DatabaseType.ORACLE_23C_CDB_PDB,
    host: 'localhost',
    port: 1522,
    service_name: 'XEPDB1',
    username: 'migration_user',
    password: 'MigrationPwd123',
    description: 'Oracle XE 21c – Target DB (empty)',
  },
];

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({ onSelect }) => {
  const [databases, setDatabases] = useState<DatabaseConfig[]>(KNOWN_DATABASES);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<Record<string, 'ok' | 'fail' | 'idle'>>({});
  const [selectedSource, setSelectedSource] = useState<string>('source_oracle');
  const [selectedTarget, setSelectedTarget] = useState<string>('target_oracle');

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      // Merge API metadata with our known credentials
      const apiData: DatabaseConfig[] = await discoveryApi.listDatabases();
      const merged = KNOWN_DATABASES.map((known) => {
        const fromApi = apiData.find((d) => d.db_id === known.db_id);
        return fromApi ? { ...known, ...fromApi, username: known.username, password: known.password } : known;
      });
      setDatabases(merged);
    } catch {
      // Fall back to hard-coded list if API fails
    } finally {
      setLoading(false);
    }
  };

  const testConnections = async () => {
    setTesting(true);
    const results: Record<string, 'ok' | 'fail' | 'idle'> = {};
    for (const db of databases) {
      try {
        await discoveryApi.testConnection(db);
        results[db.db_id] = 'ok';
      } catch {
        results[db.db_id] = 'fail';
      }
    }
    setConnectionStatus(results);
    setTesting(false);
  };

  const handleContinue = () => {
    const source = databases.find((db) => db.db_id === selectedSource);
    const target = databases.find((db) => db.db_id === selectedTarget);
    onSelect({ source, target });
  };

  const canContinue = selectedSource && selectedTarget && selectedSource !== selectedTarget;

  if (loading) {
    return (
      <div className="card">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading available databases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="database-selector">
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Select Migration Databases</h2>
            <p className="card-subtitle">
              Configure source and target databases, then start the AI-powered migration
            </p>
          </div>
          <button
            className="btn btn-secondary"
            onClick={testConnections}
            disabled={testing}
          >
            {testing ? 'Testing...' : 'Test Connections'}
          </button>
        </div>

        <div className="migration-flow">
          {/* Source */}
          <div className="flow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Source Database</h3>
              <p>Oracle 21c XE — pre-loaded with 16 500 rows</p>
              <select
                className="db-select"
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
              >
                <option value="">Select database...</option>
                {databases.map((db) => (
                  <option key={db.db_id} value={db.db_id}>
                    {db.description || db.db_id}
                  </option>
                ))}
              </select>
              {selectedSource && (() => {
                const db = databases.find((d) => d.db_id === selectedSource);
                return db ? (
                  <div className="db-info">
                    <span>{db.host}:{db.port}/{db.service_name}</span>
                    {connectionStatus[db.db_id] === 'ok' && <span className="conn-ok"> ✓ Connected</span>}
                    {connectionStatus[db.db_id] === 'fail' && <span className="conn-fail"> ✗ Failed</span>}
                  </div>
                ) : null;
              })()}
            </div>
          </div>

          <div className="flow-arrow">→</div>

          {/* Target */}
          <div className="flow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>Target Database</h3>
              <p>Oracle 21c XE — empty, ready to receive data</p>
              <select
                className="db-select"
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
              >
                <option value="">Select database...</option>
                {databases.map((db) => (
                  <option key={db.db_id} value={db.db_id}>
                    {db.description || db.db_id}
                  </option>
                ))}
              </select>
              {selectedTarget && (() => {
                const db = databases.find((d) => d.db_id === selectedTarget);
                return db ? (
                  <div className="db-info">
                    <span>{db.host}:{db.port}/{db.service_name}</span>
                    {connectionStatus[db.db_id] === 'ok' && <span className="conn-ok"> ✓ Connected</span>}
                    {connectionStatus[db.db_id] === 'fail' && <span className="conn-fail"> ✗ Failed</span>}
                  </div>
                ) : null;
              })()}
            </div>
          </div>
        </div>

        <div className="migration-info">
          <h3>What happens when you start</h3>
          <div className="info-grid">
            <div className="info-card">
              <div className="info-icon step1">1</div>
              <h4>AI Analysis</h4>
              <p>Agent reads source schema, resolves FK dependencies, and builds migration order</p>
            </div>
            <div className="info-card">
              <div className="info-icon step2">2</div>
              <h4>Human Approval</h4>
              <p>Review the generated plan before any data is moved</p>
            </div>
            <div className="info-card">
              <div className="info-icon" style={{ background: '#10b981' }}>3</div>
              <h4>Execute & Validate</h4>
              <p>Real data copy via oracledb thin driver with row-count validation</p>
            </div>
          </div>
        </div>

        <div className="selector-actions">
          <button
            className="btn btn-primary btn-lg"
            onClick={handleContinue}
            disabled={!canContinue}
          >
            Continue to Migration Dashboard →
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatabaseSelector;
