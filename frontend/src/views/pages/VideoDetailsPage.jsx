import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Divider,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Share as ShareIcon,
  Folder as FolderIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import BasicVideoPlayer from '../components/video/BasicVideoPlayer';
import { ENDPOINTS } from '../../config/api';
import VideoTagsEditor from '../components/video/VideoTagsEditor';
import AnalysisResults from '../components/scouting/AnalysisResults';
import { getVideoById, deleteVideo, getVideos, updateVideo, getVideoStreamingUrl } from '../../controllers/videoController';
import { startVideoAnalysis, getAnalysisStatus, getVideoAnalysisJobs } from '../../controllers/scoutingController';
import { getVideoStatusText, isVideoReady } from '../../models/video';

/**
 * Video details page component
 */
const VideoDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [analysisJobId, setAnalysisJobId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisJobs, setAnalysisJobs] = useState([]);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  // We only need isMobile for responsive design

  // Load analysis jobs for the video
  const loadAnalysisJobs = async () => {
    if (!id) {
      console.warn('No video ID available for loading analysis jobs');
      return;
    }

    try {
      await getVideoAnalysisJobs(
        parseInt(id),
        (jobs) => {
          setAnalysisJobs(jobs);
          // If there's a recent job, set it as the current analysis
          if (jobs.length > 0) {
            const latestJob = jobs[0]; // Jobs are ordered by created_at desc
            setAnalysisJobId(latestJob.job_id);
            setAnalysisStatus(latestJob.status);

            // Only start polling if job is actually running/pending and job_id exists
            if (latestJob.job_id && (latestJob.status === 'running' || latestJob.status === 'pending')) {
              // First verify the job exists before starting polling
              getAnalysisStatus(
                latestJob.job_id,
                (statusData) => {
                  // Job exists, start polling
                  pollAnalysisStatus(latestJob.job_id);
                },
                (error) => {
                  console.warn('Job does not exist, not starting polling:', error);
                  setAnalysisJobId(null);
                  setAnalysisStatus(null);
                }
              );
            }
          }
        },
        (error) => {
          console.warn('Could not load analysis jobs:', error);
        }
      );
    } catch (error) {
      console.warn('Error loading analysis jobs:', error);
    }
  };

  // Fetch video on mount
  useEffect(() => {
    const fetchVideo = async () => {
      try {
        setLoading(true);

        // First try to get the video from the videos list
        try {
          await getVideos(
            (videos) => {
              const videoFromList = videos.find(v => v.id.toString() === id.toString());
              if (videoFromList) {
                setVideo(videoFromList);

                // We'll use the SimpleVideoPlayer component which handles authentication
                // and streaming directly, so we don't need to set the URL here
                console.log('Video details loaded, will use SimpleVideoPlayer for playback');
                setVideo(prev => ({
                  ...prev,
                  // Keep the existing properties
                }));

                setLoading(false);
              }
            },
            (error) => console.warn('Could not fetch videos list:', error)
          );
        } catch (listError) {
          console.warn('Could not fetch videos list:', listError);
        }

        // If we couldn't get it from the list, try the direct endpoint
        await getVideoById(
          id,
          (videoData) => {
            setVideo(videoData);

            // We'll use the SimpleVideoPlayer component which handles authentication
            // and streaming directly, so we don't need to set the URL here
            console.log('Video details loaded, will use SimpleVideoPlayer for playback');
            setVideo(prev => ({
              ...prev,
              // Keep the existing properties
            }));
          },
          (error) => {
            console.error('Error from getVideoById:', error);
            showError('Could not load video details. Please try again later.');
            // Don't navigate away, we'll show a fallback UI
          }
        );

        // Load analysis jobs after video is loaded
        await loadAnalysisJobs();
      } catch (error) {
        console.error('Error fetching video:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVideo();
  }, [id, navigate, showError]);

  // Handle delete
  const handleDelete = async () => {
    try {
      await deleteVideo(
        id,
        () => {
          showSuccess('Video deleted successfully');
          navigate('/videos');
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error deleting video:', error);
    }
  };

  // Handle analysis start
  const handleStartAnalysis = async () => {
    if (!video || !isVideoReady(video)) {
      showError('Video must be processed before analysis can begin');
      return;
    }

    setAnalysisLoading(true);
    try {
      await startVideoAnalysis(
        parseInt(id),
        {}, // Default analysis options
        (result) => {
          setAnalysisJobId(result.job_id);
          setAnalysisStatus('started');
          showSuccess('Basketball analysis started! Check back in a few minutes.');
          // Start polling for status
          pollAnalysisStatus(result.job_id);
        },
        (error) => {
          showError(`Failed to start analysis: ${error}`);
          setAnalysisLoading(false);
        }
      );
    } catch (error) {
      console.error('Error starting analysis:', error);
      setAnalysisLoading(false);
    }
  };

  // Poll analysis status
  const pollAnalysisStatus = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        await getAnalysisStatus(
          jobId,
          (statusData) => {
            setAnalysisStatus(statusData.status);

            if (statusData.status === 'completed') {
              clearInterval(pollInterval);
              setAnalysisLoading(false);
              showSuccess('Basketball analysis completed!');
            } else if (statusData.status === 'failed') {
              clearInterval(pollInterval);
              setAnalysisLoading(false);
              showError('Analysis failed. Please try again.');
            }
          },
          (error) => {
            console.error('Error polling analysis status:', error);
            // Stop polling on any error (including 404)
            clearInterval(pollInterval);
            setAnalysisLoading(false);
            setAnalysisJobId(null); // Clear the job ID to stop further attempts

            // Only show error if it's not a 404 (job not found)
            if (!error.includes('404') && !error.includes('Not Found')) {
              showError('Failed to get analysis status. Polling stopped.');
            }
          }
        );
      } catch (error) {
        console.error('Error in polling:', error);
        // Stop polling on any error
        clearInterval(pollInterval);
        setAnalysisLoading(false);
        setAnalysisJobId(null); // Clear the job ID to stop further attempts

        // Check if it's a 404 error
        if (error.response?.status === 404) {
          console.warn('Analysis job not found, stopping polling');
        } else {
          showError('Analysis polling failed. Please refresh the page.');
        }
      }
    }, 5000); // Poll every 5 seconds

    // Clear interval after 10 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
      if (analysisLoading) {
        setAnalysisLoading(false);
      }
    }, 600000);
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  // Get analysis status color
  const getAnalysisStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
      case 'started':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ my: 4 }}>
          <Loading message="Loading video details..." />
        </Box>
      </Container>
    );
  }

  if (!video) {
    return (
      <Container>
        <Box sx={{ my: 4 }}>
          <Typography variant="h5" color="error" gutterBottom>
            Video not found
          </Typography>
          <Button
            variant="contained"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/videos')}
          >
            Back to Videos
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/videos')}
          sx={{
            mb: { xs: 1.5, sm: 2 },
            py: { xs: 0.5, sm: 1 },
            px: { xs: 1.5, sm: 2 }
          }}
          size={isMobile ? "small" : "medium"}
        >
          Back to Videos
        </Button>

        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: { xs: 'center', sm: 'flex-start' },
          flexDirection: { xs: 'column', sm: 'row' },
          gap: { xs: 1, sm: 0 }
        }}>
          <Typography
            variant={isMobile ? "h5" : "h4"}
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 'bold',
              width: { xs: '100%', sm: 'auto' },
              mb: { xs: 0.5, sm: 1 }
            }}
          >
            {video.title}
          </Typography>

          <Box sx={{ alignSelf: { xs: 'flex-end', sm: 'auto' } }}>
            <IconButton
              color="secondary"
              onClick={handleStartAnalysis}
              disabled={!isVideoReady(video) || analysisLoading}
              size={isMobile ? "small" : "medium"}
              title="Start Basketball Analysis"
            >
              <AnalyticsIcon fontSize={isMobile ? "small" : "medium"} />
            </IconButton>
            <IconButton
              color="primary"
              disabled
              size={isMobile ? "small" : "medium"}
            >
              <ShareIcon fontSize={isMobile ? "small" : "medium"} />
            </IconButton>
            <IconButton
              color="primary"
              disabled
              size={isMobile ? "small" : "medium"}
            >
              <EditIcon fontSize={isMobile ? "small" : "medium"} />
            </IconButton>
            <IconButton
              color="error"
              onClick={() => setDeleteDialogOpen(true)}
              size={isMobile ? "small" : "medium"}
            >
              <DeleteIcon fontSize={isMobile ? "small" : "medium"} />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          mb: { xs: 1.5, sm: 2 },
          flexWrap: 'wrap',
          gap: 1
        }}>
          <Chip
            label={getVideoStatusText(video)}
            color={getStatusColor(video.processingStatus)}
            size="small"
            sx={{ mr: { xs: 1, sm: 2 } }}
          />
          {analysisStatus && (
            <Chip
              label={`Analysis: ${analysisStatus}`}
              color={getAnalysisStatusColor(analysisStatus)}
              size="small"
              sx={{ mr: { xs: 1, sm: 2 } }}
            />
          )}
          <Typography
            variant={isMobile ? "caption" : "body2"}
            color="text.secondary"
          >
            Uploaded on {formatDate(video.createdAt)}
          </Typography>
        </Box>
      </Box>

      {/* Video Player */}
      {isVideoReady(video) ? (
        <BasicVideoPlayer
          videoId={id}
          title={video.title}
        />
      ) : (
        <Paper
          elevation={isMobile ? 1 : 3}
          sx={{
            mb: { xs: 3, sm: 4 },
            borderRadius: { xs: 1, sm: 2 }
          }}
        >
          <Box
            sx={{
              paddingTop: '56.25%',
              bgcolor: 'grey.300',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography
              variant={isMobile ? "subtitle1" : "h6"}
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                color: 'text.secondary',
                textAlign: 'center',
                px: 2
              }}
            >
              {video.processingStatus === 'processing'
                ? 'Video is still processing...'
                : video.processingStatus === 'failed'
                ? 'Video processing failed'
                : 'Video Not Available'}
            </Typography>
          </Box>
        </Paper>
      )}

      {/* Video Details */}
      <Paper
        elevation={isMobile ? 1 : 3}
        sx={{
          p: { xs: 2, sm: 3 },
          mb: { xs: 3, sm: 4 },
          borderRadius: { xs: 1, sm: 2 }
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <Typography
            variant={isMobile ? "subtitle1" : "h6"}
            gutterBottom
            sx={{ fontWeight: 500 }}
          >
            Description
          </Typography>

          {/* Tags and organization */}
          {video.color && (
            <Box
              sx={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                bgcolor: video.color,
                display: 'inline-block',
                mr: 1
              }}
            />
          )}

          {video.folder && video.folder !== 'Uncategorized' && (
            <Chip
              icon={<FolderIcon />}
              label={video.folder}
              size="small"
              sx={{ mr: 1 }}
            />
          )}

          {video.tags && video.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
              {video.tags.map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          )}
        </Box>

        <Typography
          variant={isMobile ? "body2" : "body1"}
          paragraph
          sx={{
            whiteSpace: 'pre-line',
            fontSize: { xs: '0.875rem', sm: '1rem' }
          }}
        >
          {video.description || 'No description provided.'}
        </Typography>

        {/* Tags editor */}
        <VideoTagsEditor
          video={video}
          onSave={(updatedVideo) => {
            updateVideo(
              updatedVideo,
              (updated) => {
                setVideo(updated);
                showSuccess('Video details updated successfully');
              },
              (error) => showError(error)
            );
          }}
        />

        <Divider sx={{ my: { xs: 1.5, sm: 2 } }} />

        <Grid container spacing={{ xs: 1, sm: 2 }}>
          <Grid item xs={6} sm={6} md={3}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Duration
            </Typography>
            <Typography
              variant={isMobile ? "body2" : "body1"}
              sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
            >
              {video.duration ? `${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}` : 'Unknown'}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Status
            </Typography>
            <Typography
              variant={isMobile ? "body2" : "body1"}
              sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
            >
              {getVideoStatusText(video)}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Upload Date
            </Typography>
            <Typography
              variant={isMobile ? "body2" : "body1"}
              sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
            >
              {formatDate(video.createdAt)}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Video ID
            </Typography>
            <Typography
              variant={isMobile ? "body2" : "body1"}
              sx={{
                fontSize: { xs: '0.875rem', sm: '1rem' },
                wordBreak: 'break-all'
              }}
            >
              {video.id}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Analysis Results */}
      {analysisJobId && (
        <AnalysisResults
          jobId={analysisJobId}
          videoTitle={video.title}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        fullWidth
        maxWidth="xs"
        PaperProps={{
          sx: {
            borderRadius: { xs: 1, sm: 2 },
            p: { xs: 1, sm: 2 }
          }
        }}
        // Fix accessibility issues
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
        keepMounted
      >
        <DialogTitle
          id="delete-dialog-title"
          sx={{
            fontSize: { xs: '1.1rem', sm: '1.25rem' },
            pb: { xs: 1, sm: 2 }
          }}
        >
          Delete Video
        </DialogTitle>
        <DialogContent>
          <DialogContentText
            id="delete-dialog-description"
            sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
          >
            Are you sure you want to delete "{video.title}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ pt: { xs: 1, sm: 2 } }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            size={isMobile ? "small" : "medium"}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            color="error"
            variant="contained"
            size={isMobile ? "small" : "medium"}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default VideoDetailsPage;
