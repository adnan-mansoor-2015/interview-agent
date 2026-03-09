const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async startSession(category, focusAreas = [], userEmail = '') {
    const response = await fetch(`${API_BASE_URL}/chat/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, focus_areas: focusAreas, user_email: userEmail }),
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

  async getCategoryStructure(category) {
    const response = await fetch(`${API_BASE_URL}/categories/${category}/structure`);
    return response.json();
  },

  async updateFocusAreas(sessionId, focusAreas) {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/focus`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus_areas: focusAreas }),
    });
    return response.json();
  },

  async getProgress(sessionId) {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/progress`);
    return response.json();
  },

  async getDetailedProgress(sessionId) {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}/progress/detailed`);
    return response.json();
  },

  async getPersistentProgress(category, userEmail = '') {
    const params = new URLSearchParams({ user_email: userEmail });
    const response = await fetch(`${API_BASE_URL}/progress/${category}?${params}`);
    return response.json();
  },

  async getPersistentDetailedProgress(category, userEmail = '') {
    const params = new URLSearchParams({ user_email: userEmail });
    const response = await fetch(`${API_BASE_URL}/progress/${category}/detailed?${params}`);
    return response.json();
  },

  async resetProgress(userEmail, category) {
    const params = new URLSearchParams({ user_email: userEmail });
    const response = await fetch(`${API_BASE_URL}/progress/${category}?${params}`, {
      method: 'DELETE',
    });
    return response.json();
  },

  async resetAllProgress(userEmail) {
    const params = new URLSearchParams({ user_email: userEmail });
    const response = await fetch(`${API_BASE_URL}/progress?${params}`, {
      method: 'DELETE',
    });
    return response.json();
  },
};
