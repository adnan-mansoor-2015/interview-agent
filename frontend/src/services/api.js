const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async startSession(category, focusAreas = []) {
    const response = await fetch(`${API_BASE_URL}/chat/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, focus_areas: focusAreas }),
    });
    return response.json();
  },

  async sendMessage(sessionId, message) {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    return response.json();
  },

  async uploadImage(sessionId, imageBase64, description = '') {
    const response = await fetch(`${API_BASE_URL}/chat/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        image_base64: imageBase64,
        description,
      }),
    });
    return response.json();
  },

  async getSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}`);
    return response.json();
  },
};
