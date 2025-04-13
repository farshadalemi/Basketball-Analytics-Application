import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Chip,
  CircularProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Person as PersonIcon,
  Speed as SpeedIcon,
  FitnessCenter as StrengthIcon,
  DirectionsRun as AgilityIcon,
  SportsBasketball as BasketballIcon,
  Shield as DefenseIcon
} from '@mui/icons-material';
import { useToast } from '../../context/ToastContext';
import Loading from '../components/common/Loading';
import { getReportById } from '../../controllers/scoutingController';

/**
 * Format date string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Get status color
 * @param {string} status - Report status
 * @returns {string} Color for the status chip
 */
const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'queued':
      return 'info';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Report details page component
 */
const ReportDetailsPage = () => {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const { showError } = useToast();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Fetch report on mount
  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        await getReportById(
          reportId,
          (reportData) => setReport(reportData),
          (error) => showError(error)
        );
      } catch (error) {
        console.error('Error fetching report:', error);
        showError('Failed to fetch report');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await getReportById(
        reportId,
        (reportData) => setReport(reportData),
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error refreshing report:', error);
      showError('Failed to refresh report');
    } finally {
      setRefreshing(false);
    }
  };

  const handleDownload = () => {
    if (report && report.download_url) {
      window.open(`${process.env.REACT_APP_SCOUTING_API_URL}${report.download_url}`, '_blank');
    } else {
      showError('Download not available yet');
    }
  };

  const handleBack = () => {
    navigate('/scouting');
  };

  // Render loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Loading message="Loading report details..." />
      </Container>
    );
  }

  // Render error state if report not found
  if (!report) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h5" color="error" gutterBottom>
            Report Not Found
          </Typography>
          <Typography variant="body1" paragraph>
            The requested report could not be found.
          </Typography>
          <Button
            variant="contained"
            startIcon={<BackIcon />}
            onClick={handleBack}
          >
            Back to Reports
          </Button>
        </Paper>
      </Container>
    );
  }

  // Extract team analysis from report if available
  const teamAnalysis = report.analysis_results?.team_analysis || null;

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 3 } }}>
        <Button
          variant="text"
          startIcon={<BackIcon />}
          onClick={handleBack}
          sx={{ mb: 2 }}
        >
          Back to Reports
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
          <Typography
            variant={isMobile ? "h5" : "h4"}
            component="h1"
            sx={{ fontWeight: 'bold' }}
          >
            {report.title}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
              size={isMobile ? "small" : "medium"}
            >
              Refresh
            </Button>
            
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleDownload}
              disabled={report.status !== 'completed' || !report.download_url}
              size={isMobile ? "small" : "medium"}
            >
              Download PDF
            </Button>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 1, flexWrap: 'wrap' }}>
          <Chip
            label={report.status}
            color={getStatusColor(report.status)}
            size={isMobile ? "small" : "medium"}
          />
          
          <Typography variant="body2" color="text.secondary">
            Created: {formatDate(report.created_at)}
          </Typography>
          
          {report.completed_at && (
            <Typography variant="body2" color="text.secondary">
              Completed: {formatDate(report.completed_at)}
            </Typography>
          )}
        </Box>
      </Box>

      <Divider sx={{ mb: { xs: 2, sm: 3 } }} />

      {/* Report Information */}
      <Grid container spacing={3}>
        {/* Left Column - Report Details */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report Details
            </Typography>
            
            <List dense>
              <ListItem>
                <ListItemText
                  primary="Video"
                  secondary={report.video_title || 'Unknown'}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText
                  primary="Team Name"
                  secondary={report.team_name || 'Not specified'}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText
                  primary="Opponent Name"
                  secondary={report.opponent_name || 'Not specified'}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText
                  primary="Description"
                  secondary={report.description || 'No description'}
                />
              </ListItem>
            </List>
          </Paper>
          
          {/* Team Analysis Summary */}
          {teamAnalysis && (
            <Paper sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" gutterBottom>
                Team Analysis
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                Offensive Style
              </Typography>
              <Box sx={{ mb: 2 }}>
                {Object.entries(teamAnalysis.offensive_style).map(([key, value]) => (
                  <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {typeof value === 'number' ? `${value}/10` : value}
                    </Typography>
                  </Box>
                ))}
              </Box>
              
              <Typography variant="subtitle2" gutterBottom>
                Defensive Style
              </Typography>
              <Box sx={{ mb: 2 }}>
                {Object.entries(teamAnalysis.defensive_style).map(([key, value]) => (
                  <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {typeof value === 'number' ? `${value}/10` : value}
                    </Typography>
                  </Box>
                ))}
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Team Strengths
              </Typography>
              <List dense>
                {teamAnalysis.team_strengths.map((strength, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <StrengthIcon fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText primary={strength} />
                  </ListItem>
                ))}
              </List>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                Team Weaknesses
              </Typography>
              <List dense>
                {teamAnalysis.team_weaknesses.map((weakness, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <DefenseIcon fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText primary={weakness} />
                  </ListItem>
                ))}
              </List>
              
              {teamAnalysis.recommended_strategy && (
                <>
                  <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                    Recommended Strategy
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {teamAnalysis.recommended_strategy}
                  </Typography>
                </>
              )}
            </Paper>
          )}
        </Grid>
        
        {/* Right Column - Player Analysis */}
        <Grid item xs={12} md={8}>
          {report.status === 'completed' && teamAnalysis ? (
            <>
              <Typography variant="h6" gutterBottom>
                Player Analysis
              </Typography>
              
              <Grid container spacing={2}>
                {teamAnalysis.players.map((player) => (
                  <Grid item xs={12} sm={6} key={player.player_id}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Avatar sx={{ bgcolor: theme.palette.primary.main, mr: 2 }}>
                            {player.jersey_number || '?'}
                          </Avatar>
                          <Box>
                            <Typography variant="h6">
                              {player.name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {player.position} • {player.height}
                            </Typography>
                          </Box>
                        </Box>
                        
                        <Divider sx={{ mb: 2 }} />
                        
                        <Grid container spacing={1} sx={{ mb: 2 }}>
                          <Grid item xs={4}>
                            <Box sx={{ textAlign: 'center' }}>
                              <SpeedIcon color="primary" />
                              <Typography variant="body2">
                                Speed: {player.physical_attributes.speed}/10
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={4}>
                            <Box sx={{ textAlign: 'center' }}>
                              <StrengthIcon color="primary" />
                              <Typography variant="body2">
                                Strength: {player.physical_attributes.strength}/10
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={4}>
                            <Box sx={{ textAlign: 'center' }}>
                              <AgilityIcon color="primary" />
                              <Typography variant="body2">
                                Agility: {player.physical_attributes.agility}/10
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                        
                        <Typography variant="subtitle2" gutterBottom>
                          Strengths
                        </Typography>
                        <List dense>
                          {player.strengths.map((strength, index) => (
                            <ListItem key={index} sx={{ py: 0.25 }}>
                              <ListItemIcon sx={{ minWidth: 30 }}>
                                <BasketballIcon fontSize="small" color="success" />
                              </ListItemIcon>
                              <ListItemText primary={strength} />
                            </ListItem>
                          ))}
                        </List>
                        
                        <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                          Weaknesses
                        </Typography>
                        <List dense>
                          {player.weaknesses.map((weakness, index) => (
                            <ListItem key={index} sx={{ py: 0.25 }}>
                              <ListItemIcon sx={{ minWidth: 30 }}>
                                <DefenseIcon fontSize="small" color="error" />
                              </ListItemIcon>
                              <ListItemText primary={weakness} />
                            </ListItem>
                          ))}
                        </List>
                        
                        {player.strategy_notes && (
                          <>
                            <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                              How to Play Against
                            </Typography>
                            <Typography variant="body2">
                              {player.strategy_notes}
                            </Typography>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </>
          ) : report.status === 'processing' || report.status === 'queued' ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Report is being generated
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {report.status === 'processing' 
                  ? 'Your report is currently being processed. This may take a few minutes.'
                  : 'Your report is queued for processing and will begin shortly.'}
              </Typography>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRefresh}
                sx={{ mt: 2 }}
              >
                Check Status
              </Button>
            </Paper>
          ) : report.status === 'failed' ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="error" gutterBottom>
                Report Generation Failed
              </Typography>
              <Typography variant="body1" paragraph>
                There was an error generating your report. Please try again or contact support.
              </Typography>
              <Button
                variant="contained"
                onClick={handleBack}
              >
                Back to Reports
              </Button>
            </Paper>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                No Analysis Available
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Analysis data is not available for this report.
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default ReportDetailsPage;
