/**
 * API Configuration
 */

// Get the API URL from environment variables or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// API endpoints
const ENDPOINTS = {
  BASE_URL: API_URL.replace('/api', ''), // Remove /api suffix for base URL
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
  SCOUTING: {
    BASE: `${API_URL}/scouting`,
    ANALYZE: (videoId) => `${API_URL}/scouting/analyze/${videoId}`,
    JOBS: `${API_URL}/scouting/jobs`,
    VIDEO_JOBS: (videoId) => `${API_URL}/scouting/videos/${videoId}/jobs`,
    JOB_STATUS: (jobId) => `${API_URL}/scouting/jobs/${jobId}/status`,
    JOB_RESULT: (jobId) => `${API_URL}/scouting/jobs/${jobId}/result`,
    DELETE_JOB: (jobId) => `${API_URL}/scouting/jobs/${jobId}`,
    HEALTH: `${API_URL}/scouting/health`,
    REPORTS: `${API_URL}/scouting/reports`,
    UPLOAD_CSV: `${API_URL}/scouting/upload-csv`,
  },
};

export { API_URL, ENDPOINTS };
