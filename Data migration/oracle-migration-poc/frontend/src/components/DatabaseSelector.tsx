import React, { useEffect, useState } from 'react';
import { DatabaseConfig, DatabaseType } from '../types';
import { discoveryApi } from '../services/api';
import WizardHeader from './ui/WizardHeader';
import {
  IconDatabase,
  IconShieldCheck,
  IconArrowRight,
  IconCheck,
  IconChevronRight,
  IconX,
} from './ui/Icons';
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
    db_type: DatabaseType.ORACLE_XE_21C_SOURCE,
    host: 'localhost',
    port: 1521,
    service_name: 'XEPDB1',
    username: 'migration_user',
    password: 'MigrationPwd123',
    description: 'Oracle 18c XE – Source DB (16 500 rows)',
  },
  {
    db_id: 'target_oracle',
    db_type: DatabaseType.ORACLE_XE_21C_TARGET,
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
  const [editing, setEditing] = useState<'source' | 'target' | null>(null);

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

  const tested = Object.keys(connectionStatus).length > 0;
  const allOk = tested && databases.every((db) => connectionStatus[db.db_id] === 'ok');

  /** Endpoint card for one side of the migration. */
  const renderEndpoint = (
    role: 'source' | 'target',
    label: string,
    selectedId: string,
    setSelectedId: (id: string) => void
  ) => {
    const db = databases.find((d) => d.db_id === selectedId);
    const state = db ? connectionStatus[db.db_id] : undefined;

    return (
      <div className="endpoint">
        <div className="endpoint-head">
          <span className="tile tile-md tile-blue">
            <IconDatabase size={18} />
          </span>
          <div className="endpoint-id">
            <span className="eyebrow">{label}</span>
            <div className="endpoint-name">{db?.description || db?.db_id || '—'}</div>
          </div>

          {state === 'ok' && (
            <span className="conn-state ok">
              <span className="dot dot-green" />
              Verified
            </span>
          )}
          {state === 'fail' && (
            <span className="conn-state fail">
              <IconX size={13} />
              Failed
            </span>
          )}
        </div>

        <div className="endpoint-fields">
          <div className="field">
            <label className="field-label">Host &amp; service</label>
            <div className="field-box mono">
              {db ? `${db.host}:${db.port}/${db.service_name}` : '—'}
            </div>
          </div>
          <div className="field">
            <label className="field-label">Schema</label>
            <div className="field-box">{(db?.username || '').toUpperCase() || '—'}</div>
          </div>
        </div>

        {editing === role ? (
          <div className="endpoint-edit">
            <select
              className="db-select"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Select database...</option>
              {databases.map((d) => (
                <option key={d.db_id} value={d.db_id}>
                  {d.description || d.db_id}
                </option>
              ))}
            </select>
            <button type="button" className="btn-link" onClick={() => setEditing(null)}>
              Done
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="btn-link endpoint-edit-link"
            onClick={() => setEditing(role)}
          >
            Edit connection
            <IconChevronRight size={14} />
          </button>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <>
        <WizardHeader
          step={1}
          title="Configure your migration"
          subtitle="Connect source and target environments. No data moves until you review and approve the generated plan."
        />
        <div className="card">
          <div className="loading-block">
            <div className="spinner" />
            <p>Loading available databases...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <WizardHeader
        step={1}
        title="Configure your migration"
        subtitle="Connect source and target environments. No data moves until you review and approve the generated plan."
      />

      <div className="card">
        <div className="card-head bordered">
          <div>
            <h2 className="card-title">Database endpoints</h2>
            <p className="card-subtitle">
              Confirm the connection details for both environments.
            </p>
          </div>

          <button
            type="button"
            className={`pill ${allOk ? 'pill-green' : 'pill-grey'} verify-pill`}
            onClick={testConnections}
            disabled={testing}
          >
            {allOk ? <IconCheck size={14} /> : <IconShieldCheck size={14} />}
            {testing ? 'Verifying…' : allOk ? 'Connections verified' : 'Verify connections'}
          </button>
        </div>

        <div className="card-body">
          <div className="endpoint-row">
            {renderEndpoint('source', 'Source database', selectedSource, setSelectedSource)}

            <div className="transfer">
              <span className="transfer-label">Secure transfer</span>
              <IconArrowRight size={18} />
            </div>

            {renderEndpoint('target', 'Target database', selectedTarget, setSelectedTarget)}
          </div>

          <div className="info-strip endpoint-note">
            <IconShieldCheck size={18} />
            <div>
              <div className="t">Your data remains protected</div>
              <div className="s">
                Credentials are encrypted. This step only validates access and reads
                metadata—no records are copied or changed.
              </div>
            </div>
          </div>
        </div>

        <div className="card-foot">
          <div className="foot-text">
            <div className="t">Ready to discover your source?</div>
            <div className="s">
              The agent will inventory schemas, tables, dependencies, and configuration.
            </div>
          </div>
          <button
            type="button"
            className="btn btn-primary btn-lg"
            onClick={handleContinue}
            disabled={!canContinue}
          >
            Discover database
            <IconArrowRight size={16} />
          </button>
        </div>
      </div>
    </>
  );
};

export default DatabaseSelector;
