import api from './api.js';

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  sendOtp: (data) => api.post('/auth/send-otp', data),
  verifyOtp: (data) => api.post('/auth/verify-otp', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
};

// ─── Projects ─────────────────────────────────────────────────────────────────
export const projectService = {
  getAll: (params) => api.get('/projects', { params }),
  getById: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

// ─── Videos ───────────────────────────────────────────────────────────────────
export const videoService = {
  generate: (data) => api.post('/videos/generate', data),
  getById: (id) => api.get(`/videos/${id}`),
  getByProject: (projectId) => api.get(`/videos?projectId=${projectId}`),
};

// ─── Scenes ───────────────────────────────────────────────────────────────────
export const sceneService = {
  getByVideo: (videoId) => api.get(`/scenes?videoId=${videoId}`),
  getById: (id) => api.get(`/scenes/${id}`),
  update: (id, data) => api.put(`/scenes/${id}`, data),
};

// ─── Edits ────────────────────────────────────────────────────────────────────
export const editService = {
  getByScene: (sceneId) => api.get(`/edits?sceneId=${sceneId}`),
  getByVideo: (videoId) => api.get(`/edits?videoId=${videoId}`),
};
