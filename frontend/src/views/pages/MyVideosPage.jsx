import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Import all required Material-UI components
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import useTheme from '@mui/material/styles/useTheme';
import useMediaQuery from '@mui/material/useMediaQuery';
import Chip from '@mui/material/Chip';

// Import all required Material-UI icons
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import FolderIcon from '@mui/icons-material/Folder';
import LabelIcon from '@mui/icons-material/Label';
import FilterListIcon from '@mui/icons-material/FilterList';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import VideoCard from '../components/video/VideoCard';
import { getVideos, deleteVideo } from '../../controllers/videoController';

/**
 * My Videos page component
 */
const MyVideosPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [videos, setVideos] = useState([]);
  const [filteredVideos, setFilteredVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState('All');
  const [selectedTags, setSelectedTags] = useState([]);
  const [availableFolders, setAvailableFolders] = useState(['All', 'Uncategorized']);
  const [availableTags, setAvailableTags] = useState([]);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Fetch videos on mount
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        setLoading(true);
        await getVideos(
          (videosData) => {
            setVideos(videosData);
            setFilteredVideos(videosData);
          },
          (error) => showError(error)
        );
      } catch (error) {
        console.error('Error fetching videos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Extract available folders and tags from videos
  useEffect(() => {
    if (!videos || videos.length === 0) return;

    // Extract unique folders
    const folders = ['All', ...new Set(videos.map(video => video.folder || 'Uncategorized'))];
    setAvailableFolders(folders);

    // Extract unique tags
    const tags = [...new Set(videos.flatMap(video => video.tags || []))];
    setAvailableTags(tags);
  }, [videos]);

  // Filter videos when search query, folder, or tags change
  useEffect(() => {
    if (!videos) return;

    let filtered = [...videos];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(video =>
        video.title.toLowerCase().includes(query) ||
        (video.description && video.description.toLowerCase().includes(query))
      );
    }

    // Filter by folder
    if (selectedFolder && selectedFolder !== 'All') {
      filtered = filtered.filter(video =>
        (video.folder || 'Uncategorized') === selectedFolder
      );
    }

    // Filter by tags
    if (selectedTags.length > 0) {
      filtered = filtered.filter(video => {
        const videoTags = video.tags || [];
        return selectedTags.every(tag => videoTags.includes(tag));
      });
    }

    setFilteredVideos(filtered);
  }, [searchQuery, selectedFolder, selectedTags, videos]);

  // Handle delete
  const handleDeleteClick = (videoId) => {
    const video = videos.find(v => v.id === videoId);
    if (video) {
      setVideoToDelete(video);
      setDeleteDialogOpen(true);
    }
  };

  const confirmDelete = async () => {
    if (!videoToDelete) return;

    try {
      await deleteVideo(
        videoToDelete.id,
        () => {
          // Update local state
          setVideos(videos.filter(v => v.id !== videoToDelete.id));
          setFilteredVideos(filteredVideos.filter(v => v.id !== videoToDelete.id));

          showSuccess('Video deleted successfully');
          setDeleteDialogOpen(false);
          setVideoToDelete(null);
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error deleting video:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: { xs: 2, sm: 3 },
          flexWrap: 'wrap',
          gap: { xs: 1, sm: 0 }
        }}>
          <Typography
            variant={isMobile ? "h5" : "h4"}
            component="h1"
            sx={{ fontWeight: 'bold' }}
          >
            My Videos
          </Typography>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/upload')}
            size={isMobile ? "small" : "medium"}
            sx={{
              py: { xs: 0.5, sm: 1 },
              px: { xs: 1.5, sm: 2 }
            }}
          >
            Upload New
          </Button>
        </Box>

        {/* Search and filter */}
        <Paper
          sx={{
            p: { xs: 1.5, sm: 2 },
            mb: { xs: 2, sm: 3 },
            borderRadius: { xs: 1, sm: 2 }
          }}
          elevation={isMobile ? 1 : 3}
        >
          <Grid container spacing={{ xs: 1, sm: 2 }} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search videos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                size={isMobile ? "small" : "medium"}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize={isMobile ? "small" : "medium"} />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{
                display: 'flex',
                justifyContent: { xs: 'flex-start', md: 'flex-end' },
                alignItems: 'center',
                mt: { xs: 0.5, md: 0 },
                gap: 1
              }}>
                {/* Filter button */}
                <Button
                  variant="outlined"
                  startIcon={<FilterListIcon />}
                  onClick={() => setFilterMenuOpen(!filterMenuOpen)}
                  size={isMobile ? "small" : "medium"}
                  sx={{ mr: 1 }}
                >
                  Filter
                </Button>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  {filteredVideos.length} video{filteredVideos.length !== 1 ? 's' : ''} found
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Filter options */}
          {filterMenuOpen && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Grid container spacing={2}>
                {/* Folder filter */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <FolderIcon fontSize="small" sx={{ mr: 1 }} /> Filter by Folder
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {availableFolders.map(folder => (
                      <Chip
                        key={folder}
                        label={folder}
                        onClick={() => setSelectedFolder(folder)}
                        color={selectedFolder === folder ? 'primary' : 'default'}
                        variant={selectedFolder === folder ? 'filled' : 'outlined'}
                        size="small"
                      />
                    ))}
                  </Box>
                </Grid>

                {/* Tags filter */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <LabelIcon fontSize="small" sx={{ mr: 1 }} /> Filter by Tags
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {availableTags.length > 0 ? (
                      availableTags.map(tag => (
                        <Chip
                          key={tag}
                          label={tag}
                          onClick={() => {
                            if (selectedTags.includes(tag)) {
                              setSelectedTags(selectedTags.filter(t => t !== tag));
                            } else {
                              setSelectedTags([...selectedTags, tag]);
                            }
                          }}
                          color={selectedTags.includes(tag) ? 'primary' : 'default'}
                          variant={selectedTags.includes(tag) ? 'filled' : 'outlined'}
                          size="small"
                        />
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No tags available
                      </Typography>
                    )}
                  </Box>
                </Grid>

                {/* Clear filters button */}
                {(selectedFolder !== 'All' || selectedTags.length > 0) && (
                  <Grid item xs={12}>
                    <Button
                      variant="text"
                      onClick={() => {
                        setSelectedFolder('All');
                        setSelectedTags([]);
                      }}
                      size="small"
                    >
                      Clear Filters
                    </Button>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </Paper>
      </Box>

      {/* Videos grid */}
      {loading ? (
        <Loading message="Loading videos..." />
      ) : filteredVideos.length > 0 ? (
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          {filteredVideos.map((video) => (
            <Grid item xs={12} sm={6} md={4} key={video.id}>
              <VideoCard
                video={video}
                onDelete={handleDeleteClick}
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper
          sx={{
            p: { xs: 3, sm: 4 },
            textAlign: 'center',
            borderRadius: { xs: 1, sm: 2 }
          }}
          elevation={isMobile ? 1 : 3}
        >
          {searchQuery ? (
            <>
              <Typography
                variant={isMobile ? "subtitle1" : "h6"}
                gutterBottom
                sx={{ fontWeight: 500 }}
              >
                No videos match your search
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                paragraph
                sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
              >
                Try different keywords or clear your search
              </Typography>
              <Button
                variant="outlined"
                onClick={() => setSearchQuery('')}
                size={isMobile ? "small" : "medium"}
                sx={{
                  py: { xs: 0.5, sm: 1 },
                  px: { xs: 1.5, sm: 2 }
                }}
              >
                Clear Search
              </Button>
            </>
          ) : (
            <>
              <Typography
                variant={isMobile ? "subtitle1" : "h6"}
                gutterBottom
                sx={{ fontWeight: 500 }}
              >
                You haven't uploaded any videos yet
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                paragraph
                sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
              >
                Upload your first video to get started
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => navigate('/upload')}
                size={isMobile ? "small" : "medium"}
                sx={{
                  py: { xs: 0.5, sm: 1 },
                  px: { xs: 1.5, sm: 2 }
                }}
              >
                Upload Video
              </Button>
            </>
          )}
        </Paper>
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
      >
        <DialogTitle sx={{
          fontSize: { xs: '1.1rem', sm: '1.25rem' },
          pb: { xs: 1, sm: 2 }
        }}>
          Delete Video
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            Are you sure you want to delete "{videoToDelete?.title}"? This action cannot be undone.
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
            onClick={confirmDelete}
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

export default MyVideosPage;
