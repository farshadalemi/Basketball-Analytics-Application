/**
 * Authentication model
 * Handles user authentication state and operations
 */

// Local storage key for user data
const USER_STORAGE_KEY = 'user';

/**
 * Get user data from local storage
 * @returns {Object|null} User data or null if not found
 */
export const getUserFromStorage = () => {
  try {
    const userStr = localStorage.getItem(USER_STORAGE_KEY);
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('Failed to parse user data from storage:', error);
    return null;
  }
};

/**
 * Save user data to local storage
 * @param {Object} userData - User data to save
 */
export const saveUserToStorage = (userData) => {
  try {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
  } catch (error) {
    console.error('Failed to save user data to storage:', error);
  }
};

/**
 * Remove user data from local storage
 */
export const removeUserFromStorage = () => {
  localStorage.removeItem(USER_STORAGE_KEY);
};

/**
 * Check if user is authenticated
 * @param {Object} user - User object
 * @returns {boolean} True if user is authenticated
 */
export const isAuthenticated = (user) => {
  return !!user && !!user.token;
};

/**
 * Format user data for storage
 * @param {Object} authResponse - Response from authentication API
 * @returns {Object} Formatted user data
 */
export const formatUserData = (authResponse) => {
  if (!authResponse || !authResponse.access_token) {
    return null;
  }

  // Extract user ID from JWT token if user object is not provided
  let userId = null;
  if (!authResponse.user) {
    try {
      // Parse the JWT token to get user ID
      const tokenParts = authResponse.access_token.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        userId = payload.sub; // 'sub' claim contains the user ID
      }
    } catch (error) {
      console.error('Failed to parse JWT token:', error);
    }
  }

  return {
    token: authResponse.access_token,
    type: authResponse.token_type,
    user: authResponse.user || { id: userId, email: userId ? `user-${userId}` : 'user' }
  };
};
