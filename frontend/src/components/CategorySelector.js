import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import './CategorySelector.css';

const CATEGORIES = [
  {
    id: 'behavioral',
    name: 'Behavioral (STAR)',
    icon: '💬',
    description: 'Amazon & Google Leadership Principles',
    color: '#6366f1',
  },
  {
    id: 'technical',
    name: 'Technical Knowledge',
    icon: '💻',
    description: 'Senior Backend Engineer - Cloud, OOP, Algorithms',
    color: '#06b6d4',
  },
  {
    id: 'coding',
    name: 'Problem Solving',
    icon: '🧩',
    description: 'LeetCode & HackerRank - FAANG problems',
    color: '#10b981',
  },
  {
    id: 'system-design',
    name: 'System Design',
    icon: '🏗️',
    description: 'Architecture & Scalability - FAANG questions',
    color: '#f59e0b',
  },
];

function CategorySelector({ onStart }) {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFocus, setSelectedFocus] = useState([]);
  const [focusOptions, setFocusOptions] = useState([]);

  // Load real categories from backend when a category is selected
  useEffect(() => {
    if (!selectedCategory) {
      setFocusOptions([]);
      return;
    }
    // system-design has no subcategories
    if (selectedCategory.id === 'system-design') {
      setFocusOptions([]);
      return;
    }
    api.getCategoryStructure(selectedCategory.id).then((res) => {
      if (res.structure) {
        const keys = Object.keys(res.structure).filter((k) => k !== 'total');
        setFocusOptions(keys);
      }
    }).catch(() => setFocusOptions([]));
  }, [selectedCategory]);

  const handleCategoryClick = (category) => {
    setSelectedCategory(category);
    setSelectedFocus([]);
  };

  const toggleFocus = (focus) => {
    setSelectedFocus((prev) =>
      prev.includes(focus) ? prev.filter((f) => f !== focus) : [...prev, focus]
    );
  };

  const handleStart = () => {
    if (selectedCategory) {
      onStart(selectedCategory.id, selectedFocus);
    }
  };

  return (
    <div className="category-selector">
      <header className="selector-header">
        <h1>AI Interview Prep Agent</h1>
        <p>Practice with real FAANG questions. Get instant AI feedback. Improve iteratively.</p>
      </header>

      <div className="categories-grid">
        {CATEGORIES.map((cat) => (
          <div
            key={cat.id}
            className={`category-card ${selectedCategory?.id === cat.id ? 'selected' : ''}`}
            style={{ borderColor: cat.color }}
            onClick={() => handleCategoryClick(cat)}
          >
            <span className="category-icon">{cat.icon}</span>
            <h3>{cat.name}</h3>
            <p>{cat.description}</p>
          </div>
        ))}
      </div>

      {selectedCategory && focusOptions.length > 0 && (
        <div className="focus-selector">
          <h3>Select Focus Areas (optional):</h3>
          <div className="focus-chips">
            {focusOptions.map((focus) => (
              <button
                key={focus}
                className={`focus-chip ${selectedFocus.includes(focus) ? 'selected' : ''}`}
                onClick={() => toggleFocus(focus)}
              >
                {focus}
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedCategory && (
        <div className="start-button-container">
          <button className="start-button" onClick={handleStart}>
            Start Interview →
          </button>
        </div>
      )}

      <div className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps">
          <div className="step">
            <span className="step-number">1</span>
            <h4>Real Questions</h4>
            <p>Questions sourced from FAANG interview banks (106 behavioral, 173 coding, 131 technical, 36 system design)</p>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <h4>Answer Freely</h4>
            <p>Type, speak, or upload diagrams - AI asks follow-ups like a real interviewer</p>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <h4>Get Feedback</h4>
            <p>Scored breakdown (0-10) with strengths, improvements, and follow-up questions</p>
          </div>
          <div className="step">
            <span className="step-number">4</span>
            <h4>Track Progress</h4>
            <p>Switch topics mid-session with dropdowns. Track coverage at every level.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CategorySelector;
