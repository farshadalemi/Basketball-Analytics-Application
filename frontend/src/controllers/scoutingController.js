/**
 * Scouting controller
 * Handles API calls for basketball video analysis
 */
import axios from 'axios';
import { getUserFromStorage } from '../models/auth';
import { ENDPOINTS } from '../config/api';

/**
 * Start video analysis
 * @param {number} videoId - Video ID to analyze
 * @param {Object} analysisOptions - Analysis configuration options
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const startVideoAnalysis = async (videoId, analysisOptions, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.post(
      ENDPOINTS.SCOUTING.ANALYZE(videoId),
      analysisOptions || {},
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to start video analysis:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to start video analysis';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get analysis job status
 * @param {string} jobId - Analysis job ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getAnalysisStatus = async (jobId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.get(
      ENDPOINTS.SCOUTING.JOB_STATUS(jobId),
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to get analysis status:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to get analysis status';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get analysis result
 * @param {string} jobId - Analysis job ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getAnalysisResult = async (jobId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.get(
      ENDPOINTS.SCOUTING.JOB_RESULT(jobId),
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to get analysis result:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to get analysis result';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * List all analysis jobs
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const listAnalysisJobs = async (onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.get(
      ENDPOINTS.SCOUTING.JOBS,
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to list analysis jobs:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to list analysis jobs';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Delete analysis job
 * @param {string} jobId - Analysis job ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deleteAnalysisJob = async (jobId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.delete(
      ENDPOINTS.SCOUTING.DELETE_JOB(jobId),
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to delete analysis job:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to delete analysis job';

    if (onError) onError(errorMessage);
    throw error;
  }
};

// Alias for backward compatibility
export const deleteReport = deleteAnalysisJob;

/**
 * Get reports (alias for listAnalysisJobs)
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getReports = listAnalysisJobs;

/**
 * Upload CSV file for statistics-based scouting reports
 * @param {File} csvFile - CSV file to upload
 * @param {Function} onProgress - Progress callback
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const uploadCsvStats = async (csvFile, onProgress, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    // Create form data
    const formData = new FormData();
    formData.append('csv_file', csvFile);

    const response = await axios.post(
      `${ENDPOINTS.SCOUTING.BASE}/upload-csv`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          if (onProgress) onProgress(percentCompleted);
        }
      }
    );

    if (onSuccess) onSuccess(response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to upload CSV file:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to upload CSV file';

    if (onError) onError(errorMessage);
    throw error;
  }
};

/**
 * Get report by ID (alias for getAnalysisResult)
 * @param {string} reportId - Report/Job ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getReportById = getAnalysisResult;

/**
 * Create report (alias for startVideoAnalysis)
 * @param {number} videoId - Video ID to analyze
 * @param {Object} analysisOptions - Analysis configuration options
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const createReport = startVideoAnalysis;

/**
 * Get analysis jobs for a specific video
 * @param {number} videoId - Video ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getVideoAnalysisJobs = async (videoId, onSuccess, onError) => {
  try {
    // Get user token from storage
    const userData = getUserFromStorage();
    if (!userData || !userData.token) {
      const errorMessage = 'Authentication required';
      if (onError) onError(errorMessage);
      throw new Error(errorMessage);
    }

    const response = await axios.get(
      ENDPOINTS.SCOUTING.VIDEO_JOBS(videoId),
      {
        headers: {
          'Authorization': `Bearer ${userData.token}`
        }
      }
    );

    if (onSuccess) onSuccess(response.data.jobs);
    return response.data.jobs;
  } catch (error) {
    console.error('Failed to get video analysis jobs:', error);

    const errorMessage = error.response?.data?.detail ||
                         error.response?.data?.message ||
                         error.message ||
                         'Failed to get video analysis jobs';

    if (onError) onError(errorMessage);
    throw error;
  }
};
