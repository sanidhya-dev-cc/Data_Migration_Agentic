import React, { useEffect, useState } from 'react';
import {
  DatabaseConfig,
  MigrationResponse,
  MigrationStatus,
  TableInfo,
} from '../types';
import { migrationApi, schemaApi } from '../services/api';
import TableSelector from '../components/TableSelector';
import MigrationProgress from '../components/MigrationProgress';
import MigrationPlanView from '../components/MigrationPlanView';
import AgentLogs from '../components/AgentLogs';
import './MigrationDashboard.css';

interface MigrationDashboardProps {
  databases: {
    source?: DatabaseConfig;
    intermediate?: DatabaseConfig;
    target?: DatabaseConfig;
  };
  onBack: () => void;
}

const MigrationDashboard: React.FC<MigrationDashboardProps> = ({
  databases,
  onBack,
}) => {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [migrationStarted, setMigrationStarted] = useState(false);
  const [migrationData, setMigrationData] = useState<MigrationResponse | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (databases.source) {
      loadTables();
    }
  }, [databases.source]);

  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const loadTables = async () => {
    try {
      setLoading(true);
      const schema = await schemaApi.getSourceSchema(databases.source!.db_id);
      setTables(schema.tables);
    } catch (error) {
      console.error('Failed to load tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartMigration = async () => {
    if (!databases.source || !databases.target) {
      alert('Please select source and target databases');
      return;
    }

    const selectedTables = tables.filter((t) => t.selected);
    if (selectedTables.length === 0) {
      alert('Please select at least one table to migrate');
      return;
    }

    // Ensure DB configs include credentials (enriched from DatabaseSelector)
    const sourceDb = {
      ...databases.source,
      username: databases.source.username || 'migration_user',
      password: databases.source.password || 'MigrationPwd123',
    };
    const targetDb = {
      ...databases.target,
      username: databases.target.username || 'migration_user',
      password: databases.target.password || 'MigrationPwd123',
    };

    try {
      const response = await migrationApi.startMigration({
        migration_name: `Migration ${new Date().toLocaleString()}`,
        source_db: sourceDb,
        target_db: targetDb,
        tables: selectedTables,
        migration_mode: 'direct',
        business_priority: 'medium',
        max_downtime_minutes: 60,
        user_notes: 'POC Migration via Oracle Docker containers',
      });

      setMigrationData(response);
      setMigrationStarted(true);

      // Start polling for status updates
      const interval = setInterval(async () => {
        try {
          const status = await migrationApi.getMigrationStatus(response.migration_id);
          setMigrationData(status);

          // Stop polling if migration is complete or failed
          if (
            status.status === MigrationStatus.COMPLETED ||
            status.status === MigrationStatus.FAILED ||
            status.status === MigrationStatus.CANCELLED
          ) {
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Failed to get migration status:', error);
        }
      }, 3000); // Poll every 3 seconds

      setPollingInterval(interval);
    } catch (error) {
      console.error('Failed to start migration:', error);
      alert('Failed to start migration. Please try again.');
    }
  };

  const handleApproveMigration = async (approved: boolean, comments?: string) => {
    if (!migrationData) return;

    try {
      const response = await migrationApi.approveMigration(
        migrationData.migration_id,
        approved,
        comments,
        'user'
      );
      setMigrationData(response);
    } catch (error) {
      console.error('Failed to approve migration:', error);
      alert('Failed to submit approval. Please try again.');
    }
  };

  const handleCancelMigration = async () => {
    if (!migrationData) return;

    if (
      !window.confirm(
        'Are you sure you want to cancel this migration? This action cannot be undone.'
      )
    ) {
      return;
    }

    try {
      await migrationApi.cancelMigration(migrationData.migration_id);
      const status = await migrationApi.getMigrationStatus(migrationData.migration_id);
      setMigrationData(status);
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    } catch (error) {
      console.error('Failed to cancel migration:', error);
      alert('Failed to cancel migration. Please try again.');
    }
  };

  return (
    <div className="migration-dashboard">
      {/* Database Overview */}
      <div className="card db-overview">
        <div className="card-header">
          <div>
            <h2 className="card-title">Database Configuration</h2>
            <p className="card-subtitle">Two-step migration path overview</p>
          </div>
          <button className="btn btn-secondary" onClick={onBack}>
            ← Back to Selection
          </button>
        </div>
        <div className="db-flow">
          <div className="db-card source">
            <div className="db-label">Source</div>
            <div className="db-name">{databases.source?.db_id}</div>
            <div className="db-type">{databases.source?.host}:{databases.source?.port}</div>
          </div>
          <div className="flow-arrow-lg">→</div>
          <div className="db-card target">
            <div className="db-label">Target</div>
            <div className="db-name">{databases.target?.db_id}</div>
            <div className="db-type">{databases.target?.host}:{databases.target?.port}</div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {!migrationStarted ? (
        <>
          {/* Table Selection */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Select Tables to Migrate</h2>
                <p className="card-subtitle">
                  Choose which tables to include in the migration
                </p>
              </div>
            </div>
            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading schema information...</p>
              </div>
            ) : (
              <TableSelector tables={tables} onTablesChange={setTables} />
            )}
          </div>

          {/* Start Migration Button */}
          <div className="card">
            <div className="migration-start">
              <div className="start-info">
                <h3>Ready to Start Migration?</h3>
                <p>
                  The AI agent will analyze your schema, generate a migration plan, and
                  present it for your approval before execution.
                </p>
                <div className="migration-summary">
                  <div className="summary-item">
                    <span className="summary-label">Selected Tables:</span>
                    <span className="summary-value">
                      {tables.filter((t) => t.selected).length} / {tables.length}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Total Size:</span>
                    <span className="summary-value">
                      {tables
                        .filter((t) => t.selected)
                        .reduce((sum, t) => sum + t.size_mb, 0)
                        .toFixed(2)}{' '}
                      MB
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Total Rows:</span>
                    <span className="summary-value">
                      {tables
                        .filter((t) => t.selected)
                        .reduce((sum, t) => sum + t.row_count, 0)
                        .toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
              <button
                className="btn btn-primary btn-lg"
                onClick={handleStartMigration}
                disabled={tables.filter((t) => t.selected).length === 0}
              >
                Start AI-Powered Migration →
              </button>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Migration Progress */}
          <MigrationProgress
            migrationData={migrationData}
            onCancel={handleCancelMigration}
          />

          {/* Migration Plan (if available) */}
          {migrationData?.plan && (
            <MigrationPlanView
              plan={migrationData.plan}
              status={migrationData.status}
              onApprove={handleApproveMigration}
            />
          )}

          {/* Agent Logs */}
          {migrationData?.progress && (
            <AgentLogs logs={migrationData.progress.agent_logs} />
          )}
        </>
      )}
    </div>
  );
};

export default MigrationDashboard;
