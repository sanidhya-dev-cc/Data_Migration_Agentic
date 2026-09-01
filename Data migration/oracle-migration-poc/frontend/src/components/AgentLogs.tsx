import React, { useState } from 'react';
import { AgentLog } from '../types';
import './AgentLogs.css';

interface AgentLogsProps {
  logs: AgentLog[];
}

const AgentLogs: React.FC<AgentLogsProps> = ({ logs }) => {
  const [expanded, setExpanded] = useState(true);

  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <div className="card agent-logs-card">
      <div className="card-header clickable" onClick={() => setExpanded(!expanded)}>
        <div>
          <h2 className="card-title">Agent Reasoning & Logs</h2>
          <p className="card-subtitle">
            Real-time insights into AI agent decision-making
          </p>
        </div>
        <button className="expand-btn">
          {expanded ? '▼' : '▶'}
        </button>
      </div>

      {expanded && (
        <div className="logs-container">
          <div className="logs-timeline">
            {logs.map((log, index) => (
              <div key={index} className="log-entry">
                <div className="log-marker"></div>
                <div className="log-content">
                  <div className="log-header">
                    <div className="log-agent-name">
                      <span className="agent-icon">🤖</span>
                      {log.agent_name}
                    </div>
                    <div className="log-timestamp">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  <div className="log-action">{log.action}</div>
                  {log.reasoning && (
                    <div className="log-reasoning">{log.reasoning}</div>
                  )}
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <details className="log-metadata">
                      <summary>View Metadata</summary>
                      <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentLogs;
