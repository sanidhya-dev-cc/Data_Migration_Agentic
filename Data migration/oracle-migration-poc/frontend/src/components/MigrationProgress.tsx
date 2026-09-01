import React from 'react';
import { MigrationResponse, MigrationStatus } from '../types';
import './MigrationProgress.css';

interface MigrationProgressProps {
  migrationData: MigrationResponse | null;
  onCancel: () => void;
}

const MigrationProgress: React.FC<MigrationProgressProps> = ({
  migrationData,
  onCancel,
}) => {
  if (!migrationData || !migrationData.progress) {
    return null;
  }

  const { progress, status } = migrationData;

  const getStatusColor = (status: MigrationStatus): string => {
    switch (status) {
      case MigrationStatus.COMPLETED:
        return '#10b981';
      case MigrationStatus.FAILED:
      case MigrationStatus.CANCELLED:
        return '#ef4444';
      case MigrationStatus.AWAITING_APPROVAL:
        return '#f59e0b';
      case MigrationStatus.EXECUTING:
      case MigrationStatus.VALIDATING:
        return '#3b82f6';
      default:
        return '#6b7280';
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

  return (
    <div className="card migration-progress-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Migration Progress</h2>
          <p className="card-subtitle">Migration ID: {migrationData.migration_id}</p>
        </div>
        {canCancel && (
          <button className="btn btn-danger" onClick={onCancel}>
            Cancel Migration
          </button>
        )}
      </div>

      <div className="progress-container">
        {/* Status Badge */}
        <div className="status-section">
          <div
            className="status-badge-lg"
            style={{ background: getStatusColor(status) }}
          >
            {getStatusLabel(status)}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{
              width: `${progress.progress_percentage}%`,
              background: getStatusColor(status),
            }}
          >
            <span className="progress-text">{progress.progress_percentage}%</span>
          </div>
        </div>

        {/* Statistics */}
        <div className="progress-stats">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Tables</div>
              <div className="stat-value">
                {progress.tables_completed} / {progress.tables_total}
              </div>
            </div>
          </div>

          {progress.current_table && (
            <div className="stat-card">
              <div className="stat-icon">🔄</div>
              <div className="stat-content">
                <div className="stat-label">Current Table</div>
                <div className="stat-value">{progress.current_table}</div>
              </div>
            </div>
          )}

          {progress.started_at && (
            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-label">Started At</div>
                <div className="stat-value">
                  {new Date(progress.started_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          )}

          {progress.completed_at && (
            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-content">
                <div className="stat-label">Completed At</div>
                <div className="stat-value">
                  {new Date(progress.completed_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {progress.error_message && (
          <div className="error-message">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
              <div className="error-title">Error Occurred</div>
              <div className="error-text">{progress.error_message}</div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {status === MigrationStatus.COMPLETED && (
          <div className="success-message">
            <div className="success-icon">🎉</div>
            <div className="success-content">
              <div className="success-title">Migration Completed!</div>
              <div className="success-text">
                All tables have been successfully migrated and validated.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MigrationProgress;
