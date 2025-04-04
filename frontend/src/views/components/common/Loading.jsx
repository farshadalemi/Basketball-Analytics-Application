import React from 'react';
import { CircularProgress, Box, Typography } from '@mui/material';

/**
 * Loading spinner component
 * @param {Object} props - Component props
 * @param {number} props.size - Size of the spinner
 * @param {string} props.message - Optional message to display
 */
const Loading = ({ size = 40, message = '' }) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      minHeight="200px"
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default Loading;
