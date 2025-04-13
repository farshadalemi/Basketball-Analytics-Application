/**
 * Scouting controller
 * Handles API calls for scouting reports
 */
import { fetchWithAuth } from '../utils/fetchInterceptor';

/**
 * Get all reports for the current user
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getReports = async (onSuccess, onError) => {
  try {
    const response = await fetchWithAuth(`${process.env.REACT_APP_SCOUTING_API_URL}/reports`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch reports');
    }

    if (data.status === 'success' && data.data) {
      onSuccess(data.data);
    } else {
      onError(data.message || 'Failed to fetch reports');
    }
  } catch (error) {
    console.error('Error fetching reports:', error);
    onError(error.message);
  }
};

/**
 * Get a report by ID
 * @param {number} reportId - Report ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const getReportById = async (reportId, onSuccess, onError) => {
  try {
    const response = await fetchWithAuth(`${process.env.REACT_APP_SCOUTING_API_URL}/reports/${reportId}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to fetch report');
    }

    if (data.status === 'success' && data.data) {
      onSuccess(data.data);
    } else {
      onError(data.message || 'Failed to fetch report');
    }
  } catch (error) {
    console.error('Error fetching report:', error);
    onError(error.message);
  }
};

/**
 * Create a new report
 * @param {Object} reportData - Report data
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const createReport = async (reportData, onSuccess, onError) => {
  try {
    const response = await fetchWithAuth(
      `${process.env.REACT_APP_SCOUTING_API_URL}/reports`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      }
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to create report');
    }

    if (data.status === 'success') {
      onSuccess(data.data);
    } else {
      onError(data.message || 'Failed to create report');
    }
  } catch (error) {
    console.error('Error creating report:', error);
    onError(error.message);
  }
};

/**
 * Delete a report
 * @param {number} reportId - Report ID
 * @param {Function} onSuccess - Success callback
 * @param {Function} onError - Error callback
 */
export const deleteReport = async (reportId, onSuccess, onError) => {
  try {
    const response = await fetchWithAuth(
      `${process.env.REACT_APP_SCOUTING_API_URL}/reports/${reportId}`,
      {
        method: 'DELETE',
      }
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to delete report');
    }

    if (data.status === 'success') {
      onSuccess();
    } else {
      onError(data.message || 'Failed to delete report');
    }
  } catch (error) {
    console.error('Error deleting report:', error);
    onError(error.message);
  }
};
