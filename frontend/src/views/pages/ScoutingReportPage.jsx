import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Grid,
  Typography,
  Paper,
  Divider,
  useTheme,
  useMediaQuery,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress
} from '@mui/material';
import {
  Description as ReportIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getVideos } from '../../controllers/videoController';
import { getReports, createReport } from '../../controllers/scoutingController';
import ReportCard from '../components/scouting/ReportCard';

/**
 * Scouting Report page component
 */
const ScoutingReportPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  const [videos, setVideos] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [teamName, setTeamName] = useState('');
  const [opponentName, setOpponentName] = useState('');

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
          (videosData) => setVideos(videosData),
          (error) => showError(error)
        );
        
        // Fetch reports
        await getReports(
          (reportsData) => setReports(reportsData),
          (error) => showError(error)
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

  const handleCreateReport = async () => {
    if (!selectedVideo) {
      showError('Please select a video');
      return;
    }

    if (!reportTitle) {
      showError('Please enter a report title');
      return;
    }

    try {
      setCreating(true);
      
      const videoObj = videos.find(v => v.id === parseInt(selectedVideo));
      
      const reportData = {
        title: reportTitle,
        description: `Scouting report for ${teamName || 'opponent team'}`,
        video_id: parseInt(selectedVideo),
        video_title: videoObj ? videoObj.title : '',
        team_name: teamName,
        opponent_name: opponentName,
        user_id: user.id
      };
      
      await createReport(
        reportData,
        (response) => {
          showSuccess('Report creation initiated');
          // Refresh reports list
          getReports(
            (reportsData) => setReports(reportsData),
            (error) => showError(error)
          );
          // Reset form
          setSelectedVideo('');
          setReportTitle('');
          setTeamName('');
          setOpponentName('');
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error creating report:', error);
      showError('Failed to create report');
    } finally {
      setCreating(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setLoading(true);
      
      // Fetch reports
      await getReports(
        (reportsData) => setReports(reportsData),
        (error) => showError(error)
      );
      
      setLoading(false);
    } catch (error) {
      console.error('Error refreshing reports:', error);
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Typography
          variant={isMobile ? "h5" : "h4"}
          component="h1"
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          Scouting Reports
        </Typography>
        <Typography
          variant={isMobile ? "body1" : "subtitle1"}
          color="text.secondary"
        >
          Generate and manage scouting reports for opponent teams
        </Typography>
      </Box>

      <Divider sx={{ mb: { xs: 2, sm: 3, md: 4 } }} />

      {/* Create Report Form */}
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
          Create New Report
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="video-select-label">Select Video</InputLabel>
              <Select
                labelId="video-select-label"
                id="video-select"
                value={selectedVideo}
                label="Select Video"
                onChange={(e) => setSelectedVideo(e.target.value)}
                disabled={creating || videos.length === 0}
              >
                {videos.map((video) => (
                  <MenuItem key={video.id} value={video.id}>
                    {video.title}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Report Title"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              disabled={creating}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Team Name"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              disabled={creating}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Opponent Name"
              value={opponentName}
              onChange={(e) => setOpponentName(e.target.value)}
              disabled={creating}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              startIcon={creating ? <CircularProgress size={20} color="inherit" /> : <AddIcon />}
              onClick={handleCreateReport}
              disabled={creating || !selectedVideo || !reportTitle}
              sx={{ mt: 1 }}
            >
              {creating ? 'Creating...' : 'Create Report'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Reports List */}
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
            Your Reports
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size={isMobile ? "small" : "medium"}
            sx={{
              py: { xs: 0.5, sm: 1 },
              px: { xs: 1.5, sm: 2 }
            }}
          >
            Refresh
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
          ) : reports.length > 0 ? (
            <Grid container spacing={{ xs: 2, sm: 3 }}>
              {reports.map((report) => (
                <Grid item xs={12} sm={6} md={4} key={report.id}>
                  <ReportCard report={report} onRefresh={handleRefresh} />
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
                You haven't created any scouting reports yet
              </Typography>
              <ReportIcon sx={{ fontSize: 60, color: 'text.secondary', opacity: 0.5, my: 2 }} />
              <Typography
                variant={isMobile ? "body2" : "body1"}
                color="text.secondary"
                gutterBottom
              >
                Select a video and create your first report
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default ScoutingReportPage;
