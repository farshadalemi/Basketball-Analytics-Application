# Error Handling in Basketball Analytics Frontend

This document explains how error handling is implemented in the frontend to properly display user-friendly error messages from the backend.

## Overview

The error handling system is designed to:

1. Catch API errors
2. Extract user-friendly messages from the backend response
3. Display these messages to users via toast notifications
4. Provide consistent error handling across the application

## Key Components

### 1. Error Handler (`/src/utils/errorHandler.js`)

Extracts user-friendly error messages from API responses:

```javascript
export const getErrorMessage = (error, defaultMessage = "An unexpected error occurred") => {
  if (error.response && error.response.data && error.response.data.message) {
    return error.response.data.message;  // Use backend message if available
  }
  
  // Fallback to status-based messages
  // ...
};
```

### 2. Toast Component (`/src/components/Toast.js`)

Displays notifications to users:

```javascript
const Toast = ({ message, type = 'info', duration = 3000, onClose }) => {
  // ...
};
```

### 3. Toast Context (`/src/context/ToastContext.js`)

Manages toast notifications throughout the app:

```javascript
export const useToast = () => {
  // Access toast methods: showError, showSuccess, etc.
};
```

### 4. API Wrapper (`/src/utils/apiWrapper.js`)

Wraps API calls with error handling:

```javascript
export const withErrorHandling = async (apiCall, options) => {
  try {
    const response = await apiCall();
    return response;
  } catch (error) {
    // Extract and display error message
    const errorMessage = getErrorMessage(error, options.defaultErrorMsg);
    options.showError(errorMessage);
    throw error;
  }
};
```

### 5. Enhanced API Services (`/src/services/apiService.js`)

Provides API services with integrated error handling:

```javascript
export const useVideoService = () => {
  // Access methods: getVideos, uploadVideo, etc. with error handling
};
```

## Usage Examples

### Basic Usage

```jsx
import { useVideoService } from '../services/apiService';

const VideoUpload = () => {
  const videoService = useVideoService();

  const handleUpload = async (file) => {
    try {
      await videoService.uploadVideo('My Video', 'Description', file);
      // Success! Error handling is automatically integrated
    } catch (error) {
      // Additional error handling if needed (errors are already displayed as toasts)
    }
  };
};
```

### Custom Error Handling

```jsx
import { useApi } from '../services/apiService';

const CustomComponent = () => {
  const api = useApi();
  
  const handleSpecialRequest = async () => {
    try {
      await api.post('/special-endpoint', data, {}, {
        defaultErrorMsg: "Custom error message",
        onError: (error, message) => {
          // Custom error handler
        }
      });
    } catch (error) {
      // Handle any additional logic
    }
  };
};
```

## Error Response Format

The backend returns error responses in this format:

```json
{
  "message": "User-friendly error message",
  "error": "Technical error details (only in development)"
}
```

The frontend automatically extracts and displays the "message" field to users. 