import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Divider,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
} from '@mui/material';
import { CloudUpload, PlayArrow, Analytics, Timeline, ExpandMore } from '@mui/icons-material';
import axios from 'axios';
import { ENDPOINTS } from '../../config/api';

const ComputerVisionTest = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [visualAnalysisImage, setVisualAnalysisImage] = useState(null);
  const [progressiveResults, setProgressiveResults] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [videoProcessingJob, setVideoProcessingJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Analysis options
  const [options, setOptions] = useState({
    enable_court_detection: true,
    enable_player_detection: true,
    enable_team_classification: true,
    enable_ball_detection: true,
  });

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);

  // Cleanup blob URLs to prevent memory leaks
  useEffect(() => {
    return () => {
      if (visualAnalysisImage) {
        URL.revokeObjectURL(visualAnalysisImage);
      }
    };
  }, [visualAnalysisImage]);

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedVideo(file);
      setError(null);
    }
  };

  const analyzeImage = async () => {
    if (!selectedImage) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('enable_court_detection', options.enable_court_detection);
      formData.append('enable_player_detection', options.enable_player_detection);
      formData.append('enable_team_classification', options.enable_team_classification);
      formData.append('enable_ball_detection', options.enable_ball_detection);

      const response = await axios.post(
        ENDPOINTS.SCOUTING.COMPUTER_VISION.ANALYZE_IMAGE,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setAnalysisResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze image');
    } finally {
      setLoading(false);
    }
  };

  const analyzeImageVisual = async () => {
    if (!selectedImage) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('enable_court_detection', options.enable_court_detection);
      formData.append('enable_player_detection', options.enable_player_detection);
      formData.append('enable_team_classification', options.enable_team_classification);
      formData.append('enable_ball_detection', options.enable_ball_detection);

      const response = await axios.post(
        ENDPOINTS.SCOUTING.COMPUTER_VISION.ANALYZE_IMAGE_VISUAL,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          responseType: 'blob', // Important for image response
        }
      );

      // Create blob URL for the annotated image
      const imageBlob = new Blob([response.data], { type: 'image/jpeg' });
      const imageUrl = URL.createObjectURL(imageBlob);
      setVisualAnalysisImage(imageUrl);

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze image visually');
    } finally {
      setLoading(false);
    }
  };

  const analyzeImageProgressive = async () => {
    if (!selectedImage) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);
    setProgressData({ percentage: 0, step: 'Initializing...', intermediateResults: [] });
    setProgressiveResults(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('enable_court_detection', options.enable_court_detection);
      formData.append('enable_player_detection', options.enable_player_detection);
      formData.append('enable_team_classification', options.enable_team_classification);
      formData.append('enable_ball_detection', options.enable_ball_detection);

      // Use fetch with streaming response for progressive updates
      const response = await fetch(ENDPOINTS.SCOUTING.COMPUTER_VISION.ANALYZE_IMAGE_PROGRESSIVE, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Process the streaming response
      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const eventData = line.slice(6); // Remove 'data: ' prefix
                  if (eventData.trim()) {
                    const data = JSON.parse(eventData);

                    // Handle different event types based on the data structure
                    if (data.percentage !== undefined) {
                      setProgressData(prev => ({
                        ...prev,
                        percentage: data.percentage,
                        step: data.step || data.message,
                        currentStep: data.current_step,
                        totalSteps: data.total_steps
                      }));
                    }

                    if (data.type) {
                      // Intermediate result
                      setProgressData(prev => ({
                        ...prev,
                        intermediateResults: [...(prev.intermediateResults || []), data]
                      }));
                    }

                    if (data.analysis_results) {
                      // Final result
                      setProgressiveResults({
                        analysisResults: data.analysis_results,
                        annotatedImage: data.annotated_image
                      });
                      setProgressData(prev => ({
                        ...prev,
                        percentage: 100,
                        step: 'Analysis completed!'
                      }));
                      setLoading(false);
                      return;
                    }

                    if (data.error) {
                      setError(data.error);
                      setLoading(false);
                      return;
                    }
                  }
                } catch (parseError) {
                  console.warn('Failed to parse SSE data:', parseError);
                }
              }
            }
          }
        } catch (streamError) {
          console.error('Stream processing error:', streamError);
          setError('Failed to process analysis stream');
          setLoading(false);
        }
      };

      processStream();

    } catch (err) {
      setError(err.message || 'Failed to start progressive analysis');
      setLoading(false);
    }
  };

  const processVideo = async () => {
    if (!selectedVideo) {
      setError('Please select a video first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // First upload the video to get video_id
      const uploadFormData = new FormData();
      uploadFormData.append('file', selectedVideo);
      uploadFormData.append('title', `CV Test - ${selectedVideo.name}`);
      uploadFormData.append('description', 'Computer Vision Test Video');

      const uploadResponse = await axios.post(
        ENDPOINTS.VIDEOS.UPLOAD,
        uploadFormData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      const videoId = uploadResponse.data.data.id;

      // Then start computer vision processing
      const processFormData = new FormData();
      processFormData.append('video_id', videoId);
      processFormData.append('config', JSON.stringify({
        enable_court_detection: options.enable_court_detection,
        enable_player_detection: options.enable_player_detection,
        enable_team_classification: options.enable_team_classification,
        enable_ball_detection: options.enable_ball_detection,
        process_every_nth_frame: 5, // Process every 5th frame for faster processing
      }));

      const processResponse = await axios.post(
        ENDPOINTS.SCOUTING.COMPUTER_VISION.PROCESS_VIDEO,
        processFormData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setVideoProcessingJob(processResponse.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process video');
    } finally {
      setLoading(false);
    }
  };

  const handleOptionChange = (option) => (event) => {
    setOptions(prev => ({
      ...prev,
      [option]: event.target.checked,
    }));
  };

  const renderAnalysisResults = () => {
    if (!analysisResults) return null;

    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Analysis Results
          </Typography>
          
          {analysisResults.court_detection && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary">
                Court Detection (Enhanced)
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                <Chip
                  label={`Confidence: ${(analysisResults.court_detection.confidence_score * 100).toFixed(1)}%`}
                  color={analysisResults.court_detection.confidence_score > 0.7 ? 'success' : 'warning'}
                  size="small"
                />
                {analysisResults.court_detection.detection_method && (
                  <Chip
                    label={`Method: ${analysisResults.court_detection.detection_method}`}
                    color="info"
                    size="small"
                  />
                )}
              </Box>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Homography: {analysisResults.court_detection.has_homography ? 'Available' : 'Not available'}
              </Typography>
              {analysisResults.court_detection.court_corners && (
                <Typography variant="body2">
                  Court Corners: {analysisResults.court_detection.court_corners.length} detected
                </Typography>
              )}
              {analysisResults.court_detection.three_point_line && (
                <Typography variant="body2">
                  Three-Point Line: {analysisResults.court_detection.three_point_line.length} points detected
                </Typography>
              )}
              {analysisResults.court_detection.free_throw_line && (
                <Typography variant="body2">
                  Free-Throw Line: {analysisResults.court_detection.free_throw_line.length} points detected
                </Typography>
              )}
              {analysisResults.court_detection.center_circle && (
                <Typography variant="body2">
                  Center Circle: Detected (radius: {analysisResults.court_detection.center_circle.radius?.toFixed(1) || 'N/A'})
                </Typography>
              )}
            </Box>
          )}

          {analysisResults.player_detection && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary">
                Player Detection
              </Typography>
              <Chip 
                label={`${analysisResults.player_detection.player_count} players detected`}
                color="info"
                size="small"
              />
              {analysisResults.player_detection.players.length > 0 && (
                <List dense>
                  {analysisResults.player_detection.players.slice(0, 5).map((player, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={`Player ${player.player_id}`}
                        secondary={`Confidence: ${(player.confidence * 100).toFixed(1)}%${player.jersey_number ? `, Jersey: ${player.jersey_number}` : ''}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}

          {analysisResults.team_classification && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary">
                Team Classification
              </Typography>
              {analysisResults.team_classification.message ? (
                <Typography variant="body2" color="text.secondary">
                  {analysisResults.team_classification.message}
                </Typography>
              ) : (
                <>
                  <Chip 
                    label={`Team A: ${analysisResults.team_classification.team_a_players.length} players`}
                    color="primary"
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Chip 
                    label={`Team B: ${analysisResults.team_classification.team_b_players.length} players`}
                    color="secondary"
                    size="small"
                  />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Classification Confidence: {(analysisResults.team_classification.classification_confidence * 100).toFixed(1)}%
                  </Typography>
                </>
              )}
            </Box>
          )}

          {analysisResults.ball_detection && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary">
                Ball Detection
              </Typography>
              <Chip 
                label={analysisResults.ball_detection.ball_detected ? 'Ball detected' : 'No ball detected'}
                color={analysisResults.ball_detection.ball_detected ? 'success' : 'default'}
                size="small"
              />
              {analysisResults.ball_detection.ball_detected && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Confidence: {(analysisResults.ball_detection.confidence * 100).toFixed(1)}%
                </Typography>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Computer Vision Testing
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Test the basketball computer vision capabilities with images and videos.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Options Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Options
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={options.enable_court_detection}
                    onChange={handleOptionChange('enable_court_detection')}
                  />
                }
                label="Court Detection"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={options.enable_player_detection}
                    onChange={handleOptionChange('enable_player_detection')}
                  />
                }
                label="Player Detection"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={options.enable_team_classification}
                    onChange={handleOptionChange('enable_team_classification')}
                  />
                }
                label="Team Classification"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={options.enable_ball_detection}
                    onChange={handleOptionChange('enable_ball_detection')}
                  />
                }
                label="Ball Detection"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Image Analysis */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Image Analysis
              </Typography>
              
              <input
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                ref={imageInputRef}
                style={{ display: 'none' }}
              />
              
              <Button
                variant="outlined"
                startIcon={<CloudUpload />}
                onClick={() => imageInputRef.current?.click()}
                sx={{ mr: 2, mb: 2 }}
              >
                Select Image
              </Button>
              
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <Analytics />}
                onClick={analyzeImage}
                disabled={!selectedImage || loading}
                sx={{ mr: 2, mb: 2 }}
              >
                Analyze (Data)
              </Button>

              <Button
                variant="contained"
                color="secondary"
                startIcon={loading ? <CircularProgress size={20} /> : <Analytics />}
                onClick={analyzeImageVisual}
                disabled={!selectedImage || loading}
                sx={{ mr: 2, mb: 2 }}
              >
                Analyze (Visual)
              </Button>

              <Button
                variant="contained"
                color="success"
                startIcon={loading ? <CircularProgress size={20} /> : <Timeline />}
                onClick={analyzeImageProgressive}
                disabled={!selectedImage || loading}
                sx={{ mb: 2 }}
              >
                Analyze (Live Progress)
              </Button>

              {imagePreview && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Original Image:
                  </Typography>
                  <img
                    src={imagePreview}
                    alt="Preview"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '300px',
                      objectFit: 'contain',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                    }}
                  />
                </Box>
              )}

              {visualAnalysisImage && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Analysis Results (Visual):
                  </Typography>
                  <img
                    src={visualAnalysisImage}
                    alt="Visual Analysis Results"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '400px',
                      objectFit: 'contain',
                      border: '2px solid #1976d2',
                      borderRadius: '4px',
                    }}
                  />
                </Box>
              )}

              {/* Progressive Analysis Progress */}
              {progressData && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Live Analysis Progress:
                  </Typography>
                  <Card sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        {progressData.step}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={progressData.percentage || 0}
                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {progressData.percentage || 0}% Complete
                        {progressData.currentStep && progressData.totalSteps &&
                          ` (Step ${progressData.currentStep}/${progressData.totalSteps})`
                        }
                      </Typography>
                    </Box>

                    {/* Intermediate Results */}
                    {progressData.intermediateResults && progressData.intermediateResults.length > 0 && (
                      <Box>
                        <Typography variant="subtitle3" gutterBottom>
                          Detected Features:
                        </Typography>
                        {progressData.intermediateResults.map((result, index) => (
                          <Chip
                            key={index}
                            label={result.message}
                            color="primary"
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </Card>
                </Box>
              )}

              {/* Progressive Analysis Final Results */}
              {progressiveResults && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Live Analysis Results:
                  </Typography>

                  {/* Annotated Image */}
                  {progressiveResults.annotatedImage && (
                    <Box sx={{ mb: 2 }}>
                      <img
                        src={progressiveResults.annotatedImage}
                        alt="Progressive Analysis Results"
                        style={{
                          maxWidth: '100%',
                          maxHeight: '400px',
                          objectFit: 'contain',
                          border: '2px solid #2e7d32',
                          borderRadius: '4px',
                        }}
                      />
                    </Box>
                  )}

                  {/* Analysis Summary */}
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">
                        Detailed Analysis Results
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {JSON.stringify(progressiveResults.analysisResults, null, 2)}
                      </pre>
                    </AccordionDetails>
                  </Accordion>
                </Box>
              )}

              {renderAnalysisResults()}
            </CardContent>
          </Card>

          <Divider sx={{ my: 3 }} />

          {/* Video Processing */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Video Processing
              </Typography>
              
              <input
                type="file"
                accept="video/*"
                onChange={handleVideoSelect}
                ref={videoInputRef}
                style={{ display: 'none' }}
              />
              
              <Button
                variant="outlined"
                startIcon={<CloudUpload />}
                onClick={() => videoInputRef.current?.click()}
                sx={{ mr: 2, mb: 2 }}
              >
                Select Video
              </Button>
              
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                onClick={processVideo}
                disabled={!selectedVideo || loading}
                sx={{ mb: 2 }}
              >
                Process Video
              </Button>

              {selectedVideo && (
                <Typography variant="body2" sx={{ mb: 2 }}>
                  Selected: {selectedVideo.name}
                </Typography>
              )}

              {videoProcessingJob && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Video processing job created! Job ID: {videoProcessingJob.job_id}
                  <br />
                  Status: {videoProcessingJob.status}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ComputerVisionTest;
