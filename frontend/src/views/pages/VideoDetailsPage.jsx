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
  Folder as FolderIcon
} from '@mui/icons-material';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import BasicVideoPlayer from '../components/video/BasicVideoPlayer';
import { ENDPOINTS } from '../../config/api';
import VideoTagsEditor from '../components/video/VideoTagsEditor';
import { getVideoById, deleteVideo, getVideos, updateVideo, getVideoStreamingUrl } from '../../controllers/videoController';
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

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  // We only need isMobile for responsive design

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
