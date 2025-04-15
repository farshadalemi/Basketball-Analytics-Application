import { getUserFromStorage } from '../models/auth';

/**
 * Intercepts fetch requests to add authentication headers
 */
const originalFetch = window.fetch;

window.fetch = async function(url, options = {}) {
  // Only intercept requests to our API
  if (url.includes('localhost:8000')) {
    // Get the user token
    const userData = getUserFromStorage();
    const token = userData?.token;

    if (token) {
      // Create headers object if it doesn't exist
      options.headers = options.headers || {};

      // Add authorization header
      options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      };

      // Add credentials mode
      options.credentials = 'include';
    }
  }

  // Call the original fetch with our modified options
  return originalFetch(url, options);
};

/**
 * Fetch with authentication headers
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise} - Fetch promise
 */
export const fetchWithAuth = async (url, options = {}) => {
  // Get the user token
  const userData = getUserFromStorage();
  const token = userData?.token;

  if (token) {
    // Create headers object if it doesn't exist
    options.headers = options.headers || {};

    // Add authorization header
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };

    // Add credentials mode
    options.credentials = 'include';
  }

  // Call fetch with our options
  return fetch(url, options);
};

export default function setupFetchInterceptor() {
  console.log('Fetch interceptor set up');
  // This function is just a marker to indicate the interceptor is set up
  return true;
}
