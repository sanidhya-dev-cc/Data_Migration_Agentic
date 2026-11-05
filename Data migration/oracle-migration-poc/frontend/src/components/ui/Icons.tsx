import React from 'react';

/**
 * Shared inline SVG icon set.
 * Every icon inherits `currentColor` so it can be tinted by its container.
 */

interface IconProps {
  size?: number;
  className?: string;
  strokeWidth?: number;
}

const base = (size: number, strokeWidth: number) => ({
  width: size,
  height: size,
  viewBox: '0 0 24 24',
  fill: 'none' as const,
  stroke: 'currentColor',
  strokeWidth,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
});

export const IconSparkle: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z" />
    <path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" />
  </svg>
);

export const IconGrid: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);

export const IconDatabase: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <ellipse cx="12" cy="5.5" rx="8" ry="3" />
    <path d="M4 5.5v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
    <path d="M4 11.5v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
  </svg>
);

export const IconServer: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <rect x="3" y="4" width="18" height="7" rx="2" />
    <rect x="3" y="13" width="18" height="7" rx="2" />
    <path d="M7 7.5h.01M7 16.5h.01" />
  </svg>
);

export const IconActivity: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M3 12h4l3 8 4-16 3 8h4" />
  </svg>
);

export const IconShield: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M12 3l7.5 3v6c0 4.6-3.2 8.3-7.5 9.5C7.7 20.3 4.5 16.6 4.5 12V6L12 3z" />
  </svg>
);

export const IconShieldCheck: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M12 3l7.5 3v6c0 4.6-3.2 8.3-7.5 9.5C7.7 20.3 4.5 16.6 4.5 12V6L12 3z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

export const IconLayers: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M12 3l9 5-9 5-9-5 9-5z" />
    <path d="M3 13l9 5 9-5" />
    <path d="M3 17l9 5 9-5" />
  </svg>
);

export const IconHelp: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.6 9.5a2.5 2.5 0 014.7 1.1c0 1.7-2.3 2-2.3 3.4" />
    <path d="M12 17.2h.01" />
  </svg>
);

export const IconSettings: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 14.4a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.6 1.6 0 00-1.8-.3 1.6 1.6 0 00-1 1.5v.2a2 2 0 01-4 0v-.1a1.6 1.6 0 00-1-1.5 1.6 1.6 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.6 1.6 0 00.3-1.8 1.6 1.6 0 00-1.5-1H3a2 2 0 010-4h.1a1.6 1.6 0 001.5-1 1.6 1.6 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.6 1.6 0 001.8.3H9a1.6 1.6 0 001-1.5V3a2 2 0 014 0v.1a1.6 1.6 0 001 1.5 1.6 1.6 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.6 1.6 0 00-.3 1.8V9a1.6 1.6 0 001.5 1H21a2 2 0 010 4h-.1a1.6 1.6 0 00-1.5 1z" />
  </svg>
);

export const IconChevronRight: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 2 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M9 6l6 6-6 6" />
  </svg>
);

export const IconChevronDown: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 2 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M6 9l6 6 6-6" />
  </svg>
);

export const IconArrowRight: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 2 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M4 12h15" />
    <path d="M13 6l6 6-6 6" />
  </svg>
);

export const IconClock: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3.2 1.9" />
  </svg>
);

export const IconCheck: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 2.4 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </svg>
);

export const IconCheckCircle: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8.5 12.2l2.4 2.4 4.6-4.9" />
  </svg>
);

export const IconFileText: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" />
    <path d="M14 3v5h5" />
    <path d="M9 13h6M9 17h4" />
  </svg>
);

export const IconDownload: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M12 3v12" />
    <path d="M7.5 10.5L12 15l4.5-4.5" />
    <path d="M4 18.5v1a1.5 1.5 0 001.5 1.5h13a1.5 1.5 0 001.5-1.5v-1" />
  </svg>
);

export const IconSliders: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="3.2" />
    <path d="M12 3v2.2M12 18.8V21M21 12h-2.2M5.2 12H3M18.4 5.6l-1.6 1.6M7.2 16.8l-1.6 1.6M18.4 18.4l-1.6-1.6M7.2 7.2L5.6 5.6" />
  </svg>
);

export const IconRotate: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1" />
    <path d="M3 4v5h5" />
  </svg>
);

export const IconAlert: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5v5" />
    <path d="M12 16.3h.01" />
  </svg>
);

export const IconX: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 2.2 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

export const IconLock: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
    <path d="M8 10.5V7.8a4 4 0 018 0v2.7" />
  </svg>
);

export const IconSearch: React.FC<IconProps> = ({ size = 18, className, strokeWidth = 1.8 }) => (
  <svg {...base(size, strokeWidth)} className={className}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.9-3.9" />
  </svg>
);
