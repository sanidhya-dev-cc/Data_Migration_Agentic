import React from 'react';
import { IconChevronRight, IconSettings } from '../ui/Icons';
import './TopBar.css';

interface TopBarProps {
  /** Current page name, shown as the active breadcrumb segment. */
  page: string;
}

const TopBar: React.FC<TopBarProps> = ({ page }) => (
  <header className="topbar">
    <nav className="crumbs" aria-label="Breadcrumb">
      <span className="crumb">Agentic Ops</span>
      <IconChevronRight size={14} />
      <span className="crumb current">{page}</span>
    </nav>

    <div className="topbar-actions">
      <span className="pill pill-green">
        <span className="dot dot-green" />
        All systems operational
      </span>
      <button type="button" className="icon-btn" aria-label="Settings">
        <IconSettings size={17} />
      </button>
      <span className="topbar-avatar">S</span>
    </div>
  </header>
);

export default TopBar;
