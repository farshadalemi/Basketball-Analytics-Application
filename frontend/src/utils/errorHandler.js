/**
 * Utility functions for handling API errors and displaying appropriate messages
 */

/**
 * Extract user-friendly error message from API error response
 * 
 * @param {Error} error - Error object from API call
 * @param {string} defaultMsg - Default error message
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error, defaultMsg = 'An error occurred') => {
  // No error
  if (!error) {
    return defaultMsg;
  }

  // Already a user-friendly message
  if (typeof error === 'string') {
    return error;
  }

  // Response from server with error message
  if (error.response) {
    // Handle backend JSON responses
    const { data } = error.response;
    
    if (data) {
      // Our API format: { message: "Error message" }
      if (data.message) {
        return data.message;
      }
      
      // Alternative format: { detail: "Error detail" }
      if (data.detail) {
        return data.detail;
      }
      
      // Validation errors format: { errors: [...] }
      if (data.errors && Array.isArray(data.errors) && data.errors.length > 0) {
        return data.errors[0].message || 'Validation error';
      }
    }
    
    // Handle HTTP status code
    const { status } = error.response;
    if (status === 401) {
      return 'Authentication required. Please log in.';
    }
    if (status === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (status === 404) {
      return 'The requested resource was not found.';
    }
    if (status === 422) {
      return 'The request contains invalid data.';
    }
    if (status >= 500) {
      return 'Server error. Please try again later.';
    }
  }

  // Network errors
  if (error.request && !error.response) {
    return 'Network error. Please check your connection.';
  }

  // Use error message if available
  if (error.message) {
    return error.message;
  }

  // Fallback to default message
  return defaultMsg;
};

/**
 * Common error categories for specific error handling
 */
export const isAuthError = (error) => {
  return error.response && (error.response.status === 401 || error.response.status === 403);
};

export const isValidationError = (error) => {
  return error.response && error.response.status === 422;
};

export const isNetworkError = (error) => {
  return error.request && !error.response;
};

/**
 * Handle authentication errors and redirect if needed
 * 
 * @param {Error} error - Error object
 * @param {Function} navigate - React Router's navigate function
 * @returns {boolean} Whether the error was handled
 */
export const handleAuthError = (error, navigate) => {
  if (error.response && error.response.status === 401) {
    // Clear user data
    localStorage.removeItem('user');
    
    // Redirect to login
    navigate('/login', {
      state: { 
        from: window.location.pathname,
        message: 'Your session has expired. Please log in again.'
      }
    });
    
    return true;
  }
  
  return false;
}; 