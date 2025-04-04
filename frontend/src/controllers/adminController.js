/**
 * Admin Controller
 * Handles admin-related operations between views and services
 */
import axios from 'axios';
import { ENDPOINTS } from '../config/api';

/**
 * Get system statistics
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getSystemStats = async (onSuccess, onError) => {
  try {
    const response = await axios.get(ENDPOINTS.ADMIN.STATS);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch system statistics');
    }
  } catch (error) {
    console.error('Error fetching system statistics:', error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch system statistics';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get user statistics
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getUserStats = async (onSuccess, onError) => {
  try {
    const response = await axios.get(ENDPOINTS.ADMIN.USER_STATS);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch user statistics');
    }
  } catch (error) {
    console.error('Error fetching user statistics:', error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch user statistics';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get storage statistics
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getStorageStats = async (onSuccess, onError) => {
  try {
    const response = await axios.get(ENDPOINTS.ADMIN.STORAGE_STATS);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch storage statistics');
    }
  } catch (error) {
    console.error('Error fetching storage statistics:', error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch storage statistics';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get all videos (admin only)
 * @param {Object} options - Query options (skip, limit, userId, status)
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getAllVideos = async (options = {}, onSuccess, onError) => {
  try {
    const { skip = 0, limit = 100, userId, status } = options;
    let url = `${ENDPOINTS.ADMIN.VIDEOS}?skip=${skip}&limit=${limit}`;
    
    if (userId) url += `&user_id=${userId}`;
    if (status) url += `&status=${status}`;
    
    const response = await axios.get(url);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to fetch videos');
    }
  } catch (error) {
    console.error('Error fetching videos:', error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch videos';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Delete a video (admin only)
 * @param {number} videoId - Video ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deleteVideo = async (videoId, onSuccess, onError) => {
  try {
    const response = await axios.delete(`${ENDPOINTS.ADMIN.VIDEOS}/${videoId}`);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to delete video');
    }
  } catch (error) {
    console.error(`Error deleting video ${videoId}:`, error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to delete video';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Activate a user (admin only)
 * @param {number} userId - User ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const activateUser = async (userId, onSuccess, onError) => {
  try {
    const response = await axios.put(`${ENDPOINTS.ADMIN.USERS}/${userId}/activate`);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to activate user');
    }
  } catch (error) {
    console.error(`Error activating user ${userId}:`, error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to activate user';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Deactivate a user (admin only)
 * @param {number} userId - User ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deactivateUser = async (userId, onSuccess, onError) => {
  try {
    const response = await axios.put(`${ENDPOINTS.ADMIN.USERS}/${userId}/deactivate`);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to deactivate user');
    }
  } catch (error) {
    console.error(`Error deactivating user ${userId}:`, error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to deactivate user';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Delete a user (admin only)
 * @param {number} userId - User ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deleteUser = async (userId, onSuccess, onError) => {
  try {
    const response = await axios.delete(`${ENDPOINTS.ADMIN.USERS}/${userId}`);
    
    if (response.data) {
      if (onSuccess) onSuccess(response.data);
      return response.data;
    } else {
      throw new Error('Failed to delete user');
    }
  } catch (error) {
    console.error(`Error deleting user ${userId}:`, error);
    
    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to delete user';
    
    if (onError) onError(errorMessage);
    throw error;
  }
};
