import React, { useState } from 'react';
import { MigrationPlan, MigrationStatus } from '../types';
import './MigrationPlanView.css';

interface MigrationPlanViewProps {
  plan: MigrationPlan;
  status: MigrationStatus;
  onApprove: (approved: boolean, comments?: string) => void;
}

const MigrationPlanView: React.FC<MigrationPlanViewProps> = ({
  plan,
  status,
  onApprove,
}) => {
  const [comments, setComments] = useState('');
  const [showComments, setShowComments] = useState(false);

  const handleApprove = () => {
    onApprove(true, comments || undefined);
  };

  const handleReject = () => {
    if (!comments.trim()) {
      alert('Please provide comments for rejection');
      return;
    }
    onApprove(false, comments);
  };

  const isAwaitingApproval = status === MigrationStatus.AWAITING_APPROVAL;

  return (
    <div className="card migration-plan-card">
      <div className="card-header">
        <div>
          <h2 className="card-title">AI-Generated Migration Plan</h2>
          <p className="card-subtitle">
            Review the proposed two-step migration strategy
          </p>
        </div>
        {isAwaitingApproval && (
          <div className="approval-badge">Awaiting Your Approval</div>
        )}
      </div>

      <div className="plan-content">
        {/* AI Reasoning */}
        <div className="plan-section">
          <h3 className="section-title">🤖 AI Reasoning</h3>
          <div className="reasoning-box">
            <pre className="reasoning-text">{plan.ai_reasoning}</pre>
          </div>
        </div>

        {/* Migration Steps */}
        <div className="steps-grid">
          {plan.step_1 && (
            <div className="step-card step1">
              <div className="step-header">
                <div className="step-badge">Step 1</div>
                <h3>Non-CDB to 19c PDB</h3>
              </div>
              <div className="step-details">
                <div className="detail-row">
                  <span className="detail-label">Estimated Duration:</span>
                  <span className="detail-value">
                    {plan.step_1.estimated_duration_minutes} minutes
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Risk Level:</span>
                  <span className={`risk-badge ${plan.step_1.risk_level}`}>
                    {plan.step_1.risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Execution Order:</span>
                  <div className="execution-order">
                    {plan.step_1.execution_order.map((table, idx) => (
                      <span key={idx} className="table-badge">
                        {idx + 1}. {table}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {plan.step_2 && (
            <div className="step-card step2">
              <div className="step-header">
                <div className="step-badge">Step 2</div>
                <h3>19c PDB to 23c PDB</h3>
              </div>
              <div className="step-details">
                <div className="detail-row">
                  <span className="detail-label">Estimated Duration:</span>
                  <span className="detail-value">
                    {plan.step_2.estimated_duration_minutes} minutes
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Risk Level:</span>
                  <span className={`risk-badge ${plan.step_2.risk_level}`}>
                    {plan.step_2.risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Execution Order:</span>
                  <div className="execution-order">
                    {plan.step_2.execution_order.map((table, idx) => (
                      <span key={idx} className="table-badge">
                        {idx + 1}. {table}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Risk Assessment */}
        {plan.risk_assessment && (
          <div className="plan-section">
            <h3 className="section-title">⚠️ Risk Assessment</h3>
            <div className="info-box">{plan.risk_assessment}</div>
          </div>
        )}

        {/* Pre-checks */}
        {plan.pre_checks && plan.pre_checks.length > 0 && (
          <div className="plan-section">
            <h3 className="section-title">✓ Pre-Migration Checks</h3>
            <ul className="check-list">
              {plan.pre_checks.map((check, idx) => (
                <li key={idx} className="check-item">
                  <span className="check-icon">✓</span>
                  {check}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Post-checks */}
        {plan.post_checks && plan.post_checks.length > 0 && (
          <div className="plan-section">
            <h3 className="section-title">✓ Post-Migration Validations</h3>
            <ul className="check-list">
              {plan.post_checks.map((check, idx) => (
                <li key={idx} className="check-item">
                  <span className="check-icon">✓</span>
                  {check}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Rollback Strategy */}
        {plan.rollback_strategy && (
          <div className="plan-section">
            <h3 className="section-title">🔄 Rollback Strategy</h3>
            <div className="info-box warning">{plan.rollback_strategy}</div>
          </div>
        )}

        {/* Dependencies */}
        {plan.dependencies && plan.dependencies.length > 0 && (
          <div className="plan-section">
            <h3 className="section-title">🔗 Dependencies</h3>
            <div className="dependencies-list">
              {plan.dependencies.map((dep, idx) => (
                <div key={idx} className="dependency-item">
                  <div className="dep-table">{dep.table_name}</div>
                  <div className="dep-arrow">→</div>
                  <div className="dep-depends">
                    {dep.depends_on.join(', ')}
                    <span className={`dep-risk ${dep.risk_level}`}>
                      {dep.risk_level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Approval Section */}
        {isAwaitingApproval && (
          <div className="approval-section">
            <div className="approval-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowComments(!showComments)}
              >
                Add Comments
              </button>
            </div>

            {showComments && (
              <textarea
                className="comments-input"
                placeholder="Enter your comments or concerns..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={4}
              />
            )}

            <div className="approval-buttons">
              <button className="btn btn-success btn-lg" onClick={handleApprove}>
                ✓ Approve and Execute Migration
              </button>
              <button className="btn btn-danger btn-lg" onClick={handleReject}>
                ✗ Reject Migration Plan
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MigrationPlanView;
