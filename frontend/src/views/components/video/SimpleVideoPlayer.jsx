import React, { useRef, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Box, CircularProgress, Typography, Button, Paper } from '@mui/material';
import axios from 'axios';
import { ENDPOINTS } from '../../../config/api';

/**
 * A simple video player that handles authentication and streaming
 */
const SimpleVideoPlayer = ({ videoId, title, poster }) => {
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoBlob, setVideoBlob] = useState(null);

  // Get auth token from localStorage
  const getAuthToken = () => {
    try {
      const userDataStr = localStorage.getItem('userData');
      if (userDataStr) {
        const userData = JSON.parse(userDataStr);
        return userData.token;
      }
      return null;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  // Fetch the video content
  useEffect(() => {
    const fetchVideo = async () => {
      if (!videoId) return;

      setLoading(true);
      setError(null);

      try {
        const token = getAuthToken();
        if (!token) {
          setError('Authentication required');
          setLoading(false);
          return;
        }

        // Try the direct streaming endpoint first
        try {
          console.log('Trying direct streaming endpoint');
          const directResponse = await axios.get(
            ENDPOINTS.VIDEOS.DIRECT_STREAM(videoId),
            {
              headers: {
                'Authorization': `Bearer ${token}`
              },
              responseType: 'blob' // This endpoint always returns binary data
            }
          );

          // Create a blob URL from the response
          const blob = new Blob([directResponse.data], { type: directResponse.headers['content-type'] || 'video/mp4' });
          const blobUrl = URL.createObjectURL(blob);
          setVideoBlob(blobUrl);
          setLoading(false);
          return; // Exit early if direct streaming works
        } catch (directError) {
          console.error('Direct streaming failed, falling back to regular endpoint:', directError);
          // Fall back to the regular streaming endpoint
        }

        // Fallback: Fetch the video from the regular API endpoint
        const response = await axios.get(
          ENDPOINTS.VIDEOS.STREAM(videoId) + '?self=true',
          {
            headers: {
              'Authorization': `Bearer ${token}`
            },
            // Don't set responseType to 'blob' yet, as we need to check if it's JSON or binary
          }
        )

        // Check if the response is JSON (contains streaming_url)
        if (response.data && response.data.streaming_url) {
          console.log('Got streaming URL from API:', response.data.streaming_url);

          // Fetch the video from the streaming URL
          try {
            const videoResponse = await fetch(response.data.streaming_url);
            if (!videoResponse.ok) {
              throw new Error(`HTTP error! Status: ${videoResponse.status}`);
            }

            const blob = await videoResponse.blob();
            const blobUrl = URL.createObjectURL(blob);
            setVideoBlob(blobUrl);
            setLoading(false);
            return; // Exit early
          } catch (error) {
            console.error('Error fetching video from streaming URL:', error);
            throw error; // Re-throw to be caught by the outer catch block
          }
        }

        // Create a blob URL from the response
        const blob = new Blob([response.data], { type: response.headers['content-type'] || 'video/mp4' });
        const blobUrl = URL.createObjectURL(blob);

        setVideoBlob(blobUrl);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching video:', error);
        setError('Failed to load video. Please try again later.');
        setLoading(false);
      }
    };

    fetchVideo();

    // Cleanup function
    return () => {
      if (videoBlob) {
        URL.revokeObjectURL(videoBlob);
      }
    };
  }, [videoId]);

  // Handle video errors
  const handleError = (e) => {
    console.error('Video error:', e);
    setError('Failed to play video. Please try again later.');
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
            <Button
              variant="contained"
              color="primary"
              onClick={() => {
                setError(null);
                setLoading(true);
                // Force reload the video
                if (videoRef.current) {
                  videoRef.current.load();
                }
              }}
            >
              Retry
            </Button>
          </Box>
        )}

        <video
          ref={videoRef}
          src={videoBlob}
          poster={poster || '/video-placeholder.svg'}
          style={{ width: '100%', display: 'block' }}
          playsInline
          controls
          preload="auto"
          onError={handleError}
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

SimpleVideoPlayer.propTypes = {
  videoId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  title: PropTypes.string,
  poster: PropTypes.string
};

export default SimpleVideoPlayer;
