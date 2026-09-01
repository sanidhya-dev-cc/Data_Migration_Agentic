import React, { useState } from 'react';
import './App.css';
import MigrationDashboard from './pages/MigrationDashboard';
import DatabaseSelector from './components/DatabaseSelector';
import { DatabaseConfig } from './types';

function App() {
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

  return (
    <div className="App">
      <div className="app-container">
        <header className="app-header">
          <div className="header-content">
            <div className="header-title">
              <div className="logo">O</div>
              <div>
                <h1>Agentic AI Oracle Migration Platform</h1>
                <p className="header-subtitle">
                  Intelligent Two-Step Database Migration: 19c → 19c PDB → 23c PDB
                </p>
              </div>
            </div>
            <div className="header-actions">
              <div className="status-badge">
                <div className="status-indicator"></div>
                <span>System Active</span>
              </div>
            </div>
          </div>
        </header>

        <main className="main-content">
          {!showDashboard ? (
            <DatabaseSelector onSelect={handleDatabasesSelected} />
          ) : (
            <MigrationDashboard
              databases={selectedDatabases}
              onBack={handleBackToSelection}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
