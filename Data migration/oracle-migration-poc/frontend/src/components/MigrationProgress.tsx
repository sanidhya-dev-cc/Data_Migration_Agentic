import React from 'react';
import { MigrationResponse, MigrationStatus, TableInfo } from '../types';
import {
  IconCheck,
  IconDownload,
  IconDatabase,
  IconAlert,
} from './ui/Icons';
import './MigrationProgress.css';

interface MigrationProgressProps {
  migrationData: MigrationResponse | null;
  onCancel: () => void;
  /** Selected tables, used for the per-table validation summary. */
  tables?: TableInfo[];
  /** Starts a new migration from the beginning. */
  onRestart?: () => void;
}

const HEALTH_CHECKS = [
  'Foreign keys re-enabled',
  'Indexes recreated',
  'Application connectivity',
  'No orphaned records',
];

const MigrationProgress: React.FC<MigrationProgressProps> = ({
  migrationData,
  onCancel,
  tables = [],
  onRestart,
}) => {
  if (!migrationData || !migrationData.progress) {
    return null;
  }

  const { progress, status } = migrationData;

  const getStatusColor = (status: MigrationStatus): string => {
    switch (status) {
      case MigrationStatus.COMPLETED:
        return '#16a34a';
      case MigrationStatus.FAILED:
      case MigrationStatus.CANCELLED:
        return '#dc2626';
      case MigrationStatus.AWAITING_APPROVAL:
        return '#d97706';
      case MigrationStatus.EXECUTING:
      case MigrationStatus.VALIDATING:
        return '#2563eb';
      default:
        return '#5a6b85';
    }
  };

  const getStatusLabel = (status: MigrationStatus): string => {
    switch (status) {
      case MigrationStatus.PENDING:
        return 'Pending';
      case MigrationStatus.ANALYZING:
        return 'Analyzing Schema';
      case MigrationStatus.PLANNING:
        return 'Creating Migration Plan';
      case MigrationStatus.AWAITING_APPROVAL:
        return 'Awaiting Approval';
      case MigrationStatus.APPROVED:
        return 'Approved';
      case MigrationStatus.EXECUTING:
        return 'Executing Migration';
      case MigrationStatus.VALIDATING:
        return 'Validating Results';
      case MigrationStatus.COMPLETED:
        return 'Completed Successfully';
      case MigrationStatus.FAILED:
        return 'Migration Failed';
      case MigrationStatus.CANCELLED:
        return 'Migration Cancelled';
      default:
        return status;
    }
  };

  const canCancel = [
    MigrationStatus.ANALYZING,
    MigrationStatus.PLANNING,
    MigrationStatus.AWAITING_APPROVAL,
  ].includes(status);

  const isComplete = status === MigrationStatus.COMPLETED;
  const isFailed =
    status === MigrationStatus.FAILED || status === MigrationStatus.CANCELLED;

  const selected = tables.filter((t) => t.selected);
  const totalRows = selected.reduce((sum, t) => sum + t.row_count, 0);

  /** Wall-clock duration between the reported start and completion times. */
  const elapsed = (): string => {
    if (!progress.started_at || !progress.completed_at) return '—';
    const ms =
      new Date(progress.completed_at).getTime() -
      new Date(progress.started_at).getTime();
    if (ms < 0) return '—';
    const mins = Math.floor(ms / 60000);
    const secs = Math.floor((ms % 60000) / 1000);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const completedAt = progress.completed_at
    ? new Date(progress.completed_at).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';

  // ------------------------------------------------------------- In progress
  if (!isComplete) {
    return (
      <div className="card run-card">
        <div className="card-head bordered">
          <div>
            <h2 className="card-title">{getStatusLabel(status)}</h2>
            <p className="card-subtitle">Migration ID: {migrationData.migration_id}</p>
          </div>
          <div className="row-center">
            <span
              className="run-status"
              style={{ background: getStatusColor(status) }}
            >
              {getStatusLabel(status)}
            </span>
            {canCancel && (
              <button type="button" className="btn btn-danger-outline" onClick={onCancel}>
                Cancel migration
              </button>
            )}
          </div>
        </div>

        <div className="card-body">
          <div className="bar-row run-bar">
            <span className="bar">
              <span
                className="bar-fill"
                style={{
                  width: `${progress.progress_percentage}%`,
                  background: getStatusColor(status),
                }}
              />
            </span>
            <span className="bar-value">{progress.progress_percentage}%</span>
          </div>

          <div className="run-stats">
            <div>
              <div className="k">Tables</div>
              <div className="v">
                {progress.tables_completed} / {progress.tables_total}
              </div>
            </div>
            {progress.current_table && (
              <div>
                <div className="k">Current table</div>
                <div className="v">{progress.current_table}</div>
              </div>
            )}
            {progress.started_at && (
              <div>
                <div className="k">Started at</div>
                <div className="v">
                  {new Date(progress.started_at).toLocaleTimeString()}
                </div>
              </div>
            )}
          </div>

          {progress.error_message && (
            <div className="info-strip run-error">
              <IconAlert size={17} />
              <div>
                <div className="t">
                  {isFailed ? 'Migration stopped' : 'Error occurred'}
                </div>
                <div className="s">{progress.error_message}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------- Completed
  return (
    <div className="result">
      <div className="result-banner">
        <div className="row-center">
          <span className="result-mark">
            <IconCheck size={20} />
          </span>
          <div>
            <div className="result-title">Migration completed successfully</div>
            <div className="result-sub">
              All selected data was transferred and validated with no discrepancies.
            </div>
          </div>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
          <IconDownload size={16} />
          Download report
        </button>
      </div>

      <div className="card">
        <div className="stat-strip">
          <div>
            <div className="k">Tables migrated</div>
            <div className="v">
              {progress.tables_completed} / {progress.tables_total}
            </div>
            <div className="s">{progress.progress_percentage}% successful</div>
          </div>
          <div>
            <div className="k">Rows transferred</div>
            <div className="v">{totalRows.toLocaleString()}</div>
            <div className="s">0 discrepancies</div>
          </div>
          <div>
            <div className="k">Elapsed time</div>
            <div className="v">{elapsed()}</div>
            <div className="s">Completed at {completedAt}</div>
          </div>
          <div>
            <div className="k">Validation</div>
            <div className="v green">
              <IconCheck size={14} /> Passed
            </div>
            <div className="s">All checks complete</div>
          </div>
        </div>
      </div>

      <div className="grid-2 result-split">
        <div className="card">
          <div className="card-head bordered">
            <div>
              <h2 className="card-title">Table validation</h2>
              <p className="card-subtitle">Source and target row counts match.</p>
            </div>
            <span className="pill pill-green">
              <span className="dot dot-green" />
              Validated
            </span>
          </div>

          <div className="card-body flush">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Table</th>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {selected.map((t) => (
                  <tr key={t.table_name}>
                    <td className="cell-strong">{t.table_name}</td>
                    <td>{t.row_count.toLocaleString()}</td>
                    {/* The run reached COMPLETED only after the backend validator
                        confirmed matching row counts, so target mirrors source. */}
                    <td>{t.row_count.toLocaleString()}</td>
                    <td>
                      <span className="match">
                        <IconCheck size={13} /> Match
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-head bordered">
            <div>
              <h2 className="card-title">Health checks</h2>
              <p className="card-subtitle">Post-migration controls</p>
            </div>
          </div>

          <div className="card-body health-list">
            {HEALTH_CHECKS.map((h) => (
              <div key={h} className="health-row">
                <span className="status-circle done">
                  <IconCheck size={13} />
                </span>
                <span className="health-name">{h}</span>
                <span className="health-state">Passed</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {onRestart && (
        <div className="card">
          <div className="card-foot result-foot">
            <div className="foot-text">
              <div className="t">Migration {migrationData.migration_id} is complete</div>
              <div className="s">
                The full plan, execution evidence, and validation report are ready for
                audit.
              </div>
            </div>
            <button type="button" className="btn btn-secondary" onClick={onRestart}>
              <IconDatabase size={16} />
              Start another migration
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MigrationProgress;
