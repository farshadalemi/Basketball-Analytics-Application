import { getErrorMessage, handleAuthError } from './errorHandler';

/**
 * Wraps API calls with error handling
 * 
 * @param {Function} apiCall - The API call function to execute
 * @param {Object} options - Options for handling the API call
 * @param {Function} options.onSuccess - Callback for successful response
 * @param {Function} options.onError - Custom error handler
 * @param {Function} options.showError - Function to display error messages (from useToast)
 * @param {boolean} options.showErrorToast - Whether to show error toast notification (default: true)
 * @param {Function} options.navigate - React Router's navigate function for auth redirects
 * @param {String} options.defaultErrorMsg - Default error message
 * @returns {Promise} - Result of the API call
 */
export const withErrorHandling = async (
  apiCall,
  {
    onSuccess,
    onError,
    showError,
    showErrorToast = true,
    navigate,
    defaultErrorMsg = "An error occurred",
    debug = false
  } = {}
) => {
  try {
    if (debug) {
      console.log('Making API call with options:', {
        hasOnSuccess: !!onSuccess,
        hasOnError: !!onError,
        showErrorToast,
        defaultErrorMsg
      });
    }
    
    // Execute the API call
    const response = await apiCall();
    
    if (debug) {
      console.log('API call successful, response:', response);
    }
    
    // Handle success
    if (onSuccess) {
      onSuccess(response);
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error);
    
    // Handle authentication errors (redirect to login)
    if (navigate && handleAuthError(error, navigate)) {
      return null;
    }
    
    // Get user-friendly error message
    const errorMessage = getErrorMessage(error, defaultErrorMsg);
    
    if (debug) {
      console.error('Error details:', {
        message: errorMessage,
        originalError: error.message,
        status: error.response?.status,
        data: error.response?.data
      });
    }
    
    // Show error toast if enabled
    if (showErrorToast && showError) {
      showError(errorMessage);
    }
    
    // Call custom error handler if provided
    if (onError) {
      onError(error, errorMessage);
    }
    
    // Re-throw error for caller to handle if needed
    throw error;
  }
};

/**
 * Creates an API wrapper with error handling
 * 
 * @param {Object} api - The API client instance
 * @param {Function} showError - Function to display errors
 * @param {Function} navigate - Navigation function for auth errors
 * @returns {Object} - API with error handling
 */
export const createApiWithErrorHandling = (api, showError, navigate) => {
  // Extract readable error message from backend response
  const getErrorMessage = (error) => {
    if (error.response) {
      // Server responded with a non-2xx status
      const { data, status } = error.response;
      
      // Handle authentication errors
      if (status === 401) {
        // Clear any stored auth data
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Redirect to login page
        if (navigate && window.location.pathname !== '/login') {
          navigate('/login');
        }
        
        return 'Your session has expired. Please log in again.';
      }
      
      // Parse error message from response data
      if (data) {
        if (typeof data === 'string') {
          return data;
        }
        
        if (data.detail) {
          if (typeof data.detail === 'string') {
            return data.detail;
          }
          
          if (Array.isArray(data.detail)) {
            return data.detail.map(err => err.msg).join(', ');
          }
        }
        
        if (data.message) {
          return data.message;
        }
      }
      
      // Default status-based messages
      switch (status) {
        case 400: return 'Invalid request';
        case 403: return 'You do not have permission to perform this action';
        case 404: return 'The requested resource was not found';
        case 500: return 'Server error. Please try again later.';
        default: return `Request failed with status code ${status}`;
      }
    }
    
    // Network errors
    if (error.request) {
      return 'Network error. Please check your connection.';
    }
    
    // Other errors
    return error.message || 'An unexpected error occurred';
  };
  
  // Create a wrapper for the API methods
  const withErrorHandling = async (apiCall, options = {}) => {
    const { 
      defaultErrorMsg = 'An error occurred', 
      showErrorToast = true 
    } = options;
    
    try {
      const response = await apiCall();
      return response.data;
    } catch (error) {
      const errorMessage = getErrorMessage(error) || defaultErrorMsg;
      console.error('API Error:', error, errorMessage);
      
      if (showErrorToast && showError) {
        showError(errorMessage);
      }
      
      throw {
        ...error,
        message: errorMessage
      };
    }
  };
  
  // Create wrapped API methods
  return {
    get: (url, params = {}, config = {}, options = {}) => {
      return withErrorHandling(
        () => api.get(url, { params, ...config }),
        options
      );
    },
    
    post: (url, data = {}, config = {}, options = {}) => {
      return withErrorHandling(
        () => api.post(url, data, config),
        options
      );
    },
    
    put: (url, data = {}, config = {}, options = {}) => {
      return withErrorHandling(
        () => api.put(url, data, config),
        options
      );
    },
    
    delete: (url, config = {}, options = {}) => {
      return withErrorHandling(
        () => api.delete(url, config),
        options
      );
    },
    
    // Allow access to the raw withErrorHandling function
    withErrorHandling,
    
    // Allow access to the underlying api instance
    getAxiosInstance: api.getAxiosInstance
  };
}; 