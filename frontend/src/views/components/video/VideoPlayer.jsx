import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Paper,
  CircularProgress,
  Alert,
  Slider,
  Stack,
  Button,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  VolumeOff,
  Fullscreen
} from '@mui/icons-material';
import { formatDuration } from '../../../models/video';

/**
 * Video player component
 * @param {Object} props - Component props
 * @param {string} props.src - Video source URL
 * @param {string} props.title - Video title
 * @param {string} props.poster - Video poster/thumbnail URL
 */
const VideoPlayer = ({ src, title, poster }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [controlsVisible, setControlsVisible] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isExtraSmall = useMediaQuery('(max-width:400px)');

  // Handle play/pause
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Handle mute/unmute
  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  // Handle volume change
  const handleVolumeChange = (_, newValue) => {
    if (videoRef.current) {
      videoRef.current.volume = newValue;
      setVolume(newValue);
      setIsMuted(newValue === 0);
    }
  };

  // Handle seek
  const handleSeek = (_, newValue) => {
    if (videoRef.current) {
      videoRef.current.currentTime = newValue;
      setCurrentTime(newValue);
    }
  };

  // Handle fullscreen
  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  // Error handler for video loading issues
  const handleError = (e) => {
    console.error('Video error:', e);
    setLoading(false);
    setError(`Failed to load video. Please try again later.`);

    // Try to get more detailed error information
    if (videoRef.current) {
      const video = videoRef.current;
      console.log('Video element error details:', {
        error: video.error,
        networkState: video.networkState,
        readyState: video.readyState,
        src: video.src
      });
    }
  };

  // Update time display
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleDurationChange = () => {
      setDuration(video.duration);
    };

    const handleLoadedData = () => {
      setLoading(false);
      setDuration(video.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      video.currentTime = 0;
    };

    // Add event listeners
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('error', handleError);

    // Clean up
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('error', handleError);
    };
  }, []);

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 2, bgcolor: 'background.paper' }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  // Show/hide controls on mobile
  const showControls = () => {
    if (isMobile) {
      setControlsVisible(true);
      // Auto-hide controls after 3 seconds
      setTimeout(() => setControlsVisible(false), 3000);
    }
  };

  return (
    <Paper elevation={3} sx={{ overflow: 'hidden', bgcolor: 'background.paper' }}>
      {/* Video container */}
      <Box
        sx={{ position: 'relative', width: '100%', bgcolor: 'black' }}
        onClick={() => {
          togglePlay();
          showControls();
        }}
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

        <video
          ref={videoRef}
          src={src}
          poster={poster || '/video-placeholder.svg'}
          style={{ width: '100%', display: 'block' }}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          playsInline // Better mobile experience
          crossOrigin="use-credentials" // Use credentials for cross-origin requests
          controls // Use native controls for now
          preload="auto" // Preload the video
          onError={handleError} // Handle video errors
        />

        {/* If there's an error, show a retry button */}
        {error && (
          <Button
            variant="contained"
            color="primary"
            sx={{ mt: 2 }}
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
        )}

        {/* Video title overlay */}
        {title && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              p: { xs: 0.5, sm: 1 },
              background: 'linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)',
              color: 'white'
            }}
          >
            <Typography
              variant={isMobile ? "body2" : "subtitle1"}
              sx={{
                px: 1,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}
            >
              {title}
            </Typography>
          </Box>
        )}

        {/* Controls overlay */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            p: { xs: 0.5, sm: 1 },
            background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)',
            color: 'white',
            opacity: isMobile ? (controlsVisible ? 1 : 0) : 0.9,
            transition: 'opacity 0.3s',
            '&:hover': {
              opacity: 1
            }
          }}
          onClick={(e) => e.stopPropagation()} // Prevent video toggle when clicking controls
        >
          {/* Progress bar */}
          <Slider
            value={currentTime}
            max={duration || 100}
            onChange={handleSeek}
            aria-label="Video progress"
            size="small"
            sx={{
              color: 'primary.main',
              height: 4,
              padding: { xs: '5px 0', sm: '10px 0' },
              '& .MuiSlider-thumb': {
                width: isMobile ? 6 : 8,
                height: isMobile ? 6 : 8,
                display: { xs: 'none', sm: 'block' },
                '&:hover, &.Mui-focusVisible': {
                  boxShadow: '0px 0px 0px 8px rgba(25, 118, 210, 0.16)'
                },
                '&.Mui-active': {
                  display: 'block'
                }
              }
            }}
          />

          {/* Controls */}
          <Stack
            direction="row"
            spacing={{ xs: 0.5, sm: 1 }}
            alignItems="center"
            sx={{ px: { xs: 0.5, sm: 1 } }}
          >
            <IconButton
              color="inherit"
              onClick={togglePlay}
              size={isMobile ? "small" : "medium"}
              sx={{ p: { xs: 0.5, sm: 1 } }}
            >
              {isPlaying ? <Pause fontSize={isMobile ? "small" : "medium"} /> : <PlayArrow fontSize={isMobile ? "small" : "medium"} />}
            </IconButton>

            {/* Volume control - hide on extra small screens */}
            {!isExtraSmall && (
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                width: { xs: 80, sm: 120 },
                ml: { xs: 0, sm: 1 }
              }}>
                <IconButton
                  color="inherit"
                  onClick={toggleMute}
                  size={isMobile ? "small" : "medium"}
                  sx={{ p: { xs: 0.5, sm: 1 } }}
                >
                  {isMuted ?
                    <VolumeOff fontSize={isMobile ? "small" : "medium"} /> :
                    <VolumeUp fontSize={isMobile ? "small" : "medium"} />}
                </IconButton>
                <Slider
                  value={isMuted ? 0 : volume}
                  min={0}
                  max={1}
                  step={0.1}
                  onChange={handleVolumeChange}
                  aria-label="Volume"
                  size="small"
                  sx={{
                    ml: { xs: 0.5, sm: 1 },
                    color: 'white',
                    '& .MuiSlider-thumb': {
                      width: isMobile ? 6 : 8,
                      height: isMobile ? 6 : 8,
                      display: { xs: 'none', sm: 'block' },
                      '&:hover, &.Mui-active': {
                        display: 'block'
                      }
                    }
                  }}
                />
              </Box>
            )}

            <Typography
              variant="caption"
              sx={{
                flexGrow: 1,
                textAlign: 'center',
                fontSize: { xs: '0.65rem', sm: '0.75rem' },
                display: { xs: isExtraSmall ? 'none' : 'block', sm: 'block' }
              }}
            >
              {formatDuration(currentTime)} / {formatDuration(duration)}
            </Typography>

            <IconButton
              color="inherit"
              onClick={toggleFullscreen}
              size={isMobile ? "small" : "medium"}
              sx={{ p: { xs: 0.5, sm: 1 } }}
            >
              <Fullscreen fontSize={isMobile ? "small" : "medium"} />
            </IconButton>
          </Stack>
        </Box>
      </Box>
    </Paper>
  );
};

export default VideoPlayer;
