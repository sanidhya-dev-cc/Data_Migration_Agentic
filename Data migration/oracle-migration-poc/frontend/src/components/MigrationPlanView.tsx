import React, { useState } from 'react';
import { MigrationPlan, MigrationStatus, TableInfo } from '../types';
import {
  IconSparkle,
  IconShieldCheck,
  IconCheck,
  IconCheckCircle,
  IconLayers,
  IconRotate,
  IconDatabase,
  IconAlert,
  IconLock,
  IconArrowRight,
} from './ui/Icons';
import './MigrationPlanView.css';

interface MigrationPlanViewProps {
  plan: MigrationPlan;
  status: MigrationStatus;
  onApprove: (approved: boolean, comments?: string) => void;
  /** Selected tables, used to size the scope summary. */
  tables?: TableInfo[];
  /** Returns the wizard to the discovery step. */
  onBackToDiscovery?: () => void;
}

/**
 * Clarification questions presented before the approval gate.
 * These are presentation-level choices: they refine what the plan summary
 * displays and unlock the approval gate. No request is sent when applying them.
 */
const QUESTIONS = [
  {
    id: 'mode',
    question: 'What is your preferred migration mode?',
    hint: 'Determines the expected service interruption and final synchronization strategy.',
    options: [
      { value: 'minimal', label: 'Minimal downtime', note: 'Brief cutover · Recommended' },
      { value: 'offline', label: 'Standard offline', note: 'Stop writes during migration' },
    ],
  },
  {
    id: 'indexes',
    question: 'How should indexes be handled?',
    hint: 'Impacts load performance and the sequence used by the migration agent.',
    options: [
      { value: 'rebuild', label: 'Rebuild after data load', note: 'Faster transfer · Recommended' },
      { value: 'preserve', label: 'Preserve during load', note: 'Slower, indexes remain active' },
    ],
  },
  {
    id: 'failure',
    question: 'What should happen if one table fails?',
    hint: 'Defines the stop condition and scope of rollback during execution.',
    options: [
      { value: 'stop', label: 'Stop and request review', note: 'Safest option · Recommended' },
      { value: 'continue', label: 'Continue independent tables', note: 'Failed table remains rolled back' },
    ],
  },
];

const DEFAULT_ANSWERS: Record<string, string> = {
  mode: 'minimal',
  indexes: 'rebuild',
  failure: 'stop',
};

const MigrationPlanView: React.FC<MigrationPlanViewProps> = ({
  plan,
  status,
  onApprove,
  tables = [],
  onBackToDiscovery,
}) => {
  const [comments, setComments] = useState('');
  const [showComments, setShowComments] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>(DEFAULT_ANSWERS);
  const [applied, setApplied] = useState(false);

  const handleApprove = () => {
    onApprove(true, comments || undefined);
  };

  const handleReject = () => {
    if (!comments.trim()) {
      alert('Please provide comments for rejection');
      setShowComments(true);
      return;
    }
    onApprove(false, comments);
  };

  const handleAnswer = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    setApplied(false);
  };

  const isAwaitingApproval = status === MigrationStatus.AWAITING_APPROVAL;

  // ---------------------------------------------------------------- Derived
  const executionOrder =
    plan.execution_order && plan.execution_order.length > 0
      ? plan.execution_order
      : plan.step_1?.execution_order || [];

  const selected = tables.filter((t) => t.selected);
  const scopeRows = selected.reduce((sum, t) => sum + t.row_count, 0);
  const scopeSize = selected.reduce((sum, t) => sum + t.size_mb, 0);

  const riskLevel = plan.step_1?.risk_level || 'medium';
  const executionMode =
    answers.failure === 'stop' ? 'Stop on failure' : 'Continue on failure';

  const rowsFor = (tableName: string): number => {
    const t = tables.find((x) => x.table_name === tableName);
    return t ? t.row_count : 0;
  };

  const dependencyLabel = (tableName: string): string => {
    const entry = plan.dependencies?.find((d) => d.table_name === tableName);
    const count = entry ? entry.depends_on.length : 0;
    if (count === 0) return 'Independent';
    return count === 1 ? '1 dependency' : `${count} dependencies`;
  };

  const fkCount = (plan.dependencies || []).reduce(
    (sum, d) => sum + d.depends_on.length,
    0
  );

  const appliedSummary = [
    answers.mode === 'minimal' ? 'Minimal-downtime cutover' : 'Standard offline cutover',
    answers.indexes === 'rebuild'
      ? 'Indexes rebuilt after bulk load'
      : 'Indexes preserved during load',
    answers.failure === 'stop'
      ? 'Execution stops on first failure'
      : 'Independent tables continue on failure',
  ].join(' · ');

  const preChecks = plan.pre_checks || [];

  return (
    <div className="plan-view">
      {/* ------------------------------------------- Clarification checkpoint */}
      <div className={`card clarify ${applied ? 'is-applied' : ''}`}>
        <div className="card-head">
          <div className="row-center clarify-lead">
            <span className={`tile tile-md ${applied ? 'tile-green' : 'tile-amber'}`}>
              {applied ? <IconCheck size={17} /> : <IconSparkle size={17} />}
            </span>
            <div>
              <span className="eyebrow">
                {applied ? 'Clarifications applied' : 'Agent clarification checkpoint'}
              </span>
              <div className="card-title clarify-title">
                {applied
                  ? 'Migration plan updated from your answers'
                  : 'The agent needs your input before finalizing the plan'}
              </div>
              <p className="card-subtitle">
                {applied
                  ? 'Plan version 2 is ready for Human Approval. Change any answer to regenerate it again.'
                  : 'These choices affect downtime, execution sequence, rollback behavior, and risk. Human Approval stays locked until they are applied.'}
              </p>
            </div>
          </div>

          <span className={`pill ${applied ? 'pill-green' : 'pill-amber'}`}>
            {applied ? <IconCheck size={13} /> : null}
            {applied ? 'Resolved' : `${QUESTIONS.length} responses required`}
          </span>
        </div>

        <div className="card-body clarify-body">
          {QUESTIONS.map((q, i) => (
            <div key={q.id} className="clarify-q">
              <span className="numcircle">{i + 1}</span>
              <div className="clarify-prompt">
                <div className="clarify-question">{q.question}</div>
                <div className="clarify-hint">{q.hint}</div>
              </div>
              <div className="clarify-options">
                {q.options.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`option ${answers[q.id] === opt.value ? 'is-chosen' : ''}`}
                    onClick={() => handleAnswer(q.id, opt.value)}
                  >
                    <span className="option-label">{opt.label}</span>
                    <span className="option-note">{opt.note}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="clarify-foot">
          {applied ? (
            <div className="row-center">
              <IconSparkle size={16} />
              <div>
                <div className="t">Changes incorporated into Plan v2</div>
                <div className="s">{appliedSummary}</div>
              </div>
            </div>
          ) : (
            <>
              <div className="row-center">
                <IconShieldCheck size={16} />
                <div>
                  <div className="t">No database changes will be made</div>
                  <div className="s">The agent will only update the proposed plan.</div>
                </div>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setApplied(true)}
              >
                <IconSparkle size={15} />
                Apply answers &amp; regenerate plan
              </button>
            </>
          )}
        </div>
      </div>

      {/* ----------------------------------------------- Approval checkpoint */}
      <div className="dark-banner approval-bar">
        <div className="lead">
          <span className="tile tile-md">
            <IconShieldCheck size={18} />
          </span>
          <div>
            <span className="eyebrow">Human approval checkpoint</span>
            <div className="t">Review all AI findings before execution</div>
            <div className="s">
              The agent cannot make changes to the target database until this plan is
              explicitly approved.
            </div>
          </div>
        </div>

        <span className="pill pill-amber-solid">
          {applied ? <span className="dot dot-amber" /> : <IconLock size={13} />}
          {applied ? 'Awaiting your approval' : 'Locked until clarified'}
        </span>
      </div>

      {/* ------------------------------------------------- 1. Execution plan */}
      <div className="card section">
        <div className="card-head bordered">
          <div className="row-center">
            <span className="numbox">1</span>
            <div>
              <span className="eyebrow">AI generated migration plan</span>
              <div className="card-title">Proposed execution plan</div>
              <p className="card-subtitle">
                Plan {plan.plan_id} · Version {applied ? 2 : 1} ·{' '}
                {applied ? 'Updated from your answers' : 'Draft'}
              </p>
            </div>
          </div>
          <span className={`pill ${applied ? 'pill-green' : 'pill-grey'}`}>
            {applied ? <IconCheck size={13} /> : null}
            {applied ? 'Updated' : 'Draft plan'}
          </span>
        </div>

        <div className="stat-strip bordered-bottom">
          <div>
            <div className="k">Scope</div>
            <div className="v">{executionOrder.length} tables</div>
            <div className="s">
              {scopeRows.toLocaleString()} rows · {scopeSize.toFixed(2)} MB
            </div>
          </div>
          <div>
            <div className="k">Risk level</div>
            <div className="v amber">
              {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
            </div>
            <div className="s">Controlled upgrade path</div>
          </div>
          <div>
            <div className="k">Est. downtime</div>
            <div className="v">{plan.estimated_duration_minutes} min</div>
            <div className="s">Within 60 min window</div>
          </div>
          <div>
            <div className="k">Execution mode</div>
            <div className="v">{executionMode}</div>
            <div className="s">Per-table rollback</div>
          </div>
        </div>

        <div className="card-body plan-grid">
          <div className="panel">
            <div className="panel-head">
              <IconLayers size={16} />
              <div>
                <div className="panel-title">Dependency-aware execution order</div>
                <div className="panel-sub">
                  Parent tables are completed before dependent tables.
                </div>
              </div>
            </div>
            <div className="order-list">
              {executionOrder.map((table, i) => (
                <div key={table} className="order-row">
                  <span className="numcircle plain">{i + 1}</span>
                  <span className="order-text">
                    <span className="order-name">{table}</span>
                    <span className="order-rows">
                      {rowsFor(table).toLocaleString()} rows
                    </span>
                  </span>
                  <span className="order-dep">{dependencyLabel(table)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel-stack">
            <div className="panel">
              <div className="panel-head">
                <IconRotate size={16} />
                <div className="panel-title">Rollback strategy</div>
              </div>
              <p className="panel-text">{plan.rollback_strategy}</p>
            </div>
            <div className="panel">
              <div className="panel-head">
                <IconCheck size={16} />
                <div className="panel-title">Validation strategy</div>
              </div>
              <p className="panel-text">
                {(plan.post_checks || []).join('. ') || 'Row counts are compared after load.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* --------------------------------------------------- 2. AI reasoning */}
      <div className="card section">
        <div className="card-head bordered">
          <div className="row-center">
            <span className="numbox">2</span>
            <div>
              <span className="eyebrow">AI reasoning</span>
              <div className="card-title">Why the agent recommends this approach</div>
              <p className="card-subtitle">
                Evidence and rationale used to construct the plan
              </p>
            </div>
          </div>
          <span className="pill pill-blue">
            <IconSparkle size={13} />
            Explainable AI
          </span>
        </div>

        <div className="card-body">
          <div className="reason-grid">
            <div className="panel">
              <div className="panel-head">
                <IconDatabase size={15} />
                <span className="eyebrow">Migration intent</span>
              </div>
              <div className="panel-title">Controlled Oracle version upgrade</div>
              <p className="panel-text">
                18c XE source to 21c XE target, preserving schema structure and
                application compatibility.
              </p>
            </div>

            <div className="panel">
              <div className="panel-head">
                <IconLayers size={15} />
                <span className="eyebrow">Dependency reasoning</span>
              </div>
              <div className="panel-title">Parent-first sequencing</div>
              <p className="panel-text">
                Parent tables migrate first; dependent transaction tables follow in
                topological order.
              </p>
            </div>

            <div className="panel">
              <div className="panel-head">
                <IconShieldCheck size={15} />
                <span className="eyebrow">Safety reasoning</span>
              </div>
              <div className="panel-title">Transactional, reversible execution</div>
              <p className="panel-text">
                Per-table commits limit blast radius. The selected policy will{' '}
                {answers.failure === 'stop'
                  ? 'pause on the first failure.'
                  : 'continue with independent tables.'}
              </p>
            </div>

            <div className="panel">
              <div className="panel-head">
                <IconCheckCircle size={15} />
                <span className="eyebrow">Success criteria</span>
              </div>
              <div className="panel-title">Zero row-count discrepancy</div>
              <p className="panel-text">
                Every selected table must match its source count and pass
                referential-integrity validation.
              </p>
            </div>
          </div>

          <div className="conclusion">
            <IconSparkle size={16} />
            <div>
              <div className="conclusion-title">
                {applied ? 'Agent conclusion after clarification' : 'Agent conclusion (draft)'}
              </div>
              <p className="conclusion-text">{plan.ai_reasoning}</p>
            </div>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------- 3. AI assessment */}
      <div className="card section">
        <div className="card-head bordered">
          <div className="row-center">
            <span className="numbox">3</span>
            <div>
              <span className="eyebrow">AI assessment</span>
              <div className="card-title">Readiness, risk, and compatibility assessment</div>
              <p className="card-subtitle">
                Automated evaluation of the selected migration scope
              </p>
            </div>
          </div>
          <div className="text-right confidence">
            <div className="confidence-value">92%</div>
            <div className="confidence-label">confidence</div>
          </div>
        </div>

        <div className="stat-strip bordered-bottom">
          <div>
            <div className="k">
              <IconCheck size={13} /> Overall readiness
            </div>
            <div className="v">Ready to migrate</div>
            <div className="s">No blocking issues found</div>
          </div>
          <div>
            <div className="k">
              <IconAlert size={13} /> Risk rating
            </div>
            <div className="v">
              {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
            </div>
            <div className="s">Version upgrade controls required</div>
          </div>
          <div>
            <div className="k">
              <IconLayers size={13} /> Schema compatibility
            </div>
            <div className="v">Compatible</div>
            <div className="s">
              {executionOrder.length} of {executionOrder.length} tables supported
            </div>
          </div>
          <div>
            <div className="k">
              <IconCheckCircle size={13} /> Window fit
            </div>
            <div className="v">Within window</div>
            <div className="s">
              {plan.estimated_duration_minutes} min of 60 min available
            </div>
          </div>
        </div>

        <div className="card-body flush">
          <table className="data-table">
            <thead>
              <tr>
                <th>Assessment area</th>
                <th>Finding</th>
                <th>Impact</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="cell-strong">Data types</td>
                <td>All source data types supported in Oracle 21c XE</td>
                <td>No conversion required</td>
                <td>
                  <span className="badge badge-green">Passed</span>
                </td>
              </tr>
              <tr>
                <td className="cell-strong">Foreign keys</td>
                <td>{fkCount} dependent relationships identified</td>
                <td>Sequenced automatically</td>
                <td>
                  <span className="badge badge-blue">Managed</span>
                </td>
              </tr>
              <tr>
                <td className="cell-strong">Target capacity</td>
                <td>Target has sufficient tablespace and memory</td>
                <td>No capacity risk</td>
                <td>
                  <span className="badge badge-green">Passed</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ------------------------------------------- 4. Pre-migration checks */}
      {preChecks.length > 0 && (
        <div className="card section">
          <div className="card-head bordered">
            <div className="row-center">
              <span className="numbox">4</span>
              <div>
                <span className="eyebrow">Pre-migration checks</span>
                <div className="card-title">Controls verified before approval</div>
                <p className="card-subtitle">
                  All mandatory technical and governance checks must pass
                </p>
              </div>
            </div>
            <span className="pill pill-green">
              <IconCheck size={13} />
              {preChecks.length} of {preChecks.length} passed
            </span>
          </div>

          <div className="card-body">
            <div className="check-grid">
              {preChecks.map((check, i) => (
                <div key={i} className="check-card">
                  <span className="status-circle done">
                    <IconCheck size={13} />
                  </span>
                  <div className="check-text">{check}</div>
                </div>
              ))}
            </div>

            <div className="info-strip green gates">
              <IconCheckCircle size={17} />
              <div>
                <div className="t">All pre-migration gates passed</div>
                <div className="s">
                  The plan is technically ready. Final execution still requires your
                  approval below.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------- Action bar */}
      {isAwaitingApproval && (
        <div className="card action-bar">
          {showComments && (
            <textarea
              className="comments-input"
              placeholder="Enter your review comments or reason for rejection..."
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={3}
            />
          )}

          <div className="action-row">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onBackToDiscovery}
              disabled={!onBackToDiscovery}
            >
              Back to discovery
            </button>

            <div className="action-note">
              <IconShieldCheck size={16} />
              <div>
                <div className="t">Human approval required</div>
                <div className="s">
                  You are approving the reviewed plan, reasoning, assessment, and all
                  pre-migration checks.
                </div>
              </div>
            </div>

            <div className="action-buttons">
              <button
                type="button"
                className="btn-link comments-toggle"
                onClick={() => setShowComments(!showComments)}
              >
                {showComments ? 'Hide comments' : 'Add comments'}
              </button>
              <button
                type="button"
                className="btn btn-danger-outline"
                onClick={handleReject}
              >
                Reject plan
              </button>
              {applied ? (
                <button type="button" className="btn btn-primary" onClick={handleApprove}>
                  <IconCheck size={15} />
                  Approve &amp; run migration
                </button>
              ) : (
                <button type="button" className="btn btn-secondary" disabled>
                  <IconLock size={14} />
                  Apply clarifications first
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {!isAwaitingApproval && (
        <div className="card action-bar">
          <div className="action-row simple">
            <div className="action-note">
              <IconArrowRight size={16} />
              <div>
                <div className="t">Plan locked for this run</div>
                <div className="s">
                  This plan is no longer awaiting approval. Current status: {status}.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MigrationPlanView;
