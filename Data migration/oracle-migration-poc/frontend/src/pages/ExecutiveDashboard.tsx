import React from 'react';
import {
  IconActivity,
  IconCheck,
  IconCheckCircle,
  IconClock,
  IconShieldCheck,
  IconSparkle,
  IconDatabase,
  IconServer,
  IconShield,
  IconLayers,
  IconChevronRight,
  IconArrowRight,
} from '../components/ui/Icons';
import './ExecutiveDashboard.css';

interface ExecutiveDashboardProps {
  onReviewMigration: () => void;
}

const KPIS = [
  {
    label: 'Active initiatives',
    value: '3',
    caption: 'Across database migration',
    flag: '2 on track',
    tone: 'grey',
    icon: <IconActivity size={16} />,
    tile: 'tile-blue',
  },
  {
    label: 'Completed this month',
    value: '12',
    caption: 'All validations passed',
    flag: '+20% vs last month',
    tone: 'green',
    icon: <IconCheck size={16} />,
    tile: 'tile-green',
  },
  {
    label: 'Needs a decision',
    value: '1',
    caption: 'Waiting for human approval',
    flag: 'Action required',
    tone: 'amber',
    icon: <IconClock size={16} />,
    tile: 'tile-amber',
    highlight: true,
  },
  {
    label: 'Success rate',
    value: '98.7%',
    caption: 'Across completed operations',
    flag: 'Healthy',
    tone: 'green',
    icon: <IconShieldCheck size={16} />,
    tile: 'tile-green',
  },
];

const PORTFOLIO = [
  {
    name: 'Oracle XE Upgrade',
    path: 'Oracle 18c → 21c',
    owner: 'Finance Platform',
    progress: 68,
    stage: 'Human approval',
    badge: 'badge-amber',
  },
  {
    name: 'Customer Data Warehouse',
    path: 'Oracle 19c → Autonomous DB',
    owner: 'Data & Analytics',
    progress: 100,
    stage: 'Completed',
    badge: 'badge-green',
  },
  {
    name: 'HR Reporting Database',
    path: 'SQL Server → Azure SQL',
    owner: 'People Systems',
    progress: 42,
    stage: 'Plan generation',
    badge: 'badge-blue',
  },
  {
    name: 'Legacy Billing Archive',
    path: 'Oracle 12c → Oracle 21c',
    owner: 'Billing Operations',
    progress: 18,
    stage: 'Discovery',
    badge: 'badge-grey',
  },
];

const STAGES = [
  { title: 'Discover', sub: '4 completed', right: '100%', state: 'done' },
  { title: 'Plan', sub: '3 plans ready', right: '75%', state: 'done' },
  {
    title: 'Human approval',
    sub: '1 waiting for you',
    right: 'Action',
    state: 'waiting',
  },
  { title: 'Migrate', sub: '1 scheduled', right: '25%', state: 'idle' },
  { title: 'Validate', sub: '1 fully validated', right: '25%', state: 'idle' },
];

const CAPABILITIES = [
  {
    name: 'Database Migration',
    sub: '4 migrations tracked',
    progress: 76,
    status: 'Live',
    badge: 'badge-blue',
    icon: <IconDatabase size={16} />,
    live: true,
  },
  {
    name: 'Server Migration',
    sub: 'Roadmap placeholder',
    progress: 0,
    status: 'Planned',
    badge: 'badge-grey',
    icon: <IconServer size={16} />,
  },
  {
    name: 'Incident Resolution',
    sub: 'Roadmap placeholder',
    progress: 0,
    status: 'Planned',
    badge: 'badge-grey',
    icon: <IconActivity size={16} />,
  },
  {
    name: 'Patch Management',
    sub: 'Roadmap placeholder',
    progress: 0,
    status: 'Planned',
    badge: 'badge-grey',
    icon: <IconShield size={16} />,
  },
  {
    name: 'CMDB Reconciliation',
    sub: 'Roadmap placeholder',
    progress: 0,
    status: 'Planned',
    badge: 'badge-grey',
    icon: <IconLayers size={16} />,
  },
];

const ACTIVITY = [
  {
    title: 'Warehouse migration validated',
    sub: '12,450,000 rows matched successfully',
    time: '18 min ago',
    icon: <IconCheckCircle size={15} />,
    tile: 'tile-green',
  },
  {
    title: 'Oracle XE plan generated',
    sub: 'AI assessment completed with 92% confidence',
    time: '32 min ago',
    icon: <IconSparkle size={15} />,
    tile: 'tile-blue',
  },
  {
    title: 'Approval requested',
    sub: 'Oracle XE migration needs your decision',
    time: '31 min ago',
    icon: <IconClock size={15} />,
    tile: 'tile-amber',
  },
  {
    title: 'HR database discovered',
    sub: '27 tables and 14 dependencies mapped',
    time: '2 hrs ago',
    icon: <IconDatabase size={15} />,
    tile: 'tile-grey',
  },
];

const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  onReviewMigration,
}) => (
  <div className="exec">
    <div className="page-head">
      <div className="page-head-main">
        <span className="eyebrow">Executive operations view</span>
        <h1 className="page-title">Good morning, Sandeep</h1>
        <p className="page-subtitle">
          Here is what is complete, what is moving, and what needs your attention
          across Agentic Ops.
        </p>
      </div>

      <div className="updated-card">
        <span className="tile tile-sm tile-grey">
          <IconClock size={15} />
        </span>
        <span>
          <span className="eyebrow">Last updated</span>
          <span className="updated-value">Today, 09:42 AM</span>
        </span>
      </div>
    </div>

    {/* ------------------------------------------------------------- KPIs */}
    <div className="kpi-row">
      {KPIS.map((k) => (
        <div key={k.label} className={`kpi ${k.highlight ? 'is-highlight' : ''}`}>
          <div className="kpi-top">
            <span className={`tile tile-sm ${k.tile}`}>{k.icon}</span>
            <span className="eyebrow">{k.label}</span>
          </div>
          <div className="kpi-value">{k.value}</div>
          <div className="kpi-foot">
            <span className="kpi-caption">{k.caption}</span>
            <span className={`kpi-flag ${k.tone}`}>{k.flag}</span>
          </div>
        </div>
      ))}
    </div>

    {/* ---------------------------------------------------------- Attention */}
    <div className="dark-banner attention">
      <div className="lead">
        <span className="tile tile-md">
          <IconSparkle size={18} />
        </span>
        <div>
          <span className="eyebrow">Your attention is needed</span>
          <div className="t">Oracle XE migration is ready for review</div>
          <div className="s">
            The AI plan is prepared. Answer 3 clarification questions, review the
            assessment, and approve when ready. Nothing will execute without your
            approval.
          </div>
        </div>
      </div>

      <div className="attention-action">
        <div className="attention-stage">
          <span className="eyebrow">Current stage</span>
          <div className="stage-name">Human approval</div>
          <div className="stage-eta">~5 min to review</div>
        </div>
        <button type="button" className="btn btn-white" onClick={onReviewMigration}>
          Review migration plan
          <IconArrowRight size={16} />
        </button>
      </div>
    </div>

    {/* ------------------------------------------------- Portfolio + stages */}
    <div className="exec-split">
      <div className="card">
        <div className="card-head bordered">
          <div>
            <h2 className="card-title">Migration portfolio</h2>
            <p className="card-subtitle">All current database migrations in one view</p>
          </div>
          <span className="badge badge-grey">4 total</span>
        </div>

        <div className="card-body flush">
          <table className="data-table">
            <thead>
              <tr>
                <th>Initiative</th>
                <th>Owner</th>
                <th>Overall progress</th>
                <th>Current stage</th>
              </tr>
            </thead>
            <tbody>
              {PORTFOLIO.map((p) => (
                <tr key={p.name}>
                  <td>
                    <div className="row-center">
                      <span className="tile tile-sm tile-blue">
                        <IconDatabase size={15} />
                      </span>
                      <span>
                        <div className="cell-strong">{p.name}</div>
                        <div className="cell-sub">{p.path}</div>
                      </span>
                    </div>
                  </td>
                  <td>{p.owner}</td>
                  <td>
                    <div className="bar-row">
                      <span className="bar">
                        <span
                          className={`bar-fill ${p.progress === 100 ? 'green' : ''}`}
                          style={{ width: `${p.progress}%` }}
                        />
                      </span>
                      <span className="bar-value">{p.progress}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${p.badge}`}>{p.stage}</span>
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
            <h2 className="card-title">Where work stands</h2>
            <p className="card-subtitle">Current migration stages</p>
          </div>
        </div>

        <div className="card-body stage-list">
          {STAGES.map((s) => (
            <div key={s.title} className="stage-row">
              <span className={`status-circle ${s.state}`}>
                {s.state === 'done' && <IconCheck size={14} />}
                {s.state === 'waiting' && <IconClock size={14} />}
                {s.state === 'idle' && <IconArrowRight size={14} />}
              </span>
              <span className="stage-text">
                <span className="stage-title">{s.title}</span>
                <span className="stage-sub">{s.sub}</span>
              </span>
              <span className={`stage-right ${s.state === 'waiting' ? 'amber' : ''}`}>
                {s.right}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>

    {/* ------------------------------------------------ Readiness + activity */}
    <div className="exec-split lower">
      <div className="card">
        <div className="card-head bordered">
          <div>
            <h2 className="card-title">Agent capability readiness</h2>
            <p className="card-subtitle">What is available now and what is planned next</p>
          </div>
        </div>

        <div className="card-body flush">
          {CAPABILITIES.map((c) => (
            <button
              key={c.name}
              type="button"
              className="cap-row"
              onClick={c.live ? onReviewMigration : undefined}
            >
              <span className="tile tile-sm tile-blue">{c.icon}</span>
              <span className="cap-text">
                <span className="cap-name">{c.name}</span>
                <span className="cap-sub">{c.sub}</span>
              </span>
              <span className="cap-bar">
                {c.progress > 0 ? (
                  <>
                    <span className="bar">
                      <span className="bar-fill" style={{ width: `${c.progress}%` }} />
                    </span>
                    <span className="bar-value">{c.progress}%</span>
                  </>
                ) : (
                  <>
                    <span className="bar">
                      <span className="bar-fill grey" style={{ width: '100%' }} />
                    </span>
                    <span className="cap-notstarted">Not started</span>
                  </>
                )}
              </span>
              <span className={`badge ${c.badge}`}>{c.status}</span>
              <IconChevronRight size={15} />
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-head bordered">
          <div>
            <h2 className="card-title">Recent activity</h2>
            <p className="card-subtitle">Latest important updates</p>
          </div>
        </div>

        <div className="card-body act-list">
          {ACTIVITY.map((a) => (
            <div key={a.title} className="act-row">
              <span className={`tile tile-sm ${a.tile}`}>{a.icon}</span>
              <span className="act-text">
                <span className="act-title">{a.title}</span>
                <span className="act-sub">{a.sub}</span>
              </span>
              <span className="act-time">{a.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default ExecutiveDashboard;
