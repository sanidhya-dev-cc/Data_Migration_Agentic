import React, { useState } from 'react';
import { AgentLog } from '../types';
import { IconCheck, IconChevronDown } from './ui/Icons';
import './AgentLogs.css';

interface AgentLogsProps {
  logs: AgentLog[];
}

/** Formats an agent name such as "intent_analyzer" as "Intent Analyzer". */
const formatAgent = (name: string): string =>
  name
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const AgentLogs: React.FC<AgentLogsProps> = ({ logs }) => {
  const [expanded, setExpanded] = useState(true);

  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <div className="card">
      <div className="card-head bordered clickable" onClick={() => setExpanded(!expanded)}>
        <div>
          <h2 className="card-title">Agent activity &amp; audit trail</h2>
          <p className="card-subtitle">
            A concise record of agent decisions and execution events.
          </p>
        </div>
        <div className="row-center">
          <span className="badge badge-grey">{logs.length} events</span>
          <span className={`expand-chevron ${expanded ? 'is-open' : ''}`}>
            <IconChevronDown size={16} />
          </span>
        </div>
      </div>

      {expanded && (
        <div className="card-body flush">
          {logs.map((log, index) => {
            const isLast = index === logs.length - 1;
            return (
              <div key={index} className="audit-row">
                <span className={`numcircle ${isLast ? 'done' : ''}`}>
                  {isLast ? <IconCheck size={12} /> : index + 1}
                </span>

                <span className="audit-time mono">
                  {new Date(log.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>

                <span className="audit-agent">{formatAgent(log.agent_name)}</span>

                <span className="audit-body">
                  <span className="audit-action">{log.action}</span>
                  {log.reasoning && (
                    <span className="audit-reasoning">{log.reasoning}</span>
                  )}
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <details className="audit-meta">
                      <summary>View metadata</summary>
                      <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
                    </details>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AgentLogs;
