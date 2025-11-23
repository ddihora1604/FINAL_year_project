import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export const chatAPI = {
  sendMessage: async (message: string, conversationId?: string) => {
    const response = await api.post('/api/chat/message', {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },

  newConversation: async () => {
    const response = await api.post('/api/chat/new');
    return response.data;
  },

  getHistory: async () => {
    const response = await api.get('/api/chat/history');
    return response.data;
  },

  getConversation: async (conversationId: string) => {
    const response = await api.get(`/api/chat/history/${conversationId}`);
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};
