/**
 * Authentication Controller
 * Handles authentication logic between views and services
 */
import axios from 'axios';
import {
  getUserFromStorage,
  saveUserToStorage,
  removeUserFromStorage,
  formatUserData
} from '../models/auth';
import { validateRegistration } from '../models/user';
import { ENDPOINTS } from '../config/api';

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const login = async (email, password, onSuccess, onError) => {
  try {
    // Create URLSearchParams for proper form encoding
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 expects 'username'
    formData.append('password', password);

    console.log('Submitting login with:', { email, formData: formData.toString() });

    const response = await axios.post(ENDPOINTS.AUTH.LOGIN, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    if (response.data && response.data.access_token) {
      const userData = formatUserData(response.data);
      saveUserToStorage(userData);

      // Set auth header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`;

      if (onSuccess) onSuccess(userData);
      return userData;
    } else {
      throw new Error('Invalid response from server');
    }
  } catch (error) {
    console.error('Login failed:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Login failed. Please check your credentials.';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Register new user
 * @param {Object} userData - User registration data
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const register = async (userData, onSuccess, onError) => {
  try {
    // Validate registration data
    const validation = validateRegistration(userData);
    if (!validation.isValid) {
      const errorMessage = Object.values(validation.errors)[0];
      if (onError) onError(errorMessage);
      return;
    }

    const response = await axios.post(ENDPOINTS.AUTH.REGISTER, {
      email: userData.email,
      username: userData.username,
      password: userData.password
    });

    if (response.status === 200 || response.status === 201) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Registration failed');
    }
  } catch (error) {
    console.error('Registration failed:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Registration failed. Please try again.';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Logout user
 */
export const logout = () => {
  removeUserFromStorage();
  delete axios.defaults.headers.common['Authorization'];
};

/**
 * Check if user is authenticated
 * @returns {Object|null} User data if authenticated, null otherwise
 */
export const checkAuth = async () => {
  const userData = getUserFromStorage();

  if (!userData || !userData.token) {
    return null;
  }

  try {
    // Set auth header
    axios.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`;

    // Verify token with backend
    const response = await axios.get(ENDPOINTS.AUTH.ME);

    if (response.data) {
      return {
        ...userData,
        user: response.data
      };
    }

    return userData;
  } catch (error) {
    console.error('Auth check failed:', error);
    removeUserFromStorage();
    delete axios.defaults.headers.common['Authorization'];
    return null;
  }
};
