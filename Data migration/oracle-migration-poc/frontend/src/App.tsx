import React, { useState } from 'react';
import './App.css';
import MigrationDashboard from './pages/MigrationDashboard';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import AgentRoadmap from './pages/AgentRoadmap';
import DatabaseSelector from './components/DatabaseSelector';
import Sidebar, { ViewKey } from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';
import { IconServer, IconActivity, IconShield, IconLayers } from './components/ui/Icons';
import { DatabaseConfig } from './types';

const PAGE_TITLES: Record<ViewKey, string> = {
  executive: 'Executive Dashboard',
  database: 'Database Migration',
  server: 'Server Migration',
  incident: 'Incident Resolution',
  patch: 'Patch Management',
  cmdb: 'CMDB Reconciliation',
};

const ROADMAPS: Record<string, {
  name: string;
  summary: string;
  icon: React.ReactNode;
  scope: string[];
}> = {
  server: {
    name: 'Server Migration Agent',
    summary:
      'Workload migration factory will become part of the same governed Agentic Ops workspace.',
    icon: <IconServer size={24} />,
    scope: [
      'Discover server configurations and dependencies',
      'Generate repeatable migration waves',
      'Validate workloads after cutover',
    ],
  },
  incident: {
    name: 'Incident Resolution Agent',
    summary:
      'Diagnosis and self-healing will become part of the same governed Agentic Ops workspace.',
    icon: <IconActivity size={24} />,
    scope: [
      'Correlate alerts into a single probable cause',
      'Propose a remediation plan for review',
      'Verify service health after the fix',
    ],
  },
  patch: {
    name: 'Patch Management Agent',
    summary:
      'Automated patch lifecycle will become part of the same governed Agentic Ops workspace.',
    icon: <IconShield size={24} />,
    scope: [
      'Assess patch applicability across the estate',
      'Sequence rollout rings with rollback points',
      'Confirm compliance after deployment',
    ],
  },
  cmdb: {
    name: 'CMDB Reconciliation Agent',
    summary:
      'Asset data integrity will become part of the same governed Agentic Ops workspace.',
    icon: <IconLayers size={24} />,
    scope: [
      'Compare discovered assets against CMDB records',
      'Explain every detected discrepancy',
      'Apply approved corrections with an audit trail',
    ],
  },
};

function App() {
  const [view, setView] = useState<ViewKey>('executive');

  const [selectedDatabases, setSelectedDatabases] = useState<{
    source?: DatabaseConfig;
    intermediate?: DatabaseConfig;
    target?: DatabaseConfig;
  }>({});

  const [showDashboard, setShowDashboard] = useState(false);

  const handleDatabasesSelected = (databases: {
    source?: DatabaseConfig;
    intermediate?: DatabaseConfig;
    target?: DatabaseConfig;
  }) => {
    setSelectedDatabases(databases);
    setShowDashboard(true);
  };

  const handleBackToSelection = () => {
    setShowDashboard(false);
  };

  const goToMigration = () => {
    setView('database');
  };

  const renderView = () => {
    if (view === 'executive') {
      return <ExecutiveDashboard onReviewMigration={goToMigration} />;
    }

    if (view === 'database') {
      return !showDashboard ? (
        <DatabaseSelector onSelect={handleDatabasesSelected} />
      ) : (
        <MigrationDashboard
          databases={selectedDatabases}
          onBack={handleBackToSelection}
        />
      );
    }

    const roadmap = ROADMAPS[view];
    return (
      <AgentRoadmap
        name={roadmap.name}
        summary={roadmap.summary}
        icon={roadmap.icon}
        scope={roadmap.scope}
        onReturn={goToMigration}
      />
    );
  };

  return (
    <div className="app-shell">
      <Sidebar active={view} onNavigate={setView} />

      <div className="workspace">
        <TopBar page={PAGE_TITLES[view]} />
        <main className="workspace-body">
          <div className="workspace-inner">{renderView()}</div>
        </main>
      </div>
    </div>
  );
}

export default App;
