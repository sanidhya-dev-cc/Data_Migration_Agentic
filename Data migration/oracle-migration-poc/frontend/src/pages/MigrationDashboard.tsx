import React, { useEffect, useState } from 'react';
import {
  DatabaseConfig,
  DependencyInfo,
  MigrationResponse,
  MigrationStatus,
  TableInfo,
} from '../types';
import { migrationApi, schemaApi } from '../services/api';
import TableSelector from '../components/TableSelector';
import MigrationProgress from '../components/MigrationProgress';
import MigrationPlanView from '../components/MigrationPlanView';
import AgentLogs from '../components/AgentLogs';
import WizardHeader from '../components/ui/WizardHeader';
import { IconArrowRight, IconAlert } from '../components/ui/Icons';
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
  const [dependencies, setDependencies] = useState<DependencyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [migrationStarted, setMigrationStarted] = useState(false);
  const [migrationData, setMigrationData] = useState<MigrationResponse | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (databases.source) {
      loadTables();
    }
    // Reloads only when the selected source database changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setLoadError(null);
      const schema = await schemaApi.getSourceSchema(databases.source!.db_id);
      setTables(schema.tables);
      setDependencies(schema.dependencies || []);
    } catch (error: any) {
      console.error('Failed to load tables:', error);
      setLoadError(error?.response?.data?.detail || error?.message || 'Unknown error');
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

  // ------------------------------------------------------------ Wizard state
  const status = migrationData?.status;
  const isPlanning =
    status === MigrationStatus.PENDING ||
    status === MigrationStatus.ANALYZING ||
    status === MigrationStatus.PLANNING ||
    status === MigrationStatus.AWAITING_APPROVAL;

  const step = !migrationStarted ? 2 : isPlanning ? 3 : 4;
  const isComplete = status === MigrationStatus.COMPLETED;

  const headings: Record<number, { title: string; subtitle: string }> = {
    2: {
      title: 'Review discovered objects',
      subtitle:
        'Choose the database objects to include. Dependencies are automatically sequenced in the migration plan.',
    },
    3: {
      title: 'Review the migration plan',
      subtitle:
        "Review the agent's execution order, risk controls, and validation strategy before granting approval.",
    },
    4: {
      title: isComplete ? 'Migration completed' : 'Migrating your data',
      subtitle: isComplete
        ? 'All selected tables were migrated successfully and independently validated against the source.'
        : 'The agent is transferring your selected tables and validating them against the source.',
    },
  };

  const selectedCount = tables.filter((t) => t.selected).length;
  const selectedRows = tables
    .filter((t) => t.selected)
    .reduce((sum, t) => sum + t.row_count, 0);

  return (
    <div className="migration-dashboard">
      <WizardHeader
        step={step}
        title={headings[step].title}
        subtitle={headings[step].subtitle}
      />

      {!migrationStarted ? (
        <>
          {loading ? (
            <div className="card">
              <div className="loading-block">
                <div className="spinner" />
                <p>Loading schema information...</p>
              </div>
            </div>
          ) : loadError ? (
            <div className="card">
              <div className="loading-block">
                <span className="tile tile-lg tile-grey">
                  <IconAlert size={20} />
                </span>
                <p>Failed to load source tables: {loadError}</p>
                <button type="button" className="btn btn-secondary" onClick={loadTables}>
                  Retry
                </button>
              </div>
            </div>
          ) : (
            <TableSelector
              tables={tables}
              onTablesChange={setTables}
              dependencies={dependencies}
            />
          )}

          <div className="card discover-foot">
            <div className="card-foot">
              <button type="button" className="btn btn-secondary" onClick={onBack}>
                Back to configuration
              </button>

              <div className="discover-next">
                <div className="foot-text text-right">
                  <div className="t">
                    {selectedCount} tables · {selectedRows.toLocaleString()} rows
                  </div>
                  <div className="s">
                    Next, the agent will generate a dependency-aware plan for your
                    approval.
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-lg"
                  onClick={handleStartMigration}
                  disabled={selectedCount === 0}
                >
                  Generate migration plan
                  <IconArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Plan review and approval gate */}
          {migrationData?.plan && isPlanning && (
            <MigrationPlanView
              plan={migrationData.plan}
              status={migrationData.status}
              onApprove={handleApproveMigration}
              tables={tables}
              onBackToDiscovery={() => setMigrationStarted(false)}
            />
          )}

          {/* Execution progress and final result */}
          {!isPlanning && (
            <MigrationProgress
              migrationData={migrationData}
              onCancel={handleCancelMigration}
              tables={tables}
              onRestart={onBack}
            />
          )}

          {/* Status card while the plan is still being produced */}
          {isPlanning && !migrationData?.plan && (
            <MigrationProgress
              migrationData={migrationData}
              onCancel={handleCancelMigration}
              tables={tables}
            />
          )}

          {/* Agent reasoning and audit trail */}
          {migrationData?.progress && (
            <AgentLogs logs={migrationData.progress.agent_logs} />
          )}
        </>
      )}
    </div>
  );
};

export default MigrationDashboard;
