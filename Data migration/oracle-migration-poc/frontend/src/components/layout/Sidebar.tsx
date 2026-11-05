import React from 'react';
import {
  IconSparkle,
  IconGrid,
  IconDatabase,
  IconServer,
  IconActivity,
  IconShield,
  IconLayers,
  IconHelp,
  IconSettings,
  IconChevronRight,
} from '../ui/Icons';
import './Sidebar.css';

export type ViewKey =
  | 'executive'
  | 'database'
  | 'server'
  | 'incident'
  | 'patch'
  | 'cmdb';

interface NavItem {
  key: ViewKey;
  label: string;
  caption: string;
  icon: React.ReactNode;
  soon?: boolean;
  live?: boolean;
}

const OVERVIEW_ITEMS: NavItem[] = [
  {
    key: 'executive',
    label: 'Executive Dashboard',
    caption: 'Consolidated operations view',
    icon: <IconGrid size={17} />,
  },
];

const AGENT_ITEMS: NavItem[] = [
  {
    key: 'database',
    label: 'Database Migration',
    caption: 'Oracle & SQL workloads',
    icon: <IconDatabase size={17} />,
    live: true,
  },
  {
    key: 'server',
    label: 'Server Migration',
    caption: 'Workload migration factory',
    icon: <IconServer size={17} />,
    soon: true,
  },
  {
    key: 'incident',
    label: 'Incident Resolution',
    caption: 'Diagnosis & self-healing',
    icon: <IconActivity size={17} />,
    soon: true,
  },
  {
    key: 'patch',
    label: 'Patch Management',
    caption: 'Automated patch lifecycle',
    icon: <IconShield size={17} />,
    soon: true,
  },
  {
    key: 'cmdb',
    label: 'CMDB Reconciliation',
    caption: 'Asset data integrity',
    icon: <IconLayers size={17} />,
    soon: true,
  },
];

interface SidebarProps {
  active: ViewKey;
  onNavigate: (view: ViewKey) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ active, onNavigate }) => {
  const renderItem = (item: NavItem) => (
    <button
      key={item.key}
      type="button"
      className={`nav-item ${active === item.key ? 'is-active' : ''}`}
      onClick={() => onNavigate(item.key)}
    >
      <span className="nav-icon">{item.icon}</span>
      <span className="nav-text">
        <span className="nav-label">{item.label}</span>
        <span className="nav-caption">{item.caption}</span>
      </span>
      {item.soon && <span className="nav-soon">Soon</span>}
      {item.live && <span className="nav-live" aria-label="Live" />}
    </button>
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">
          <IconSparkle size={19} />
        </span>
        <span className="brand-text">
          <span className="brand-name">Agentic Ops</span>
          <span className="brand-sub">Enterprise AI platform</span>
        </span>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-group-label">Overview</div>
        {OVERVIEW_ITEMS.map(renderItem)}

        <div className="nav-group-label spaced">AI Agents</div>
        {AGENT_ITEMS.map(renderItem)}
      </nav>

      <div className="sidebar-foot">
        <button type="button" className="foot-link">
          <IconHelp size={16} />
          <span>Help &amp; documentation</span>
        </button>
        <button type="button" className="foot-link">
          <IconSettings size={16} />
          <span>Platform settings</span>
        </button>

        <button type="button" className="foot-user">
          <span className="user-avatar">S</span>
          <span className="user-text">
            <span className="user-name">Sandeep</span>
            <span className="user-role">Platform administrator</span>
          </span>
          <IconChevronRight size={16} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
