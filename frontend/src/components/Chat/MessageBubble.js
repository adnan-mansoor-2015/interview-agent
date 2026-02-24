import React from 'react';
import './MessageBubble.css';

function MessageBubble({ role, content, isLoading }) {
  return (
    <div className={`message-bubble ${role}`}>
      <div className="message-content">
        {isLoading ? (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        ) : (
          <div className="message-text">{formatMessage(content)}</div>
        )}
      </div>
    </div>
  );
}

function formatMessage(content) {
  // Convert markdown-style formatting to JSX
  const lines = content.split('\n');
  return lines.map((line, idx) => {
    if (line.startsWith('**') && line.endsWith('**')) {
      return <strong key={idx}>{line.slice(2, -2)}</strong>;
    }
    if (line.startsWith('• ') || line.startsWith('- ')) {
      return <li key={idx}>{line.slice(2)}</li>;
    }
    if (line.startsWith('# ')) {
      return <h3 key={idx}>{line.slice(2)}</h3>;
    }
    if (line.trim() === '') {
      return <br key={idx} />;
    }
    return <p key={idx}>{line}</p>;
  });
}

export default MessageBubble;
