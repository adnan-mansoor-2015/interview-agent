import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../../services/api';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import VoiceRecorder from './VoiceRecorder';
import ImageUploader from './ImageUploader';
import SearchableDropdown from '../SearchableDropdown/SearchableDropdown';
import Breadcrumb from '../Breadcrumb/Breadcrumb';
import './ChatInterface.css';

function ChatInterface({ category, onBack, sessionId, setSessionId, initialFocusAreas, onViewProgress, userEmail }) {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showEvaluateButton, setShowEvaluateButton] = useState(false);
  const [showNextButton, setShowNextButton] = useState(false);
  const messagesEndRef = useRef(null);
  const initCalledRef = useRef(false);

  // Dropdown navigation state
  const [structure, setStructure] = useState(null);
  const [progress, setProgress] = useState(null);
  const [level1, setLevel1] = useState('');
  const [level2, setLevel2] = useState('');
  const [level3, setLevel3] = useState('');

  // Determine how many dropdown levels this category needs
  const getDropdownLevels = () => {
    if (category === 'technical') return 3;
    if (category === 'behavioral') return 2;
    if (category === 'coding') return 1;
    return 0; // system-design: flat, no dropdowns
  };

  const dropdownLevels = getDropdownLevels();

  // Fetch category structure on mount
  useEffect(() => {
    if (dropdownLevels > 0) {
      api.getCategoryStructure(category).then((res) => {
        if (res.structure) setStructure(res.structure);
      });
    }
  }, [category, dropdownLevels]);

  // Refresh progress after session exists
  const refreshProgress = useCallback(() => {
    if (sessionId) {
      api.getProgress(sessionId).then((res) => {
        if (res.progress) setProgress(res.progress);
      });
    }
  }, [sessionId]);

  useEffect(() => {
    refreshProgress();
  }, [refreshProgress]);

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
      const response = await api.startSession(category, initialFocusAreas || [], userEmail || '');
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

        // Refresh progress after evaluation
        if (response.response.phase === 'question_needed') {
          refreshProgress();
        }
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

  // ── Dropdown handlers ──────────────────────────────────────────

  const applyFocusAndNext = async (focusAreas, label) => {
    if (!sessionId) return;
    await api.updateFocusAreas(sessionId, focusAreas);
    addMessage('system', `Switched to: ${label}`);
    setShowEvaluateButton(false);
    setShowNextButton(false);
    handleSendMessage('next');
  };

  const handleLevel1Change = (value) => {
    setLevel1(value);
    setLevel2('');
    setLevel3('');
    if (!value) return;

    if (dropdownLevels === 1) {
      // Coding: 1 level — apply immediately
      applyFocusAndNext([value], value);
    }
  };

  const handleLevel2Change = (value) => {
    setLevel2(value);
    setLevel3('');
    if (!value) return;

    if (dropdownLevels === 2) {
      // Behavioral: 2 levels — apply on level 2 selection
      applyFocusAndNext([level1, value], `${level1} > ${value}`);
    }
  };

  const handleLevel3Change = (value) => {
    setLevel3(value);
    if (!value) return;

    // Technical: 3 levels — apply on level 3 selection
    applyFocusAndNext([level1, level2, value], `${level1} > ${level2} > ${value}`);
  };

  // ── Helpers for progress-annotated options ─────────────────────

  const getProgressForLevel = (key, parentKey, grandparentKey) => {
    if (!progress || !progress.levels) return null;
    if (grandparentKey) {
      return progress.levels[grandparentKey]?.children?.[parentKey]?.children?.[key];
    }
    if (parentKey) {
      return progress.levels[parentKey]?.children?.[key];
    }
    return progress.levels[key];
  };

  // Convert raw keys into SearchableDropdown option objects
  const buildOptions = (keys, parentKey, grandparentKey) => {
    return keys.map((key) => {
      const progressData = getProgressForLevel(key, parentKey, grandparentKey);
      return {
        value: key,
        label: key,
        progress: progressData && progressData.total
          ? { covered: progressData.covered || 0, total: progressData.total }
          : undefined,
      };
    });
  };

  // ── Build dropdown option lists ────────────────────────────────

  const getLevel1Options = () => {
    if (!structure) return [];
    return Object.keys(structure).filter((k) => k !== 'total');
  };

  const getLevel2Options = () => {
    if (!structure || !level1 || !structure[level1]?.children) return [];
    return Object.keys(structure[level1].children);
  };

  const getLevel3Options = () => {
    if (!structure || !level1 || !level2) return [];
    return Object.keys(structure[level1]?.children?.[level2]?.children || {});
  };

  const getDropdownLabels = () => {
    if (category === 'technical') return ['Category', 'Topic', 'Sub-Topic'];
    if (category === 'behavioral') return ['Company', 'Leadership Principle'];
    if (category === 'coding') return ['Category'];
    return [];
  };

  const labels = getDropdownLabels();

  const getCategoryDisplay = () => {
    const categoryMap = {
      behavioral: 'Behavioral (STAR)',
      technical: 'Technical Knowledge',
      coding: 'Problem Solving',
      'system-design': 'System Design',
    };
    return categoryMap[category] || category;
  };

  // ── Build breadcrumb segments ──────────────────────────────────

  const buildBreadcrumbs = () => {
    const segments = [];
    if (level1) {
      segments.push({
        label: level1,
        onClick: () => { setLevel1(''); setLevel2(''); setLevel3(''); },
      });
    }
    if (level2) {
      segments.push({
        label: level2,
        onClick: () => { setLevel2(''); setLevel3(''); },
      });
    }
    if (level3) {
      segments.push({
        label: level3,
        onClick: () => { setLevel3(''); },
      });
    }
    return segments;
  };

  return (
    <div className="chat-interface">
      <header className="chat-header">
        <div className="header-top">
          <button className="back-button" onClick={onBack}>
            ← Back
          </button>
          <h2>{getCategoryDisplay()}</h2>
          {progress && (
            <span className="overall-progress">
              {progress.covered}/{progress.total} covered ({progress.overall_percent}%)
            </span>
          )}
          {onViewProgress && sessionId && (
            <button className="progress-btn" onClick={onViewProgress}>
              View All Topics
            </button>
          )}
        </div>

        {/* Breadcrumb trail */}
        {dropdownLevels > 0 && (level1 || level2 || level3) && (
          <Breadcrumb segments={buildBreadcrumbs()} />
        )}

        {/* Dropdown navigation */}
        {dropdownLevels > 0 && structure && (
          <div className="topic-dropdowns">
            {/* Level 1 */}
            <SearchableDropdown
              value={level1}
              onChange={handleLevel1Change}
              options={buildOptions(getLevel1Options())}
              placeholder={`All ${labels[0]}s`}
            />

            {/* Level 2 */}
            {dropdownLevels >= 2 && level1 && (
              <SearchableDropdown
                value={level2}
                onChange={handleLevel2Change}
                options={buildOptions(getLevel2Options(), level1)}
                placeholder={`All ${labels[1]}s`}
              />
            )}

            {/* Level 3 */}
            {dropdownLevels >= 3 && level2 && (
              <SearchableDropdown
                value={level3}
                onChange={handleLevel3Change}
                options={buildOptions(getLevel3Options(), level2, level1)}
                placeholder={`All ${labels[2]}s`}
              />
            )}
          </div>
        )}
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
            Evaluate My Answer
          </button>
        )}
        {showNextButton && (
          <button className="action-button next" onClick={handleNext}>
            Next Question
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
