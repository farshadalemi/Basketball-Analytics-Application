/**
 * API Configuration
 */

// Get the API URL from environment variables or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const SCOUTING_API_URL = process.env.REACT_APP_SCOUTING_API_URL || 'http://localhost:8001/api';

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
  SCOUTING: {
    REPORTS: `${SCOUTING_API_URL}/reports`,
    COMPUTER_VISION: {
      PROCESS_VIDEO: `${SCOUTING_API_URL}/computer-vision/process-video`,
      ANALYZE_IMAGE: `${SCOUTING_API_URL}/computer-vision/analyze-image`,
      ANALYZE_IMAGE_VISUAL: `${SCOUTING_API_URL}/computer-vision/analyze-image-visual`,
      ANALYZE_IMAGE_PROGRESSIVE: `${SCOUTING_API_URL}/computer-vision/analyze-image-progressive`,
      JOBS: `${SCOUTING_API_URL}/computer-vision/jobs`,
      JOB_STATUS: (id) => `${SCOUTING_API_URL}/computer-vision/jobs/${id}`,
      RESULTS: (id) => `${SCOUTING_API_URL}/computer-vision/results/${id}`,
    },
  },
};

export { API_URL, SCOUTING_API_URL, ENDPOINTS };
