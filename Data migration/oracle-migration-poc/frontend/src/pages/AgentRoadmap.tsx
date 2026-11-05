import React from 'react';
import {
  IconClock,
  IconCheck,
  IconSparkle,
  IconDatabase,
} from '../components/ui/Icons';
import './AgentRoadmap.css';

interface AgentRoadmapProps {
  name: string;
  summary: string;
  icon: React.ReactNode;
  scope: string[];
  onReturn: () => void;
}

const AgentRoadmap: React.FC<AgentRoadmapProps> = ({
  name,
  summary,
  icon,
  scope,
  onReturn,
}) => (
  <div className="roadmap">
    <div className="card roadmap-card">
      <div className="roadmap-hero">
        <span className="pill pill-dark roadmap-pill">
          <IconClock size={14} />
          Planned capability
        </span>

        <span className="roadmap-icon">{icon}</span>
        <span className="eyebrow roadmap-eyebrow">Agent roadmap</span>
        <h1 className="roadmap-title">{name}</h1>
        <p className="roadmap-summary">{summary}</p>
      </div>

      <div className="roadmap-body">
        <span className="eyebrow">Planned scope</span>
        <h2 className="roadmap-h2">What this agent will do</h2>

        <div className="grid-3 roadmap-grid">
          {scope.map((item, i) => (
            <div key={item} className="roadmap-step">
              <span className="numbox plain">{i + 1}</span>
              <p className="roadmap-step-text">{item}</p>
              <IconCheck size={15} />
            </div>
          ))}
        </div>

        <div className="info-strip amber roadmap-note">
          <IconSparkle size={17} />
          <div>
            <div className="t">Designed for safe automation</div>
            <div className="s">
              Every execution will include policy checks, human approvals, and
              complete audit history.
            </div>
          </div>
        </div>

        <button type="button" className="btn btn-secondary" onClick={onReturn}>
          <IconDatabase size={16} />
          Return to Database Migration
        </button>
      </div>
    </div>
  </div>
);

export default AgentRoadmap;
