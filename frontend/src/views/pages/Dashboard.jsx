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
  useMediaQuery,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  VideoLibrary as VideoIcon,
  Upload as UploadIcon,
  Assessment as ScoutingIcon,
  PlayArrow as PlayIcon,
  Analytics as AnalyticsIcon,
  PictureAsPdf as PdfIcon,
  CloudUpload as CsvUploadIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getVideos } from '../../controllers/videoController';
import { getReports } from '../../controllers/scoutingController';

/**
 * Dashboard page component
 */
const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showError } = useToast();
  const [videos, setVideos] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Fetch videos and reports on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch videos
        await getVideos(
          (videos) => setVideos(videos),
          (error) => console.warn('Error fetching videos:', error)
        );

        // Fetch reports
        await getReports(
          (reports) => setReports(reports),
          (error) => console.warn('Error fetching reports:', error)
        );

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Safe array variables
  const safeVideos = Array.isArray(videos) ? videos : [];
  const safeReports = Array.isArray(reports) ? reports : [];

  // Calculate workflow progress
  const videosWithAnalysis = safeVideos.filter(v => v.status === 'completed');
  const completedReports = safeReports.filter(r => r.status === 'completed');

  // Workflow steps data
  const workflowSteps = [
    {
      label: 'Upload Videos',
      description: 'Upload basketball game videos for analysis',
      icon: <UploadIcon />,
      action: () => navigate('/upload'),
      buttonText: 'Upload Video',
      completed: safeVideos.length > 0,
      count: safeVideos.length,
      color: 'primary'
    },
    {
      label: 'Analyze Videos',
      description: 'AI-powered basketball analysis with player tracking',
      icon: <AnalyticsIcon />,
      action: () => navigate('/scouting'),
      buttonText: 'Start Analysis',
      completed: videosWithAnalysis.length > 0,
      count: videosWithAnalysis.length,
      color: 'secondary'
    },
    {
      label: 'Generate Reports',
      description: 'Create scouting reports from video analysis or CSV stats',
      icon: <ScoutingIcon />,
      action: () => navigate('/scouting/reports'),
      buttonText: 'Create Report',
      completed: completedReports.length > 0,
      count: completedReports.length,
      color: 'success'
    }
  ];

  // Quick action cards
  const quickActions = [
    {
      title: 'My Videos',
      description: `${safeVideos.length} video${safeVideos.length !== 1 ? 's' : ''} uploaded`,
      icon: <VideoIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      action: () => navigate('/videos'),
      buttonText: 'View All',
      count: safeVideos.length
    },
    {
      title: 'Scouting Reports',
      description: `${safeReports.length} report${safeReports.length !== 1 ? 's' : ''} created`,
      icon: <PdfIcon sx={{ fontSize: 40, color: 'success.main' }} />,
      action: () => navigate('/scouting/reports'),
      buttonText: 'View Reports',
      count: safeReports.length
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
          Basketball Analytics Dashboard
        </Typography>
        <Typography
          variant={isMobile ? "body1" : "subtitle1"}
          color="text.secondary"
        >
          Welcome back, {user?.username || 'User'}! Follow the workflow below to analyze your basketball videos.
        </Typography>
      </Box>

      {loading ? (
        <Loading />
      ) : (
        <>
          {/* Workflow Steps */}
          <Paper
            sx={{
              p: { xs: 2, sm: 3 },
              mb: { xs: 3, sm: 4 },
              borderRadius: { xs: 1, sm: 2 }
            }}
            elevation={isMobile ? 1 : 2}
          >
            <Typography
              variant={isMobile ? "h6" : "h5"}
              sx={{ mb: { xs: 2, sm: 3 }, fontWeight: 500 }}
            >
              Basketball Analysis Workflow
            </Typography>

            <Stepper
              orientation={isMobile ? "vertical" : "horizontal"}
              sx={{ mb: 2 }}
            >
              {workflowSteps.map((step, index) => (
                <Step key={step.label} completed={step.completed}>
                  <StepLabel
                    StepIconComponent={() => (
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: step.completed ? `${step.color}.main` : 'grey.300',
                          color: step.completed ? 'white' : 'grey.600'
                        }}
                      >
                        {step.icon}
                      </Box>
                    )}
                  >
                    <Box sx={{ ml: { xs: 0, sm: 1 } }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                        {step.label}
                        {step.count > 0 && (
                          <Chip
                            label={step.count}
                            size="small"
                            color={step.color}
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {step.description}
                      </Typography>
                    </Box>
                  </StepLabel>
                  {isMobile && (
                    <StepContent>
                      <Button
                        variant={step.completed ? "outlined" : "contained"}
                        color={step.color}
                        onClick={step.action}
                        size="small"
                        sx={{ mt: 1 }}
                      >
                        {step.buttonText}
                      </Button>
                    </StepContent>
                  )}
                </Step>
              ))}
            </Stepper>

            {!isMobile && (
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 3 }}>
                {workflowSteps.map((step, index) => (
                  <Button
                    key={step.label}
                    variant={step.completed ? "outlined" : "contained"}
                    color={step.color}
                    onClick={step.action}
                    size="medium"
                    startIcon={step.icon}
                  >
                    {step.buttonText}
                  </Button>
                ))}
              </Box>
            )}
          </Paper>

          {/* Quick Stats */}
          <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
            {quickActions.map((action) => (
              <Grid item xs={12} sm={6} key={action.title}>
                <Card
                  sx={{
                    p: { xs: 2, sm: 3 },
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4
                    },
                    borderRadius: { xs: 1, sm: 2 }
                  }}
                  onClick={action.action}
                  elevation={isMobile ? 1 : 2}
                >
                  <Box sx={{ mr: 2 }}>
                    {action.icon}
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      {action.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {action.description}
                    </Typography>
                  </Box>
                  <Button
                    variant="outlined"
                    size={isMobile ? "small" : "medium"}
                    onClick={(e) => {
                      e.stopPropagation();
                      action.action();
                    }}
                  >
                    {action.buttonText}
                  </Button>
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
              {safeVideos.length > 0 ? (
                <Grid container spacing={{ xs: 1, sm: 2 }}>
                  {safeVideos.slice(0, isTablet ? 2 : 3).map((video) => (
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
                          {/* Status indicator */}
                          <Box
                            sx={{
                              position: 'absolute',
                              top: 8,
                              right: 8,
                              zIndex: 1
                            }}
                          >
                            <Chip
                              label={video.status === 'completed' ? 'Ready' : 'Processing'}
                              size="small"
                              color={video.status === 'completed' ? 'success' : 'warning'}
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </Box>
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
                  <UploadIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography
                    variant={isMobile ? "body2" : "body1"}
                    color="text.secondary"
                    gutterBottom
                  >
                    Start your basketball analysis journey
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 2 }}
                  >
                    Upload your first basketball video to begin
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
        </>
      )}
    </Container>
  );
};

export default Dashboard;
