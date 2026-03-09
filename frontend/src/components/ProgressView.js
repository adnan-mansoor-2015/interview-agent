import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import './ProgressView.css';

function ProgressBar({ covered, total }) {
  const percent = total > 0 ? Math.round((covered / total) * 100) : 0;
  return (
    <div className="progress-bar-container">
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="progress-bar-label">{covered}/{total} ({percent}%)</span>
    </div>
  );
}

function ItemRow({ item }) {
  return (
    <div className={`item-row ${item.covered ? 'covered' : ''}`}>
      <span className={`item-icon ${item.covered ? 'checked' : ''}`}>
        {item.covered ? '\u2713' : '\u25CB'}
      </span>
      <span className="item-name">{item.name}</span>
      {item.difficulty && (
        <span className={`difficulty-badge ${item.difficulty.toLowerCase()}`}>
          {item.difficulty}
        </span>
      )}
      {item.company && (
        <span className="company-badge">{item.company}</span>
      )}
    </div>
  );
}

function CollapsibleSection({ name, data, depth, onPractice, focusPath }) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = data.children && Object.keys(data.children).length > 0;
  const hasItems = data.items && data.items.length > 0;

  return (
    <div className={`section depth-${depth}`}>
      <div className="section-header" onClick={() => setExpanded(!expanded)}>
        <span className={`chevron ${expanded ? 'expanded' : ''}`}>{'\u25B6'}</span>
        <span className="section-name">{name}</span>
        <ProgressBar covered={data.covered || 0} total={data.total || 0} />
        {onPractice && data.covered < data.total && (
          <button
            className="practice-btn"
            onClick={(e) => {
              e.stopPropagation();
              onPractice([...focusPath, name]);
            }}
          >
            Practice
          </button>
        )}
      </div>

      {expanded && (
        <div className="section-body">
          {hasChildren && Object.entries(data.children).map(([childName, childData]) => (
            <CollapsibleSection
              key={childName}
              name={childName}
              data={childData}
              depth={depth + 1}
              onPractice={onPractice}
              focusPath={[...focusPath, name]}
            />
          ))}
          {hasItems && (
            <div className="items-list">
              {data.items.map((item, idx) => (
                <ItemRow key={idx} item={item} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConfirmDialog({ message, onConfirm, onCancel }) {
  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <p className="confirm-message">{message}</p>
        <div className="confirm-actions">
          <button className="confirm-cancel" onClick={onCancel}>Cancel</button>
          <button className="confirm-ok" onClick={onConfirm}>Reset</button>
        </div>
      </div>
    </div>
  );
}

function ProgressView({ sessionId, category, onBack, onPractice, userEmail }) {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirmAction, setConfirmAction] = useState(null); // null | { type, message }

  const loadProgress = useCallback(() => {
    setLoading(true);
    // Use session-based if we have a sessionId, otherwise persistent
    const fetchFn = sessionId
      ? api.getDetailedProgress(sessionId)
      : api.getPersistentDetailedProgress(category, userEmail || '');

    fetchFn.then((res) => {
      if (res.progress) setProgress(res.progress);
    }).finally(() => setLoading(false));
  }, [sessionId, category, userEmail]);

  useEffect(() => {
    loadProgress();
  }, [loadProgress]);

  const handleResetCategory = () => {
    setConfirmAction({
      type: 'category',
      message: `Reset all progress for ${getCategoryDisplay()}? This cannot be undone.`,
    });
  };

  const handleResetAll = () => {
    setConfirmAction({
      type: 'all',
      message: 'Reset ALL progress across every category? This cannot be undone.',
    });
  };

  const executeReset = async () => {
    if (!confirmAction || !userEmail) return;
    if (confirmAction.type === 'category') {
      await api.resetProgress(userEmail, category);
    } else {
      await api.resetAllProgress(userEmail);
    }
    setConfirmAction(null);
    loadProgress();
  };

  const getCategoryDisplay = () => {
    const map = {
      behavioral: 'Behavioral (STAR)',
      technical: 'Technical Knowledge',
      coding: 'Problem Solving',
      'system-design': 'System Design',
    };
    return map[category] || category;
  };

  if (loading) {
    return (
      <div className="progress-view">
        <div className="progress-loading">Loading progress...</div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="progress-view">
        <div className="progress-loading">No progress data available.</div>
      </div>
    );
  }

  const hasLevels = progress.levels && Object.keys(progress.levels).length > 0;
  const hasTopLevelItems = progress.items && progress.items.length > 0;

  return (
    <div className="progress-view">
      {confirmAction && (
        <ConfirmDialog
          message={confirmAction.message}
          onConfirm={executeReset}
          onCancel={() => setConfirmAction(null)}
        />
      )}

      <header className="progress-header">
        <button className="back-button" onClick={onBack}>
          ← Back to Interview
        </button>
        <h2>{getCategoryDisplay()} — Progress</h2>
        <div className="reset-actions">
          <button className="reset-btn" onClick={handleResetCategory}>
            Reset {getCategoryDisplay()}
          </button>
          <button className="reset-btn reset-all" onClick={handleResetAll}>
            Reset All
          </button>
        </div>
      </header>

      <div className="progress-summary">
        <div className="summary-stat">
          <span className="stat-number">{progress.covered}</span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="summary-stat">
          <span className="stat-number">{progress.total - progress.covered}</span>
          <span className="stat-label">Remaining</span>
        </div>
        <div className="summary-stat">
          <span className="stat-number">{progress.overall_percent}%</span>
          <span className="stat-label">Coverage</span>
        </div>
        <div className="summary-bar">
          <ProgressBar covered={progress.covered} total={progress.total} />
        </div>
      </div>

      <div className="progress-tree">
        {hasLevels && Object.entries(progress.levels).map(([name, data]) => (
          <CollapsibleSection
            key={name}
            name={name}
            data={data}
            depth={0}
            onPractice={onPractice}
            focusPath={[]}
          />
        ))}

        {hasTopLevelItems && (
          <div className="items-list top-level">
            {progress.items.map((item, idx) => (
              <ItemRow key={idx} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProgressView;
