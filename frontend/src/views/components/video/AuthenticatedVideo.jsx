import React, { useEffect, useRef, forwardRef } from 'react';
import PropTypes from 'prop-types';

/**
 * A video component that handles authentication for API endpoints
 */
const AuthenticatedVideo = forwardRef(({ src, poster, onError, ...props }, ref) => {
  const localVideoRef = useRef(null);

  // Use the forwarded ref if provided, otherwise use the local ref
  const videoRef = ref || localVideoRef;

  // Get auth token from localStorage
  const getAuthToken = () => {
    try {
      const userData = localStorage.getItem('userData');
      if (userData) {
        const parsedData = JSON.parse(userData);
        return parsedData.token;
      }
      return null;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  useEffect(() => {
    // If the src is an API URL, we need to handle authentication
    if (src && src.includes('/api/') && videoRef.current) {
      const token = getAuthToken();
      if (token) {
        // Create a fetch request with the auth token
        fetch(src, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
          .then(response => {
            if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            if (data && data.streaming_url) {
              // Update the video src with the streaming URL
              videoRef.current.src = data.streaming_url;
              videoRef.current.load();
            } else {
              throw new Error('No streaming URL in response');
            }
          })
          .catch(error => {
            console.error('Error fetching video URL:', error);
            if (onError) onError(error);
          });
      }
    }
  }, [src, onError]);

  return (
    <video
      ref={videoRef}
      src={src && !src.includes('/api/') ? src : undefined}
      poster={poster}
      {...props}
    />
  );
});

AuthenticatedVideo.propTypes = {
  src: PropTypes.string,
  poster: PropTypes.string,
  onError: PropTypes.func
};

export default AuthenticatedVideo;
