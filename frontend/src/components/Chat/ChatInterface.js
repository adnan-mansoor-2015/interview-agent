import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import VoiceRecorder from './VoiceRecorder';
import ImageUploader from './ImageUploader';
import './ChatInterface.css';

function ChatInterface({ category, onBack, sessionId, setSessionId }) {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showEvaluateButton, setShowEvaluateButton] = useState(false);
  const [showNextButton, setShowNextButton] = useState(false);
  const messagesEndRef = useRef(null);
  const initCalledRef = useRef(false);

  useEffect(() => {
    // Start session when component mounts (guard against StrictMode double-mount)
    if (!sessionId && !initCalledRef.current) {
      initCalledRef.current = true;
      initializeSession();
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    setLoading(true);
    try {
      const response = await api.startSession(category, []);
      setSessionId(response.session_id);

      if (response.response && response.response.message) {
        addMessage('assistant', response.response.message);
        updateButtonStates(response.response);
      }
    } catch (error) {
      addMessage('system', `Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const addMessage = (role, content) => {
    setMessages((prev) => [...prev, { role, content, timestamp: Date.now() }]);
  };

  const updateButtonStates = (response) => {
    setShowEvaluateButton(response.show_evaluate_button || false);
    setShowNextButton(response.show_next_button || false);
  };

  const handleSendMessage = async (message = currentMessage) => {
    if (!message.trim() || loading || !sessionId) return;

    addMessage('user', message);
    setCurrentMessage('');
    setLoading(true);

    try {
      const response = await api.sendMessage(sessionId, message);

      if (response.response && response.response.message) {
        addMessage('assistant', response.response.message);
        updateButtonStates(response.response);
      }
    } catch (error) {
      addMessage('system', `Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    setCurrentMessage(transcript);
  };

  const handleImageUpload = async (base64Image, description) => {
    if (!sessionId) return;

    addMessage('user', `[Uploaded diagram] ${description}`);
    setLoading(true);

    try {
      const response = await api.uploadImage(sessionId, base64Image, description);

      if (response.response && response.response.message) {
        addMessage('assistant', response.response.message);
        updateButtonStates(response.response);
      }
    } catch (error) {
      addMessage('system', `Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = () => {
    handleSendMessage('evaluate');
    setShowEvaluateButton(false);
  };

  const handleNext = () => {
    handleSendMessage('next');
    setShowNextButton(false);
  };

  const getCategoryDisplay = () => {
    const categoryMap = {
      behavioral: '💬 Behavioral (STAR)',
      technical: '💻 Technical Knowledge',
      coding: '🧩 Problem Solving',
      'system-design': '🏗️ System Design',
    };
    return categoryMap[category] || category;
  };

  return (
    <div className="chat-interface">
      <header className="chat-header">
        <button className="back-button" onClick={onBack}>
          ← Back
        </button>
        <h2>{getCategoryDisplay()}</h2>
      </header>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} role={msg.role} content={msg.content} />
        ))}
        {loading && (
          <MessageBubble role="assistant" content="..." isLoading />
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-actions">
        {showEvaluateButton && (
          <button className="action-button evaluate" onClick={handleEvaluate}>
            🎯 Evaluate My Answer
          </button>
        )}
        {showNextButton && (
          <button className="action-button next" onClick={handleNext}>
            ⏭️ Next Question
          </button>
        )}
      </div>

      <div className="chat-input-area">
        {category === 'system-design' && (
          <ImageUploader onUpload={handleImageUpload} disabled={loading} />
        )}

        <VoiceRecorder
          onTranscript={handleVoiceTranscript}
          disabled={loading}
        />

        <InputArea
          value={currentMessage}
          onChange={setCurrentMessage}
          onSend={() => handleSendMessage()}
          disabled={loading}
          placeholder={
            category === 'behavioral'
              ? 'Use the STAR method: Situation, Task, Action, Result...'
              : category === 'technical'
              ? 'Explain the concept with examples...'
              : category === 'system-design'
              ? 'Describe your architecture or upload a diagram...'
              : 'Type your answer...'
          }
        />
      </div>
    </div>
  );
}

export default ChatInterface;
