import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  IconButton,
  Divider,
  useTheme,
  useMediaQuery,
  Alert,
  LinearProgress,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  VideoLibrary as VideoIcon,
  Assessment as ReportIcon,
  CheckCircle as CompleteIcon,
  Schedule as PendingIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getVideos } from '../../controllers/videoController';
import { getVideoAnalysisJobs, startVideoAnalysis } from '../../controllers/scoutingController';

/**
 * Video Analysis page - Shows videos with their analysis status
 */
const VideoAnalysisPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  const [videos, setVideos] = useState([]);
  const [videoAnalysisJobs, setVideoAnalysisJobs] = useState({});
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState({});

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Fetch videos and their analysis jobs
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch videos
        await getVideos(
          async (videosData) => {
            setVideos(videosData);
            
            // Fetch analysis jobs for each video
            const jobsData = {};
            for (const video of videosData) {
              try {
                await getVideoAnalysisJobs(
                  video.id,
                  (jobs) => {
                    jobsData[video.id] = jobs;
                  },
                  (error) => {
                    console.warn(`Could not load analysis jobs for video ${video.id}:`, error);
                    jobsData[video.id] = [];
                  }
                );
              } catch (error) {
                console.warn(`Error loading analysis jobs for video ${video.id}:`, error);
                jobsData[video.id] = [];
              }
            }
            setVideoAnalysisJobs(jobsData);
          },
          (error) => showError(error)
        );
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, [showError]);

  // Get latest analysis job for a video
  const getLatestAnalysisJob = (videoId) => {
    const jobs = videoAnalysisJobs[videoId] || [];
    return jobs.length > 0 ? jobs[0] : null;
  };

  // Get analysis status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  // Get analysis status text
  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Analysis Complete';
      case 'running':
        return 'Analyzing...';
      case 'pending':
        return 'Pending Analysis';
      case 'failed':
        return 'Analysis Failed';
      default:
        return 'Not Analyzed';
    }
  };

  // Start analysis for a video
  const handleStartAnalysis = async (video) => {
    if (analyzing[video.id]) return;

    setAnalyzing(prev => ({ ...prev, [video.id]: true }));
    
    try {
      await startVideoAnalysis(
        video.id,
        {},
        (result) => {
          showSuccess(`Analysis started for ${video.title}`);
          // Refresh the analysis jobs for this video
          getVideoAnalysisJobs(
            video.id,
            (jobs) => {
              setVideoAnalysisJobs(prev => ({
                ...prev,
                [video.id]: jobs
              }));
            },
            (error) => console.warn('Could not refresh analysis jobs:', error)
          );
        },
        (error) => showError(`Failed to start analysis: ${error}`)
      );
    } catch (error) {
      console.error('Error starting analysis:', error);
    } finally {
      setAnalyzing(prev => ({ ...prev, [video.id]: false }));
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    window.location.reload();
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Calculate analysis progress
  const safeVideos = Array.isArray(videos) ? videos : [];
  const totalVideos = safeVideos.length;
  const analyzedVideos = safeVideos.filter(v => {
    const latestJob = getLatestAnalysisJob(v.id);
    return latestJob && latestJob.status === 'completed';
  }).length;
  const processingVideos = safeVideos.filter(v => {
    const latestJob = getLatestAnalysisJob(v.id);
    return latestJob && latestJob.status === 'processing';
  }).length;

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography
            variant={isMobile ? "h5" : "h4"}
            component="h1"
            sx={{ fontWeight: 'bold' }}
          >
            Video Analysis
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              size={isMobile ? "small" : "medium"}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<ReportIcon />}
              onClick={() => navigate('/scouting/reports')}
              size={isMobile ? "small" : "medium"}
            >
              Create Reports
            </Button>
          </Box>
        </Box>
        <Typography
          variant={isMobile ? "body1" : "subtitle1"}
          color="text.secondary"
        >
          AI-powered basketball analysis with player tracking and tactical insights
        </Typography>
      </Box>

      {/* Analysis Progress Overview */}
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
          sx={{ mb: 2, fontWeight: 500 }}
        >
          Analysis Progress
        </Typography>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main" sx={{ fontWeight: 'bold' }}>
                {totalVideos}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Videos
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                {analyzedVideos}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analyzed
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main" sx={{ fontWeight: 'bold' }}>
                {processingVideos}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Processing
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {totalVideos > 0 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                Overall Progress
              </Typography>
              <Typography variant="body2">
                {Math.round((analyzedVideos / totalVideos) * 100)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(analyzedVideos / totalVideos) * 100}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        )}
      </Paper>

      <Divider sx={{ mb: { xs: 2, sm: 3, md: 4 } }} />

      {loading ? (
        <Loading message="Loading videos and analysis status..." />
      ) : safeVideos.length > 0 ? (
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          {safeVideos.map((video) => {
            const latestJob = getLatestAnalysisJob(video.id);
            const isAnalyzing = analyzing[video.id];
            const canAnalyze = video.status === 'completed';
            const hasAnalysis = latestJob && latestJob.status === 'completed';

            return (
              <Grid item xs={12} sm={6} md={4} key={video.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: { xs: 1, sm: 2 },
                    border: hasAnalysis ? '2px solid' : '1px solid',
                    borderColor: hasAnalysis ? 'success.main' : 'divider'
                  }}
                  elevation={isMobile ? 1 : 2}
                >
                  {/* Video thumbnail area */}
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
                        <VideoIcon sx={{ fontSize: 40, color: 'text.secondary' }} />
                      </Box>
                    )}

                    {/* Status overlay */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        zIndex: 1
                      }}
                    >
                      <Chip
                        icon={hasAnalysis ? <CompleteIcon /> : <PendingIcon />}
                        label={getStatusText(latestJob?.status)}
                        color={getStatusColor(latestJob?.status)}
                        size="small"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </Box>
                  </Box>

                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div" noWrap gutterBottom>
                      {video.title}
                    </Typography>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Uploaded: {new Date(video.createdAt).toLocaleDateString()}
                    </Typography>

                    {/* Analysis progress */}
                    {latestJob && latestJob.status === 'processing' && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Analysis in progress...
                        </Typography>
                        <LinearProgress sx={{ mt: 0.5 }} />
                      </Box>
                    )}

                    {/* Analysis results summary */}
                    {hasAnalysis && (
                      <Alert severity="success" sx={{ mb: 2 }}>
                        <Typography variant="caption">
                          Analysis completed! Ready for scouting reports.
                        </Typography>
                      </Alert>
                    )}

                    {!canAnalyze && (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        <Typography variant="caption">
                          Video processing required before analysis
                        </Typography>
                      </Alert>
                    )}

                    {latestJob && (
                      <Typography variant="caption" color="text.secondary">
                        Last analysis: {formatDate(latestJob.created_at)}
                      </Typography>
                    )}
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                    <Button
                      size="small"
                      startIcon={<PlayIcon />}
                      onClick={() => navigate(`/videos/${video.id}`)}
                      variant="outlined"
                    >
                      View Video
                    </Button>

                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {hasAnalysis ? (
                        <Button
                          size="small"
                          startIcon={<ReportIcon />}
                          onClick={() => navigate('/scouting/reports')}
                          variant="contained"
                          color="success"
                        >
                          Create Report
                        </Button>
                      ) : canAnalyze ? (
                        <Button
                          size="small"
                          startIcon={isAnalyzing ? <PendingIcon /> : <AnalyticsIcon />}
                          onClick={() => handleStartAnalysis(video)}
                          disabled={isAnalyzing || (latestJob && latestJob.status === 'processing')}
                          variant="contained"
                        >
                          {isAnalyzing ? 'Starting...' : 'Analyze'}
                        </Button>
                      ) : (
                        <Button
                          size="small"
                          disabled
                          variant="outlined"
                        >
                          Processing...
                        </Button>
                      )}

                      {latestJob?.status === 'completed' && latestJob.download_url && (
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => window.open(latestJob.download_url, '_blank')}
                          title="Download Analysis Video"
                        >
                          <DownloadIcon />
                        </IconButton>
                      )}
                    </Box>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        <Paper
          sx={{
            p: { xs: 3, sm: 4 },
            textAlign: 'center',
            borderRadius: { xs: 1, sm: 2 }
          }}
          elevation={isMobile ? 1 : 2}
        >
          <VideoIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          <Typography
            variant={isMobile ? "h6" : "h5"}
            gutterBottom
            sx={{ fontWeight: 500 }}
          >
            No Videos Available
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            Upload basketball videos to start AI-powered analysis
          </Typography>
          <Button
            variant="contained"
            startIcon={<VideoIcon />}
            onClick={() => navigate('/upload')}
            size={isMobile ? "small" : "medium"}
          >
            Upload Video
          </Button>
        </Paper>
      )}
    </Container>
  );
};

export default VideoAnalysisPage;
