import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Chip,
  Tooltip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
} from '@mui/material';
import {
  Search as SearchIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle as CompletedIcon,
  Pending as ProcessingIcon,
  Error as FailedIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';

import { useAuth } from '../../../context/AuthContext';
import { useToast } from '../../../context/ToastContext';
import { getAllVideos, deleteVideo } from '../../../controllers/adminController';

// Format date helper
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a');
  } catch (error) {
    return dateString;
  }
};

// Video Management Page
const VideoManagement = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();

  const [loading, setLoading] = useState(true);
  const [videos, setVideos] = useState([]);
  const [filteredVideos, setFilteredVideos] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Dialog states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);

  // Check if user is admin
  useEffect(() => {
    if (isAuthenticated && user && !user.is_admin) {
      showError('You do not have permission to access the admin panel');
      navigate('/');
    }
  }, [isAuthenticated, user, navigate, showError]);

  // Load videos
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        setLoading(true);
        const data = await getAllVideos();
        setVideos(data);
        setFilteredVideos(data);
      } catch (error) {
        console.error('Error loading videos:', error);
        showError('Failed to load videos');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated && user?.is_admin) {
      fetchVideos();
    }
  }, [isAuthenticated, user, showError]);

  // Filter videos based on search query and status filter
  useEffect(() => {
    let filtered = [...videos];

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(video => video.processing_status === statusFilter);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        video =>
          video.title.toLowerCase().includes(query) ||
          video.username.toLowerCase().includes(query)
      );
    }

    setFilteredVideos(filtered);
  }, [searchQuery, statusFilter, videos]);

  // Handle search input change
  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  // Handle status filter change
  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
  };

  // Handle video deletion
  const handleDeleteClick = (video) => {
    setSelectedVideo(video);
    setDeleteDialogOpen(true);
  };

  // Handle video view
  const handleViewClick = (video) => {
    navigate(`/videos/${video.id}`);
  };

  // Confirm video deletion
  const confirmDelete = async () => {
    if (!selectedVideo) return;

    try {
      await deleteVideo(
        selectedVideo.id,
        () => {
          showSuccess(`Video "${selectedVideo.title}" has been deleted`);
          // Update local state
          setVideos(videos.filter(v => v.id !== selectedVideo.id));
          setFilteredVideos(filteredVideos.filter(v => v.id !== selectedVideo.id));
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error deleting video:', error);
    } finally {
      setDeleteDialogOpen(false);
      setSelectedVideo(null);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Video Management
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/admin')}
        >
          Back to Dashboard
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search videos by title or username..."
              value={searchQuery}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                label="Status"
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Videos Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredVideos.length > 0 ? (
              filteredVideos.map((video) => (
                <TableRow key={video.id}>
                  <TableCell>{video.id}</TableCell>
                  <TableCell>{video.title}</TableCell>
                  <TableCell>{video.username}</TableCell>
                  <TableCell>
                    {video.processing_status === 'completed' ? (
                      <Chip
                        icon={<CompletedIcon />}
                        label="Completed"
                        color="success"
                        size="small"
                      />
                    ) : video.processing_status === 'processing' ? (
                      <Chip
                        icon={<ProcessingIcon />}
                        label="Processing"
                        color="warning"
                        size="small"
                      />
                    ) : (
                      <Chip
                        icon={<FailedIcon />}
                        label="Failed"
                        color="error"
                        size="small"
                      />
                    )}
                  </TableCell>
                  <TableCell>{formatDate(video.created_at)}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Video">
                      <IconButton
                        color="primary"
                        onClick={() => handleViewClick(video)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Delete Video">
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteClick(video)}
                        disabled={video.id === selectedVideo?.id}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No videos found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Video</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{selectedVideo?.title}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default VideoManagement;
