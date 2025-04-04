/**
 * API Configuration
 */

// Get the API URL from environment variables or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// API endpoints
const ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_URL}/auth/login`,
    REGISTER: `${API_URL}/auth/register`,
    ME: `${API_URL}/auth/me`,
  },
  VIDEOS: {
    LIST: `${API_URL}/videos`,
    UPLOAD: `${API_URL}/videos`,
    DETAILS: (id) => `${API_URL}/videos/${id}`,
    STREAM: (id) => `${API_URL}/videos/stream/${id}`,
    DIRECT_STREAM: (id) => `${API_URL}/direct/videos/${id}`,
  },
  USERS: {
    PROFILE: `${API_URL}/users/me`,
    UPDATE: `${API_URL}/users/me`,
    LIST: `${API_URL}/users`,
    DETAILS: (id) => `${API_URL}/users/${id}`,
  },
  ADMIN: {
    STATS: `${API_URL}/admin/stats`,
    USER_STATS: `${API_URL}/admin/users/stats`,
    STORAGE_STATS: `${API_URL}/admin/storage/stats`,
    USERS: `${API_URL}/admin/users`,
    VIDEOS: `${API_URL}/admin/videos`,
  },
};

export { API_URL, ENDPOINTS };
