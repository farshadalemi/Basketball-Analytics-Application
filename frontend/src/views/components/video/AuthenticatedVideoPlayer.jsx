import React, { useRef, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Button,
  useMediaQuery,
  useTheme
} from '@mui/material';
import axios from 'axios';

/**
 * A video player component that handles authentication for API endpoints
 */
const AuthenticatedVideoPlayer = ({ src, title, poster, onError }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Get auth token from localStorage
  const getAuthToken = () => {
    try {
      // Try both storage keys that might be used in the app
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const userData = JSON.parse(userStr);
        if (userData.token) {
          return userData.token;
        }
      }

      // Try alternative storage key
      const userDataStr = localStorage.getItem('userData');
      if (userDataStr) {
        const userData = JSON.parse(userDataStr);
        if (userData.token) {
          return userData.token;
        }
      }

      return null;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  // Load video with authentication
  useEffect(() => {
    let isMounted = true; // Flag to prevent state updates after unmount
    const loadVideo = async () => {
      if (!isMounted) return;
      setLoading(true);
      setError(null);

      try {
        if (!src) {
          setError('No video source provided');
          setLoading(false);
          return;
        }

        // If the source is an API URL, we need to fetch it with authentication
        if (src.includes('/api/')) {
          const token = getAuthToken();
          if (!token) {
            setError('Authentication required');
            setLoading(false);
            if (onError) onError(new Error('Authentication required'));
            return;
          }

          // Fetch the video URL with authentication
          const response = await axios.get(src, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          // Check if we got a streaming URL in the response
          if (isMounted) { // Only update state if component is still mounted
            if (response.data && response.data.streaming_url) {
              const streamingUrl = response.data.streaming_url;
              setVideoUrl(streamingUrl);
              console.log('Got streaming URL:', streamingUrl);

              // Preload the video to check if it's accessible
              const preloadImg = new Image();
              preloadImg.src = streamingUrl;
              preloadImg.onerror = () => {
                console.error('Error preloading streaming URL:', streamingUrl);
                // If the streaming URL fails, try using a direct URL
                if (streamingUrl.includes('localhost:9000')) {
                  // Try a different format for the direct URL
                  const directUrl = streamingUrl.replace(/\?.*$/, '');
                  console.log('Trying direct URL without query params:', directUrl);
                  setVideoUrl(directUrl);
                }
              };
            } else {
              // Use the original URL as fallback
              setVideoUrl(src);
              console.log('Using original URL as fallback');
            }
          }
        } else {
          // Not an API URL, use directly
          if (isMounted) setVideoUrl(src);
        }
      } catch (error) {
        console.error('Error loading video:', error);
        if (isMounted) {
          setError(error.message || 'Failed to load video');
          if (onError) onError(error);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadVideo();

    // Cleanup function to handle component unmounting
    return () => {
      isMounted = false;
      // Pause video if it's playing to prevent errors
      if (videoRef.current && !videoRef.current.paused) {
        videoRef.current.pause();
      }
    };
  }, [src, onError]);

  // Simple play/pause handler for the video element
  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Handle video events
  useEffect(() => {
    // Store a reference to the video element
    const video = videoRef.current;
    if (!video) return;

    // Event handlers
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleCanPlay = () => setLoading(false);
    const handleLoadedMetadata = () => setLoading(false);

    // Add event listeners
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('canplay', handleCanPlay);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);

    // Cleanup function
    return () => {
      // Remove event listeners
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('canplay', handleCanPlay);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);

      // Pause and unload video to prevent memory leaks
      try {
        if (video && !video.paused) {
          video.pause();
        }
        if (video) {
          video.removeAttribute('src'); // Unload the video
          video.load(); // Reset the video element
        }
      } catch (e) {
        console.error('Error cleaning up video element:', e);
      }
    };
  }, []);

  // Error handler for video loading issues
  const handleError = (e) => {
    console.error('Video error:', e);
    setLoading(false);

    // Try to get more detailed error information
    if (videoRef.current) {
      const video = videoRef.current;
      console.log('Video element error details:', {
        error: video.error,
        networkState: video.networkState,
        readyState: video.readyState,
        src: video.src
      });

      // If the video URL is a presigned URL that might have expired
      if (videoUrl && videoUrl.includes('X-Amz-Signature')) {
        // Try a direct URL without the query parameters
        const directUrl = videoUrl.replace(/\?.*$/, '');
        console.log('Video error, trying direct URL:', directUrl);
        setVideoUrl(directUrl);
        setError(`Trying alternative source...`);
        return; // Don't show the error yet, wait for the direct URL to load
      }
    }

    setError(`Failed to load video. Please try again later.`);
    if (onError) onError(e);
  };

  // We're using native video controls, so no need for custom controls

  return (
    <Paper elevation={3} sx={{ overflow: 'hidden', bgcolor: 'background.paper' }}>
      {/* Video container */}
      <Box
        sx={{ position: 'relative', width: '100%', bgcolor: 'black' }}
        onClick={handlePlayPause}
      >
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
          src={videoUrl}
          poster={poster || '/video-placeholder.svg'}
          style={{ width: '100%', display: 'block' }}
          playsInline // Better mobile experience
          crossOrigin="use-credentials" // Use credentials for cross-origin requests
          controls // Use native controls
          preload="auto" // Preload the video
          onError={handleError}
          tabIndex="0" // Make it focusable
          aria-label={title || 'Video player'} // Add accessible label
        />
      </Box>

      {/* Video title */}
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

AuthenticatedVideoPlayer.propTypes = {
  src: PropTypes.string,
  title: PropTypes.string,
  poster: PropTypes.string,
  onError: PropTypes.func
};

export default AuthenticatedVideoPlayer;
