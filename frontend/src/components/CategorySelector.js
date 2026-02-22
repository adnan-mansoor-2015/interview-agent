import React, { useState } from 'react';
import './CategorySelector.css';

const CATEGORIES = [
  {
    id: 'behavioral',
    name: 'Behavioral (STAR)',
    icon: '💬',
    description: 'Amazon & Google Leadership Principles',
    color: '#6366f1',
    focusOptions: ['Amazon Leadership Principles', 'Google Googleyness'],
  },
  {
    id: 'technical',
    name: 'Technical Knowledge',
    icon: '💻',
    description: 'Senior Backend Engineer - Cloud, OOP, Algorithms',
    color: '#06b6d4',
    focusOptions: ['Cloud Architecture', 'OOP & Design Patterns', 'Data Structures & Algorithms', 'Prompt Engineering'],
  },
  {
    id: 'coding',
    name: 'Problem Solving',
    icon: '🧩',
    description: 'LeetCode & HackerRank - FAANG problems',
    color: '#10b981',
    focusOptions: [],
  },
  {
    id: 'system-design',
    name: 'System Design',
    icon: '🏗️',
    description: 'Architecture & Scalability - FAANG questions',
    color: '#f59e0b',
    focusOptions: [],
  },
];

function CategorySelector({ onStart }) {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFocus, setSelectedFocus] = useState([]);

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
        <h1>🤖 AI Interview Prep Agent</h1>
        <p>Practice with real FAANG questions • Get instant AI feedback • Improve iteratively</p>
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

      {selectedCategory && selectedCategory.focusOptions.length > 0 && (
        <div className="focus-selector">
          <h3>Select Focus Areas (optional):</h3>
          <div className="focus-chips">
            {selectedCategory.focusOptions.map((focus) => (
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
            <p>AI searches Reddit, Glassdoor, LeetCode for verified FAANG questions</p>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <h4>Answer Freely</h4>
            <p>Type, speak, or upload diagrams - AI asks follow-ups if incomplete</p>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <h4>Get Feedback</h4>
            <p>Instant scores (0-10) with strengths, improvements, and follow-up questions</p>
          </div>
          <div className="step">
            <span className="step-number">4</span>
            <h4>Iterate</h4>
            <p>Practice unlimited questions, refine answers, track progress</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CategorySelector;
