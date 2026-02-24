import React from 'react';
import './InputArea.css';

function InputArea({ value, onChange, onSend, disabled, placeholder }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="input-area">
      <textarea
        className="message-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        rows={3}
      />
      <button
        className="send-button"
        onClick={onSend}
        disabled={disabled || !value.trim()}
      >
        Send →
      </button>
    </div>
  );
}

export default InputArea;
