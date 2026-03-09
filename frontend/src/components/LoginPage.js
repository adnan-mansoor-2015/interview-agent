import React, { useState } from 'react';
import './LoginPage.css';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }
    if (!validateEmail(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }
    setError('');
    onLogin(email.trim().toLowerCase());
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">AI Interview Prep Agent</h1>
        <p className="login-subtitle">Enter your email to track your progress across sessions</p>

        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="email"
            className="login-input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError(''); }}
            autoFocus
          />
          {error && <span className="login-error">{error}</span>}
          <button type="submit" className="login-button">
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
