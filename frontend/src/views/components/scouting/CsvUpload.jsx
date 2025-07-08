import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  IconButton,
  useTheme,
  useMediaQuery,
  Divider
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Close as CloseIcon,
  Description as FileIcon
} from '@mui/icons-material';

/**
 * CSV Upload component for FIBA live statistics
 */
const CsvUpload = ({ onFileSelect, onFileRemove, file, uploading, uploadProgress, error }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) {
      return;
    }

    // Validate file type
    const validTypes = ['text/csv', 'application/vnd.ms-excel'];
    const isValidType = validTypes.includes(selectedFile.type) || selectedFile.name.toLowerCase().endsWith('.csv');
    
    if (!isValidType) {
      if (onFileSelect) {
        onFileSelect(null, 'Please select a valid CSV file');
      }
      return;
    }

    // Validate file size (max 10MB for CSV)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      if (onFileSelect) {
        onFileSelect(null, 'File size exceeds 10MB limit');
      }
      return;
    }

    if (onFileSelect) {
      onFileSelect(selectedFile, null);
    }
  };

  // Handle file removal
  const handleRemoveFile = () => {
    if (onFileRemove) {
      onFileRemove();
    }
  };

  return (
    <Paper
      sx={{
        p: { xs: 2, sm: 3 },
        borderRadius: { xs: 1, sm: 2 },
        border: '2px dashed',
        borderColor: error ? 'error.main' : file ? 'success.main' : 'grey.300',
        bgcolor: error ? 'error.light' : file ? 'success.light' : 'grey.50',
        transition: 'all 0.3s ease'
      }}
      elevation={0}
    >
      <Typography
        variant={isMobile ? "subtitle1" : "h6"}
        sx={{ mb: 1, fontWeight: 500 }}
      >
        FIBA Live Statistics
      </Typography>
      
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 2 }}
      >
        Upload CSV file with basketball statistics from FIBA live scoring system
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {file ? (
        <Box>
          {/* File info */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              p: { xs: 1.5, sm: 2 },
              bgcolor: 'background.paper',
              borderRadius: 1,
              mb: 2
            }}
          >
            <FileIcon sx={{ mr: 1, color: 'success.main' }} />
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography
                variant="body2"
                noWrap
                sx={{ fontWeight: 500 }}
              >
                {file.name}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
              >
                {(file.size / 1024).toFixed(1)} KB
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleRemoveFile}
              disabled={uploading}
              sx={{ ml: 1 }}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* Upload progress */}
          {uploading && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress
                variant="determinate"
                value={uploadProgress}
                sx={{ mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                Uploading... {uploadProgress}%
              </Typography>
            </Box>
          )}
        </Box>
      ) : (
        <Box sx={{ textAlign: 'center', py: { xs: 2, sm: 3 } }}>
          <input
            accept=".csv,text/csv,application/vnd.ms-excel"
            style={{ display: 'none' }}
            id="csv-upload"
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <label htmlFor="csv-upload">
            <Button
              variant="outlined"
              component="span"
              startIcon={<UploadIcon />}
              disabled={uploading}
              size={isMobile ? "small" : "medium"}
              sx={{
                py: { xs: 1, sm: 1.5 },
                px: { xs: 2, sm: 3 }
              }}
            >
              Select CSV File
            </Button>
          </label>
          
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ 
              display: 'block', 
              mt: 1,
              fontSize: { xs: '0.7rem', sm: '0.75rem' }
            }}
          >
            Supported formats: CSV files up to 10MB
          </Typography>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />
      
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
      >
        <strong>Expected CSV format:</strong> Player stats with columns like Player Name, Points, Rebounds, Assists, etc.
      </Typography>
    </Paper>
  );
};

CsvUpload.propTypes = {
  onFileSelect: PropTypes.func,
  onFileRemove: PropTypes.func,
  file: PropTypes.object,
  uploading: PropTypes.bool,
  uploadProgress: PropTypes.number,
  error: PropTypes.string
};

CsvUpload.defaultProps = {
  uploading: false,
  uploadProgress: 0
};

export default CsvUpload;
