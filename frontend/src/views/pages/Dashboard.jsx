import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  Container,
  Grid,
  Typography,
  Paper,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  VideoLibrary as VideoIcon,
  Upload as UploadIcon,
  BarChart as AnalyticsIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getVideos } from '../../controllers/videoController';

/**
 * Dashboard page component
 */
const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showError } = useToast();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Fetch videos on mount
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        setLoading(true);
        await getVideos(
          (videos) => setVideos(videos),
          (error) => showError(error)
        );
        setLoading(false);
      } catch (error) {
        console.error('Error fetching videos:', error);
        setLoading(false);
      }
    };

    fetchVideos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Dashboard cards for quick navigation
  const dashboardItems = [
    {
      title: 'My Videos',
      description: `You have ${videos.length} video${videos.length !== 1 ? 's' : ''}`,
      icon: <VideoIcon sx={{ fontSize: 60, color: 'primary.main' }} />,
      action: () => navigate('/videos'),
      buttonText: 'View Videos'
    },
    {
      title: 'Upload Video',
      description: 'Upload a new video for analysis',
      icon: <UploadIcon sx={{ fontSize: 60, color: 'secondary.main' }} />,
      action: () => navigate('/upload'),
      buttonText: 'Upload New'
    },
    {
      title: 'Analytics',
      description: 'View analytics and insights from your videos',
      icon: <AnalyticsIcon sx={{ fontSize: 60, color: 'success.main' }} />,
      action: () => navigate('/analytics'),
      buttonText: 'View Analytics',
      disabled: true
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Typography
          variant={isMobile ? "h5" : "h4"}
          component="h1"
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          Dashboard
        </Typography>
        <Typography
          variant={isMobile ? "body1" : "subtitle1"}
          color="text.secondary"
        >
          Welcome back, {user?.username || 'User'}!
        </Typography>
      </Box>

      <Divider sx={{ mb: { xs: 2, sm: 3, md: 4 } }} />

      {/* Quick Actions */}
      <Typography
        variant={isMobile ? "h6" : "h5"}
        sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 500 }}
      >
        Quick Actions
      </Typography>

      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 4, sm: 5, md: 6 } }}>
        {dashboardItems.map((item) => (
          <Grid item xs={12} sm={6} md={4} key={item.title}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                borderRadius: { xs: 1, sm: 2 },
                boxShadow: { xs: 1, sm: 2 }
              }}
              elevation={isMobile ? 1 : 2}
            >
              <Box sx={{
                p: { xs: 2, sm: 3 },
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center'
              }}>
                {item.icon}
                <Typography
                  variant={isMobile ? "subtitle1" : "h6"}
                  component="h2"
                  sx={{ mt: { xs: 1, sm: 2 }, fontWeight: 500 }}
                >
                  {item.title}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mt: { xs: 0.5, sm: 1 },
                    mb: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '0.8rem', sm: '0.875rem' }
                  }}
                >
                  {item.description}
                </Typography>
                <Button
                  variant="contained"
                  onClick={item.action}
                  disabled={item.disabled}
                  sx={{
                    mt: 'auto',
                    py: { xs: 0.5, sm: 1 },
                    px: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '0.8rem', sm: '0.875rem' }
                  }}
                  size={isMobile ? "small" : "medium"}
                >
                  {item.buttonText}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Videos */}
      <Box sx={{ mb: { xs: 3, sm: 4 } }}>
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: { xs: 1, sm: 2 },
          flexWrap: 'wrap',
          gap: 1
        }}>
          <Typography
            variant={isMobile ? "h6" : "h5"}
            sx={{ fontWeight: 500 }}
          >
            Recent Videos
          </Typography>
          <Button
            variant="outlined"
            onClick={() => navigate('/videos')}
            size={isMobile ? "small" : "medium"}
            sx={{
              py: { xs: 0.5, sm: 1 },
              px: { xs: 1.5, sm: 2 }
            }}
          >
            View All
          </Button>
        </Box>

        <Paper
          sx={{
            p: { xs: 2, sm: 3 },
            borderRadius: { xs: 1, sm: 2 }
          }}
          elevation={isMobile ? 1 : 2}
        >
          {loading ? (
            <Loading />
          ) : videos.length > 0 ? (
            <Grid container spacing={{ xs: 1, sm: 2 }}>
              {videos.slice(0, isTablet ? 2 : 3).map((video) => (
                <Grid item xs={12} sm={6} md={4} key={video.id}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4
                      },
                      borderRadius: { xs: 1, sm: 2 }
                    }}
                    onClick={() => navigate(`/videos/${video.id}`)}
                    elevation={isMobile ? 1 : 2}
                  >
                    <Box sx={{ position: 'relative', paddingTop: '56.25%', bgcolor: 'grey.200' }}>
                      {video.thumbnailUrl ? (
                        <Box
                          component="img"
                          src={video.thumbnailUrl}
                          alt={video.title}
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                          }}
                        />
                      ) : (
                        <Box
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <VideoIcon sx={{ fontSize: isMobile ? 30 : 40, color: 'text.secondary' }} />
                        </Box>
                      )}
                    </Box>
                    <Box sx={{ p: { xs: 1.5, sm: 2 } }}>
                      <Typography
                        variant={isMobile ? "body1" : "subtitle1"}
                        noWrap
                        sx={{ fontWeight: 500 }}
                      >
                        {video.title}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                      >
                        {new Date(video.createdAt).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box sx={{ py: { xs: 3, sm: 4 }, textAlign: 'center' }}>
              <Typography
                variant={isMobile ? "body2" : "body1"}
                color="text.secondary"
                gutterBottom
              >
                You haven't uploaded any videos yet
              </Typography>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => navigate('/upload')}
                sx={{ mt: { xs: 1.5, sm: 2 } }}
                size={isMobile ? "small" : "medium"}
              >
                Upload Your First Video
              </Button>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default Dashboard;
