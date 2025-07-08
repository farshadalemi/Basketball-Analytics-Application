import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import {
  Download as DownloadIcon,
  PlayArrow as PlayIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { getAnalysisResult, getAnalysisStatus } from '../../../controllers/scoutingController';
import { useToast } from '../../../context/ToastContext';

/**
 * Analysis Results Component
 * Displays basketball analysis results and download options
 */
const AnalysisResults = ({ jobId, videoTitle }) => {
  const { showSuccess, showError } = useToast();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resultUrl, setResultUrl] = useState(null);

  useEffect(() => {
    if (jobId) {
      fetchAnalysisStatus();
    }
  }, [jobId]);

  const fetchAnalysisStatus = async () => {
    try {
      await getAnalysisStatus(
        jobId,
        (statusData) => {
          setStatus(statusData);
          if (statusData.status === 'completed') {
            fetchAnalysisResult();
          }
          setLoading(false);
        },
        (error) => {
          console.error('Error fetching analysis status:', error);
          // Check if it's a 404 error (job not found)
          if (error.includes('404') || error.includes('Not Found')) {
            setStatus({ status: 'not_found', message: 'Analysis job not found' });
          } else {
            showError(`Failed to get analysis status: ${error}`);
          }
          setLoading(false);
        }
      );
    } catch (error) {
      console.error('Error fetching analysis status:', error);
      // Check if it's a 404 error
      if (error.response?.status === 404) {
        setStatus({ status: 'not_found', message: 'Analysis job not found' });
      } else {
        showError('Failed to load analysis status');
      }
      setLoading(false);
    }
  };

  const fetchAnalysisResult = async () => {
    try {
      await getAnalysisResult(
        jobId,
        (resultData) => {
          setResultUrl(resultData.result_url);
        },
        (error) => {
          console.error('Error fetching analysis result:', error);
        }
      );
    } catch (error) {
      console.error('Error fetching analysis result:', error);
    }
  };

  const handleDownload = () => {
    if (resultUrl) {
      // Create a temporary link to download the file
      const link = document.createElement('a');
      link.href = resultUrl;
      link.download = `${videoTitle}_analysis.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showSuccess('Analysis video download started');
    }
  };

  const handlePreview = () => {
    if (resultUrl) {
      window.open(resultUrl, '_blank');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
      case 'started':
        return 'info';
      case 'failed':
        return 'error';
      case 'not_found':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Analysis Complete';
      case 'running':
        return 'Analyzing Video...';
      case 'started':
        return 'Analysis Started';
      case 'failed':
        return 'Analysis Failed';
      case 'not_found':
        return 'Job Not Found';
      default:
        return 'Unknown Status';
    }
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading analysis status...
        </Typography>
      </Paper>
    );
  }

  if (!status) {
    return (
      <Alert severity="error">
        Failed to load analysis status
      </Alert>
    );
  }

  // Special case for job not found
  if (status.status === 'not_found') {
    return (
      <Alert severity="warning" sx={{ mt: 3 }}>
        <Typography variant="h6" component="div" sx={{ mb: 1 }}>
          Analysis Job Not Found
        </Typography>
        <Typography variant="body2">
          The analysis job for this video could not be found. It may have been deleted or expired.
        </Typography>
      </Alert>
    );
  }

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h3">
            Basketball Analysis
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Chip
            label={getStatusText(status.status)}
            color={getStatusColor(status.status)}
            sx={{ mr: 1 }}
          />
          {status.progress !== undefined && status.status === 'running' && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Progress: {status.progress}%
            </Typography>
          )}
        </Box>

        {status.message && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {status.message}
          </Typography>
        )}

        {status.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {status.error}
          </Alert>
        )}

        {status.status === 'running' && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography variant="body2">
              Analysis in progress... This may take several minutes.
            </Typography>
          </Box>
        )}

        {status.status === 'completed' && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Alert severity="success" sx={{ mb: 2 }}>
                Analysis completed successfully! The video includes player tracking, 
                ball detection, tactical analysis, and performance metrics.
              </Alert>
            </Grid>
          </Grid>
        )}
      </CardContent>

      {status.status === 'completed' && resultUrl && (
        <CardActions>
          <Button
            startIcon={<PlayIcon />}
            onClick={handlePreview}
            variant="outlined"
            color="primary"
          >
            Preview
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
            variant="contained"
            color="primary"
          >
            Download Analysis
          </Button>
        </CardActions>
      )}
    </Card>
  );
};

export default AnalysisResults;
