import React, { useState } from 'react';
import LoginPage from './components/LoginPage';
import CategorySelector from './components/CategorySelector';
import ChatInterface from './components/Chat/ChatInterface';
import ProgressView from './components/ProgressView';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('login'); // 'login' | 'home' | 'chat' | 'progress'
  const [userEmail, setUserEmail] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [category, setCategory] = useState(null);
  const [focusAreas, setFocusAreas] = useState([]);

  const handleLogin = (email) => {
    setUserEmail(email);
    setCurrentView('home');
  };

  const handleStartSession = (selectedCategory, selectedFocusAreas) => {
    setCategory(selectedCategory);
    setFocusAreas(selectedFocusAreas || []);
    setCurrentView('chat');
  };

  const handleBackHome = () => {
    setCurrentView('home');
    setSessionId(null);
    setCategory(null);
    setFocusAreas([]);
  };

  const handleViewProgress = () => {
    setCurrentView('progress');
  };

  const handleBackToChat = () => {
    setCurrentView('chat');
  };

  const handlePracticeTopic = async (newFocusAreas) => {
    setFocusAreas(newFocusAreas);
    setCurrentView('chat');
  };

  return (
    <div className="app">
      {currentView === 'login' && (
        <LoginPage onLogin={handleLogin} />
      )}
      {currentView === 'home' && (
        <CategorySelector onStart={handleStartSession} />
      )}
      {currentView === 'chat' && (
        <ChatInterface
          category={category}
          onBack={handleBackHome}
          sessionId={sessionId}
          setSessionId={setSessionId}
          initialFocusAreas={focusAreas}
          onViewProgress={handleViewProgress}
          userEmail={userEmail}
        />
      )}
      {currentView === 'progress' && (
        <ProgressView
          sessionId={sessionId}
          category={category}
          onBack={handleBackToChat}
          onPractice={handlePracticeTopic}
          userEmail={userEmail}
        />
      )}
    </div>
  );
}

export default App;
