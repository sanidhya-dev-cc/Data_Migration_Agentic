import React from 'react';
import {
  IconSliders,
  IconGrid,
  IconFileText,
  IconCheck,
  IconClock,
  IconShieldCheck,
} from './Icons';

const STEPS = [
  { label: 'Configure', icon: <IconSliders size={16} /> },
  { label: 'Discover', icon: <IconGrid size={16} /> },
  { label: 'Plan & approve', icon: <IconFileText size={16} /> },
  { label: 'Migrate & validate', icon: <IconCheck size={16} /> },
];

interface WizardHeaderProps {
  /** 1-based index of the active wizard step. */
  step: number;
  title: string;
  subtitle: string;
}

const WizardHeader: React.FC<WizardHeaderProps> = ({ step, title, subtitle }) => (
  <>
    <div className="page-head">
      <div className="page-head-main">
        <div className="agent-tag">
          <span className="vendor">Oracle</span>
          <span className="agent-name">Database Migration Agent</span>
        </div>
        <h1 className="page-title">{title}</h1>
        <p className="page-subtitle">{subtitle}</p>
      </div>

      <div className="page-meta">
        <span className="page-meta-item">
          <IconClock size={15} />
          Est. 8–12 min
        </span>
        <span className="page-meta-item">
          <IconShieldCheck size={15} />
          Approval required
        </span>
      </div>
    </div>

    <div className="card">
      <div className="stepper">
        {STEPS.map((s, i) => {
          const index = i + 1;
          const state = index < step ? 'done' : index === step ? 'current' : 'todo';
          return (
            <div key={s.label} className={`step ${state}`}>
              <span className="step-mark">
                {state === 'done' ? <IconCheck size={15} /> : s.icon}
              </span>
              <span>
                <span className="step-k">Step {index}</span>
                <span className="step-v">{s.label}</span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  </>
);

export default WizardHeader;
