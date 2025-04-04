/**
 * Video Controller
 * Handles video-related logic between views and services
 */
import axios from 'axios';
import { formatVideoData, formatVideoList } from '../models/video';
import { getUserFromStorage } from '../models/auth';
import { ENDPOINTS } from '../config/api';

/**
 * Get all videos for the current user
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getVideos = async (onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Set authorization header
    const response = await axios.get(`${ENDPOINTS.VIDEOS.LIST}?self=true`, {
      headers: {
        'Authorization': `Bearer ${userData.token}`
      }
    });

    const formattedVideos = formatVideoList(response.data);

    if (onSuccess) onSuccess(formattedVideos);
    return formattedVideos;
  } catch (error) {
    console.error('Failed to fetch videos:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch videos';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get video by ID
 * @param {number|string} videoId - Video ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getVideoById = async (videoId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.get(`${ENDPOINTS.VIDEOS.DETAILS(videoId)}?self=true`, {
      headers: {
        'Authorization': `Bearer ${userData.token}`
      }
    });

    const formattedVideo = formatVideoData(response.data);

    if (onSuccess) onSuccess(formattedVideo);
    return formattedVideo;
  } catch (error) {
    console.error(`Failed to fetch video ${videoId}:`, error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to fetch video details';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Upload new video
 * @param {Object} videoData - Video data
 * @param {File} videoData.file - Video file
 * @param {string} videoData.title - Video title
 * @param {string} videoData.description - Video description
 * @param {Function} onProgress - Progress callback
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const uploadVideo = async (videoData, onProgress, onSuccess, onError) => {
  try {
    // Validate video data
    if (!videoData.file) {
      const errorMessage = 'Please select a video file';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    if (!videoData.title) {
      const errorMessage = 'Please enter a title for the video';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Create form data
    const formData = new FormData();
    formData.append('file', videoData.file);
    formData.append('title', videoData.title);

    if (videoData.description) {
      formData.append('description', videoData.description);
    }

    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Upload video
    const response = await axios.post(`${ENDPOINTS.VIDEOS.UPLOAD}?self=true`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${userData.token}`
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );

        if (onProgress) onProgress(percentCompleted);
      }
    });

    const uploadedVideo = formatVideoData(response.data);

    if (onSuccess) onSuccess(uploadedVideo);
    return uploadedVideo;
  } catch (error) {
    console.error('Failed to upload video:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to upload video';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get video streaming URL
 * @param {number|string} videoId - Video ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getVideoStreamingUrl = async (videoId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Make a request to get the streaming URL
    const response = await axios.get(`${ENDPOINTS.VIDEOS.STREAM(videoId)}?self=true`, {
      headers: {
        'Authorization': `Bearer ${userData.token}`
      }
    });

    // Check if we got a streaming URL in the response
    if (response.data && response.data.streaming_url) {
      const streamingUrl = response.data.streaming_url;
      console.log('Got streaming URL from backend:', streamingUrl);
      if (onSuccess) onSuccess(streamingUrl);
      return streamingUrl;
    } else {
      // If we got a direct response with no streaming_url, it means the backend is streaming the video directly
      // In this case, we'll use the endpoint URL directly
      const streamingUrl = `${ENDPOINTS.VIDEOS.STREAM(videoId)}?self=true`;
      console.log('Using direct streaming endpoint:', streamingUrl);
      if (onSuccess) onSuccess(streamingUrl);
      return streamingUrl;
    }
  } catch (error) {
    console.error(`Failed to get streaming URL for video ${videoId}:`, error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to get streaming URL';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Delete video
 * @param {number|string} videoId - Video ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deleteVideo = async (videoId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    await axios.delete(`${ENDPOINTS.VIDEOS.DETAILS(videoId)}?self=true`, {
      headers: {
        'Authorization': `Bearer ${userData.token}`
      }
    });

    if (onSuccess) onSuccess(videoId);
    return videoId;
  } catch (error) {
    console.error(`Failed to delete video ${videoId}:`, error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to delete video';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Update video metadata
 * @param {Object} videoData - Updated video data
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const updateVideo = async (videoData, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // For now, we'll store the tags, color, and folder in localStorage
    // since the backend doesn't support these features yet
    const storageKey = `video_metadata_${videoData.id}`;
    localStorage.setItem(storageKey, JSON.stringify({
      tags: videoData.tags || [],
      color: videoData.color || '',
      folder: videoData.folder || 'Uncategorized'
    }));

    // In a real implementation, we would send this to the backend
    // const response = await axios.patch(`${ENDPOINTS.VIDEOS.DETAILS(videoData.id)}?self=true`, {
    //   tags: videoData.tags,
    //   color: videoData.color,
    //   folder: videoData.folder
    // }, {
    //   headers: {
    //     'Authorization': `Bearer ${userData.token}`,
    //     'Content-Type': 'application/json'
    //   }
    // });

    if (onSuccess) onSuccess(videoData);
    return videoData;
  } catch (error) {
    console.error('Failed to update video:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to update video';

    if (onError) onError(errorMessage);
    throw error;
  }
};
