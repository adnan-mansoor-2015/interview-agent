import React, { useState } from 'react';
import CategorySelector from './components/CategorySelector';
import ChatInterface from './components/Chat/ChatInterface';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('home'); // 'home' | 'chat'
  const [sessionId, setSessionId] = useState(null);
  const [category, setCategory] = useState(null);

  const handleStartSession = (selectedCategory, focusAreas) => {
    setCategory(selectedCategory);
    setCurrentView('chat');
  };

  const handleBackHome = () => {
    setCurrentView('home');
    setSessionId(null);
    setCategory(null);
  };

  return (
    <div className="app">
      {currentView === 'home' && (
        <CategorySelector onStart={handleStartSession} />
      )}
      {currentView === 'chat' && (
        <ChatInterface
          category={category}
          onBack={handleBackHome}
          sessionId={sessionId}
          setSessionId={setSessionId}
        />
      )}
    </div>
  );
}

export default App;
