import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // Update this based on the actual backend URL
});

// Add a request interceptor to include the auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add a response interceptor to handle 401 Unauthorized globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const loginRequest = (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  return api.post('/api/v1/login/', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
};

export const getSessions = () => api.get('/api/v1/sessions/');
export const createSession = (title) => api.post('/api/v1/sessions/', { title });
export const renameSession = (sessionId, title) => api.put(`/api/v1/sessions/${sessionId}`, { title });
export const deleteSession = (sessionId) => api.delete(`/api/v1/sessions/${sessionId}`);
export const getSessionMessages = (sessionId) => api.get(`/api/v1/sessions/${sessionId}/messages`);

export const CHAT_API_URL = 'http://localhost:8000/api/v1/chat/';

export default api;
