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
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
  Alert
} from '@mui/material';
import {
  Description as ReportIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  VideoLibrary as VideoIcon,
  TableChart as CsvIcon,
  PictureAsPdf as PdfIcon
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getVideos } from '../../controllers/videoController';
import { getReports, createReport, uploadCsvStats } from '../../controllers/scoutingController';
import ReportCard from '../components/scouting/ReportCard';
import CsvUpload from '../components/scouting/CsvUpload';

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

  // Form states
  const [selectedVideo, setSelectedVideo] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [teamName, setTeamName] = useState('');
  const [opponentName, setOpponentName] = useState('');

  // Tab and CSV states
  const [tabValue, setTabValue] = useState(0); // 0 = Video-based, 1 = CSV-based
  const [csvFile, setCsvFile] = useState(null);
  const [csvError, setCsvError] = useState('');
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvUploadProgress, setCsvUploadProgress] = useState(0);

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

  // Handle CSV file selection
  const handleCsvFileSelect = (file, error) => {
    setCsvFile(file);
    setCsvError(error || '');
  };

  // Handle CSV file removal
  const handleCsvFileRemove = () => {
    setCsvFile(null);
    setCsvError('');
  };

  // Handle CSV upload
  const handleCsvUpload = async (file) => {
    try {
      setCsvUploading(true);
      setCsvUploadProgress(0);

      await uploadCsvStats(
        file,
        (progress) => setCsvUploadProgress(progress),
        (response) => {
          showSuccess('CSV file uploaded successfully');
          setCsvUploading(false);
          return response;
        },
        (error) => {
          setCsvError(error);
          setCsvUploading(false);
          showError(`Failed to upload CSV: ${error}`);
        }
      );
    } catch (error) {
      console.error('CSV upload error:', error);
      setCsvUploading(false);
    }
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    // Reset form when switching tabs
    setSelectedVideo('');
    setReportTitle('');
    setTeamName('');
    setOpponentName('');
    setCsvFile(null);
    setCsvError('');
  };

  const handleCreateReport = async () => {
    // Validation based on tab
    if (tabValue === 0) {
      // Video-based report
      if (!selectedVideo) {
        showError('Please select a video');
        return;
      }
    } else {
      // CSV-based report
      if (!csvFile) {
        showError('Please upload a CSV file');
        return;
      }
    }

    if (!reportTitle) {
      showError('Please enter a report title');
      return;
    }

    try {
      setCreating(true);

      let reportData;

      if (tabValue === 0) {
        // Video-based report
        const videoObj = videos.find(v => v.id === parseInt(selectedVideo));
        reportData = {
          title: reportTitle,
          description: `Video-based scouting report for ${teamName || 'team'}`,
          video_id: parseInt(selectedVideo),
          video_title: videoObj ? videoObj.title : '',
          team_name: teamName,
          opponent_name: opponentName,
          user_id: user.id,
          report_type: 'video'
        };
      } else {
        // CSV-based report - first upload the CSV if not already uploaded
        if (csvFile && !csvUploading) {
          await handleCsvUpload(csvFile);
        }

        reportData = {
          title: reportTitle,
          description: `Statistics-based scouting report for ${teamName || 'team'}`,
          team_name: teamName,
          opponent_name: opponentName,
          user_id: user.id,
          report_type: 'csv',
          csv_file_name: csvFile ? csvFile.name : null
        };
      }

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
          setCsvFile(null);
          setCsvError('');
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
          Create New Scouting Report
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3 }}
        >
          Choose your data source: analyze from uploaded videos or import statistics from CSV files
        </Typography>

        {/* Report Type Tabs */}
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<VideoIcon />}
            label="Video Analysis"
            iconPosition="start"
            sx={{ minHeight: 48 }}
          />
          <Tab
            icon={<CsvIcon />}
            label="CSV Statistics"
            iconPosition="start"
            sx={{ minHeight: 48 }}
          />
        </Tabs>

        {/* Tab Content */}
        {tabValue === 0 ? (
          // Video-based report form
          <Box>
            <Alert severity="info" sx={{ mb: 3 }}>
              Create reports based on AI analysis of your uploaded basketball videos
            </Alert>

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
                    disabled={creating || !Array.isArray(videos) || videos.length === 0}
                  >
                    {Array.isArray(videos) ? videos.filter(v => v.status === 'completed').map((video) => (
                      <MenuItem key={video.id} value={video.id}>
                        {video.title}
                      </MenuItem>
                    )) : []}
                  </Select>
                </FormControl>
                {Array.isArray(videos) && videos.filter(v => v.status === 'completed').length === 0 && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    No analyzed videos available. <Button size="small" onClick={() => navigate('/scouting')}>Analyze videos</Button>
                  </Typography>
                )}
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
                  {creating ? 'Creating Video Report...' : 'Create Video Report'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        ) : (
          // CSV-based report form
          <Box>
            <Alert severity="info" sx={{ mb: 3 }}>
              Create reports by uploading CSV files with basketball statistics (FIBA format supported)
            </Alert>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <CsvUpload
                  file={csvFile}
                  onFileSelect={handleCsvFileSelect}
                  onFileRemove={handleCsvFileRemove}
                  uploading={csvUploading}
                  uploadProgress={csvUploadProgress}
                  error={csvError}
                />
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
                  disabled={creating || !csvFile || !reportTitle}
                  sx={{ mt: 1 }}
                >
                  {creating ? 'Creating CSV Report...' : 'Create CSV Report'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        )}
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
          ) : Array.isArray(reports) && reports.length > 0 ? (
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
