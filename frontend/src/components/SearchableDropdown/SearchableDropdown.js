import React, { useState, useRef, useEffect, useCallback } from 'react';
import './SearchableDropdown.css';

/**
 * Custom searchable dropdown with progress badges.
 *
 * Props:
 *   value       — currently selected value (string)
 *   onChange     — callback(value) when a new option is picked
 *   options      — [{ value, label, progress?: { covered, total } }]
 *   placeholder  — text shown when nothing is selected
 *   disabled     — disable interaction
 */
function SearchableDropdown({ value, onChange, options = [], placeholder = 'Select...', disabled = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [highlightIdx, setHighlightIdx] = useState(0);
  const containerRef = useRef(null);
  const searchInputRef = useRef(null);
  const listRef = useRef(null);

  // Filtered options based on search text
  const filtered = options.filter((opt) =>
    opt.label.toLowerCase().includes(search.toLowerCase())
  );

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const items = listRef.current.querySelectorAll('.sd-option');
      if (items[highlightIdx]) {
        items[highlightIdx].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightIdx, isOpen]);

  const toggle = useCallback(() => {
    if (disabled) return;
    setIsOpen((prev) => {
      if (!prev) {
        setSearch('');
        setHighlightIdx(0);
      }
      return !prev;
    });
  }, [disabled]);

  const selectOption = useCallback(
    (opt) => {
      onChange(opt.value);
      setIsOpen(false);
      setSearch('');
    },
    [onChange]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (!isOpen) {
        if (e.key === 'Enter' || e.key === 'ArrowDown') {
          e.preventDefault();
          setIsOpen(true);
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightIdx((prev) => Math.min(prev + 1, filtered.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightIdx((prev) => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filtered[highlightIdx]) selectOption(filtered[highlightIdx]);
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          setSearch('');
          break;
        default:
          break;
      }
    },
    [isOpen, filtered, highlightIdx, selectOption]
  );

  // Current label for the trigger
  const selectedOption = options.find((o) => o.value === value);
  const displayLabel = selectedOption ? selectedOption.label : placeholder;

  return (
    <div
      className={`sd-container ${disabled ? 'sd-disabled' : ''}`}
      ref={containerRef}
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        className={`sd-trigger ${isOpen ? 'sd-open' : ''} ${value ? 'sd-has-value' : ''}`}
        onClick={toggle}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="sd-trigger-label">{displayLabel}</span>
        <span className="sd-chevron">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="sd-panel">
          {options.length > 5 && (
            <div className="sd-search-wrapper">
              <input
                ref={searchInputRef}
                className="sd-search"
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setHighlightIdx(0);
                }}
              />
            </div>
          )}

          <ul className="sd-list" ref={listRef} role="listbox">
            {filtered.length === 0 && (
              <li className="sd-no-results">No matches</li>
            )}
            {filtered.map((opt, idx) => (
              <li
                key={opt.value}
                className={`sd-option ${idx === highlightIdx ? 'sd-highlighted' : ''} ${
                  opt.value === value ? 'sd-selected' : ''
                }`}
                role="option"
                aria-selected={opt.value === value}
                onMouseEnter={() => setHighlightIdx(idx)}
                onClick={() => selectOption(opt)}
              >
                <span className="sd-option-label">{opt.label}</span>
                {opt.progress && (
                  <span className="sd-badge">
                    {opt.progress.covered}/{opt.progress.total}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default SearchableDropdown;
