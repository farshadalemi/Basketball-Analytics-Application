/**
 * User Controller
 * Handles user-related operations between views and services
 */
import axios from 'axios';
import { ENDPOINTS } from '../config/api';

/**
 * Get current user profile
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getUserProfile = async (onSuccess, onError) => {
  try {
    // Add self=true parameter to handle legacy API requirements
    const response = await axios.get(`${ENDPOINTS.USERS.PROFILE}?self=true`);

    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch user profile');
    }
  } catch (error) {
    console.error('Error fetching user profile:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch user profile';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Update user profile
 * @param {Object} userData - User data to update
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const updateUserProfile = async (userData, onSuccess, onError) => {
  try {
    // Validate required fields
    if (!userData) {
      const errorMessage = 'No user data provided';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Add self=true parameter to handle legacy API requirements
    const response = await axios.put(`${ENDPOINTS.USERS.UPDATE}?self=true`, userData);

    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to update user profile');
    }
  } catch (error) {
    console.error('Error updating user profile:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to update user profile';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get user by ID (admin only)
 * @param {number} userId - User ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getUserById = async (userId, onSuccess, onError) => {
  try {
    const response = await axios.get(`${ENDPOINTS.USERS.LIST}/${userId}`);

    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch user');
    }
  } catch (error) {
    console.error(`Error fetching user ${userId}:`, error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch user';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get all users (admin only)
 * @param {Object} options - Query options (skip, limit)
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getUsers = async (options = {}, onSuccess, onError) => {
  try {
    const { skip = 0, limit = 100 } = options;
    const response = await axios.get(`${ENDPOINTS.USERS.LIST}?skip=${skip}&limit=${limit}`);

    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch users');
    }
  } catch (error) {
    console.error('Error fetching users:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch users';

    if (onError) onError(errorMessage);
    throw error;
  }
};
