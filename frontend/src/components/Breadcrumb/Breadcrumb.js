import React from 'react';
import './Breadcrumb.css';

/**
 * Breadcrumb trail showing the current selection path.
 *
 * Props:
 *   segments  — [{ label, onClick }]  — clickable path segments
 *   separator — character between segments (default '›')
 */
function Breadcrumb({ segments = [], separator = '›' }) {
  if (segments.length === 0) return null;

  return (
    <nav className="breadcrumb" aria-label="Selection path">
      {segments.map((seg, idx) => (
        <React.Fragment key={idx}>
          {idx > 0 && <span className="breadcrumb-sep">{separator}</span>}
          <button
            className="breadcrumb-segment"
            onClick={seg.onClick}
            title={`Reset to ${seg.label}`}
          >
            {seg.label}
          </button>
        </React.Fragment>
      ))}
    </nav>
  );
}

export default Breadcrumb;
