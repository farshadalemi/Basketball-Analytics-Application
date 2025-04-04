import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Grid,
  LinearProgress,
  IconButton,
  Divider,
  Alert,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Close as CloseIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useToast } from '../../context/ToastContext';
import { uploadVideo } from '../../controllers/videoController';

/**
 * Upload Video page component
 */
const UploadVideoPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState({});

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) {
      return;
    }

    // Validate file type
    const validTypes = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'];
    if (!validTypes.includes(selectedFile.type)) {
      showError('Please select a valid video file (MP4, WebM, OGG, MOV)');
      return;
    }

    // Validate file size (max 100MB)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (selectedFile.size > maxSize) {
      showError('File size exceeds 100MB limit');
      return;
    }

    setFile(selectedFile);

    // Create file preview URL
    const previewUrl = URL.createObjectURL(selectedFile);
    setFilePreview(previewUrl);

    // Clear error
    if (errors.file) {
      setErrors({
        ...errors,
        file: ''
      });
    }

    // Auto-fill title if empty
    if (!title) {
      // Remove extension from filename
      const fileName = selectedFile.name.replace(/\.[^/.]+$/, '');
      // Convert to title case
      const titleCase = fileName
        .replace(/[-_]/g, ' ')
        .replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());

      setTitle(titleCase);
    }
  };

  // Clear selected file
  const clearFile = () => {
    if (filePreview) {
      URL.revokeObjectURL(filePreview);
    }
    setFile(null);
    setFilePreview('');
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate form
    const newErrors = {};
    if (!title) newErrors.title = 'Title is required';
    if (!file) newErrors.file = 'Please select a video file';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Clear errors
    setErrors({});

    // Upload video
    try {
      setUploading(true);

      await uploadVideo(
        {
          file,
          title,
          description
        },
        (progress) => setUploadProgress(progress),
        (uploadedVideo) => {
          showSuccess('Video uploaded successfully');
          navigate(`/videos/${uploadedVideo.id}`);
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          sx={{
            mb: { xs: 1.5, sm: 2 },
            py: { xs: 0.5, sm: 1 },
            px: { xs: 1.5, sm: 2 }
          }}
          size={isMobile ? "small" : "medium"}
        >
          Back
        </Button>

        <Typography
          variant={isMobile ? "h5" : "h4"}
          component="h1"
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          Upload Video
        </Typography>
        <Typography
          variant={isMobile ? "body2" : "body1"}
          color="text.secondary"
          paragraph
          sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
        >
          Upload a video for analysis. Supported formats: MP4, WebM, OGG, MOV.
        </Typography>
      </Box>

      <Paper
        elevation={isMobile ? 1 : 3}
        sx={{
          p: { xs: 2, sm: 3 },
          borderRadius: { xs: 1, sm: 2 }
        }}
      >
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <Grid container spacing={{ xs: 2, sm: 3 }}>
            {/* File upload section */}
            <Grid item xs={12}>
              <Box
                sx={{
                  border: '2px dashed',
                  borderColor: errors.file ? 'error.main' : 'divider',
                  borderRadius: { xs: 1, sm: 2 },
                  p: { xs: 2, sm: 3 },
                  textAlign: 'center',
                  bgcolor: 'background.default',
                  position: 'relative'
                }}
              >
                {file ? (
                  <Box>
                    <Box sx={{ position: 'relative', mb: { xs: 1.5, sm: 2 } }}>
                      <Box
                        component="video"
                        src={filePreview}
                        controls
                        sx={{
                          maxHeight: { xs: 150, sm: 200 },
                          maxWidth: '100%'
                        }}
                      />
                      <IconButton
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: -8,
                          right: -8,
                          bgcolor: 'background.paper',
                          '&:hover': { bgcolor: 'background.default' }
                        }}
                        onClick={clearFile}
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Typography
                      variant={isMobile ? "caption" : "body2"}
                      sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                    >
                      {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                    </Typography>
                  </Box>
                ) : (
                  <Box>
                    <input
                      accept="video/*"
                      style={{ display: 'none' }}
                      id="video-upload"
                      type="file"
                      onChange={handleFileChange}
                      disabled={uploading}
                    />
                    <label htmlFor="video-upload">
                      <Button
                        variant="contained"
                        component="span"
                        startIcon={<UploadIcon />}
                        disabled={uploading}
                        size={isMobile ? "small" : "medium"}
                        sx={{
                          py: { xs: 0.5, sm: 1 },
                          px: { xs: 1.5, sm: 2 }
                        }}
                      >
                        Select Video
                      </Button>
                    </label>
                    <Typography
                      variant={isMobile ? "caption" : "body2"}
                      color="text.secondary"
                      sx={{
                        mt: { xs: 1.5, sm: 2 },
                        fontSize: { xs: '0.75rem', sm: '0.875rem' }
                      }}
                    >
                      Drag and drop a video file here, or click to select
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{
                        mt: { xs: 0.5, sm: 1 },
                        display: 'block',
                        fontSize: { xs: '0.7rem', sm: '0.75rem' }
                      }}
                    >
                      Maximum file size: 100MB
                    </Typography>
                  </Box>
                )}

                {errors.file && (
                  <Typography
                    color="error"
                    variant="caption"
                    sx={{
                      mt: { xs: 0.5, sm: 1 },
                      display: 'block',
                      fontSize: { xs: '0.7rem', sm: '0.75rem' }
                    }}
                  >
                    {errors.file}
                  </Typography>
                )}
              </Box>
            </Grid>

            {/* Video details section */}
            <Grid item xs={12}>
              <Divider sx={{ my: { xs: 1.5, sm: 2 } }} />
              <Typography
                variant={isMobile ? "subtitle1" : "h6"}
                gutterBottom
                sx={{ fontWeight: 500 }}
              >
                Video Details
              </Typography>

              <TextField
                margin="normal"
                required
                fullWidth
                id="title"
                label="Title"
                name="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                error={!!errors.title}
                helperText={errors.title}
                disabled={uploading}
                size={isMobile ? "small" : "medium"}
                sx={{ mt: { xs: 1, sm: 2 } }}
              />

              <TextField
                margin="normal"
                fullWidth
                id="description"
                label="Description"
                name="description"
                multiline
                rows={isMobile ? 3 : 4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
                size={isMobile ? "small" : "medium"}
                sx={{ mt: { xs: 1, sm: 2 } }}
              />
            </Grid>

            {/* Upload progress */}
            {uploading && (
              <Grid item xs={12}>
                <Box sx={{ mb: { xs: 1.5, sm: 2 } }}>
                  <Typography
                    variant={isMobile ? "caption" : "body2"}
                    color="text.secondary"
                    gutterBottom
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Uploading: {uploadProgress}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={uploadProgress}
                    sx={{ height: isMobile ? 4 : 6 }}
                  />
                </Box>
                <Alert
                  severity="info"
                  sx={{
                    py: { xs: 0.5, sm: 1 },
                    fontSize: { xs: '0.75rem', sm: '0.875rem' }
                  }}
                >
                  Please do not close this page while your video is uploading.
                </Alert>
              </Grid>
            )}

            {/* Submit button */}
            <Grid item xs={12}>
              <Box sx={{
                display: 'flex',
                justifyContent: 'flex-end',
                mt: { xs: 1.5, sm: 2 },
                gap: { xs: 1, sm: 2 }
              }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate(-1)}
                  disabled={uploading}
                  size={isMobile ? "small" : "medium"}
                  sx={{
                    py: { xs: 0.5, sm: 1 },
                    px: { xs: 1.5, sm: 2 }
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<UploadIcon />}
                  disabled={uploading || !file}
                  size={isMobile ? "small" : "medium"}
                  sx={{
                    py: { xs: 0.5, sm: 1 },
                    px: { xs: 1.5, sm: 2 }
                  }}
                >
                  {uploading ? 'Uploading...' : 'Upload Video'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Container>
  );
};

export default UploadVideoPage;
