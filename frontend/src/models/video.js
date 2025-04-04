/**
 * Video model
 * Handles video data and operations
 */
import { ENDPOINTS } from '../config/api';

/**
 * Format video data from API response
 * @param {Object} videoData - Raw video data from API
 * @returns {Object} Formatted video data
 */
export const formatVideoData = (videoData) => {
  if (!videoData) return null;

  // Determine the URL for the video
  let videoUrl = '';

  // Always use the streaming endpoint for consistency
  if (videoData.id) {
    videoUrl = `${ENDPOINTS.VIDEOS.STREAM(videoData.id)}?self=true`;
    console.log(`Using streaming endpoint for video ${videoData.id}: ${videoUrl}`);
  }
  // Fallback to streaming_url if provided
  else if (videoData.streaming_url) {
    videoUrl = videoData.streaming_url;
    console.log(`Using provided streaming URL: ${videoUrl}`);
  }

  // Check if we have metadata stored in localStorage
  let tags = [];
  let color = '';
  let folder = 'Uncategorized';

  try {
    const storageKey = `video_metadata_${videoData.id}`;
    const storedMetadata = localStorage.getItem(storageKey);

    if (storedMetadata) {
      const metadata = JSON.parse(storedMetadata);
      tags = metadata.tags || [];
      color = metadata.color || '';
      folder = metadata.folder || 'Uncategorized';
    }
  } catch (error) {
    console.warn('Failed to load video metadata from localStorage:', error);
  }

  return {
    id: videoData.id,
    title: videoData.title,
    description: videoData.description || '',
    url: videoUrl,
    file_path: videoData.file_path || '',
    thumbnail_url: videoData.thumbnail_url || null,
    createdAt: videoData.created_at ? new Date(videoData.created_at) : null,
    duration: videoData.duration || 0,
    processingStatus: videoData.processing_status || 'unknown',
    // Add tags and color properties with defaults or from localStorage
    tags: videoData.tags || tags,
    color: videoData.color || color,
    folder: videoData.folder || folder
  };
};

/**
 * Format video list from API response
 * @param {Array} videosData - Raw videos data from API
 * @returns {Array} Formatted videos data
 */
export const formatVideoList = (videosData) => {
  if (!videosData || !Array.isArray(videosData)) return [];

  return videosData.map(formatVideoData);
};

/**
 * Check if video is ready for playback
 * @param {Object} video - Video object
 * @returns {boolean} True if video is ready
 */
export const isVideoReady = (video) => {
  // Consider a video ready if it has an ID (we can always use the streaming endpoint)
  if (video && video.id) {
    // If the video is still processing, check the status
    if (video.processingStatus && video.processingStatus !== 'completed' && video.processingStatus !== 'unknown') {
      console.log(`Video ${video.id} is not ready: ${video.processingStatus}`);
      return false;
    }

    // If url is already set, use it
    if (video.url) {
      return true;
    }

    // Otherwise, we can always construct a URL from the ID
    video.url = `${ENDPOINTS.VIDEOS.STREAM(video.id)}?self=true`;
    console.log(`Constructed URL for video ${video.id}: ${video.url}`);
    return true;
  }

  return false;
};

/**
 * Get video processing status text
 * @param {Object} video - Video object
 * @returns {string} Status text
 */
export const getVideoStatusText = (video) => {
  if (!video) return 'Unknown';

  switch (video.processingStatus) {
    case 'queued':
      return 'Queued for processing';
    case 'processing':
      return 'Processing...';
    case 'completed':
      return 'Ready';
    case 'failed':
      return 'Processing failed';
    default:
      return 'Unknown status';
  }
};

/**
 * Format duration to human-readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration (e.g., "1:23")
 */
export const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00';

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};
