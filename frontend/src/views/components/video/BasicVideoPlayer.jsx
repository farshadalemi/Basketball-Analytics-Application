import React, { useRef, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Box, CircularProgress, Typography, Paper } from '@mui/material';
import { getUserFromStorage } from '../../../models/auth';

/**
 * A very basic video player that uses the browser's native video element
 * with authentication headers
 */
const BasicVideoPlayer = ({ videoId, title }) => {
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get the auth token
  const getAuthToken = () => {
    const userData = getUserFromStorage();
    return userData?.token || '';
  };

  // State to store the video blob URL
  const [videoUrl, setVideoUrl] = useState(null);

  // Fetch the video using XMLHttpRequest to handle authentication
  useEffect(() => {
    if (!videoId) return;

    setLoading(true);
    setError(null);

    const xhr = new XMLHttpRequest();
    xhr.open('GET', `http://localhost:8000/api/direct/videos/${videoId}?self=true`, true);
    xhr.responseType = 'blob';

    // Add authentication header
    const token = getAuthToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    // Log the request for debugging
    console.log(`Sending request to: http://localhost:8000/api/direct/videos/${videoId}?self=true`);
    console.log(`With token: ${token ? 'Bearer ' + token.substring(0, 10) + '...' : 'No token'}`);

    xhr.onload = function() {
      console.log(`Response received with status: ${this.status}`);
      console.log(`Response headers: ${this.getAllResponseHeaders()}`);

      if (this.status === 200) {
        try {
          const contentType = this.getResponseHeader('Content-Type') || 'video/mp4';
          console.log(`Content-Type: ${contentType}`);

          const blob = new Blob([this.response], { type: contentType });
          const url = URL.createObjectURL(blob);
          console.log(`Created blob URL: ${url}`);

          setVideoUrl(url);
          setLoading(false);
        } catch (error) {
          console.error('Error creating blob URL:', error);
          setError(`Failed to process video: ${error.message}`);
          setLoading(false);
        }
      } else {
        console.error(`Failed with status: ${this.status} ${this.statusText}`);
        setError(`Failed to load video: ${this.status} ${this.statusText}`);
        setLoading(false);
      }
    };

    xhr.onerror = function() {
      setError('Network error occurred while loading video');
      setLoading(false);
    };

    xhr.send();

    // Clean up function
    return () => {
      xhr.abort(); // Abort the request if component unmounts
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl); // Clean up the blob URL
      }
    };
  }, [videoId]);

  // Handle video loading
  const handleLoadedData = () => {
    setLoading(false);
  };

  // Handle video errors
  const handleError = (e) => {
    console.error('Video error:', e);
    setLoading(false);
    setError('Failed to load video. Please try again later.');
  };

  return (
    <Paper elevation={3} sx={{ overflow: 'hidden', bgcolor: 'background.paper' }}>
      <Box sx={{ position: 'relative', width: '100%', bgcolor: 'black' }}>
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1
            }}
          >
            <CircularProgress color="primary" />
          </Box>
        )}

        {error && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1,
              bgcolor: 'rgba(0,0,0,0.7)',
              p: 2
            }}
          >
            <Typography color="error" gutterBottom>
              {error}
            </Typography>
          </Box>
        )}

        <video
          ref={videoRef}
          src={videoUrl}
          poster="/video-placeholder.svg"
          style={{ width: '100%', display: 'block' }}
          playsInline
          controls
          preload="auto"
          onLoadedData={handleLoadedData}
          onError={handleError}
          crossOrigin="use-credentials"
        />
      </Box>

      {title && (
        <Box sx={{ p: { xs: 1, sm: 2 } }}>
          <Typography variant="h6" component="h2" noWrap>
            {title}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

BasicVideoPlayer.propTypes = {
  videoId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  title: PropTypes.string
};

export default BasicVideoPlayer;
