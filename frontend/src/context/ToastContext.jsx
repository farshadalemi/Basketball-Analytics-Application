import React, { createContext, useState, useContext } from 'react';
import { Snackbar, Alert } from '@mui/material';

// Create the context
const ToastContext = createContext();

/**
 * Hook to use the toast context
 */
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

/**
 * Provider component for toast notifications
 */
export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'info',
    duration: 6000
  });

  // Show a success toast
  const showSuccess = (message, duration = 6000) => {
    setToast({
      open: true,
      message,
      severity: 'success',
      duration
    });
  };

  // Show an error toast
  const showError = (message, duration = 6000) => {
    setToast({
      open: true,
      message,
      severity: 'error',
      duration
    });
  };

  // Show an info toast
  const showInfo = (message, duration = 6000) => {
    setToast({
      open: true,
      message,
      severity: 'info',
      duration
    });
  };

  // Show a warning toast
  const showWarning = (message, duration = 6000) => {
    setToast({
      open: true,
      message,
      severity: 'warning',
      duration
    });
  };

  // Close the toast
  const handleClose = () => {
    setToast((prev) => ({ ...prev, open: false }));
  };

  return (
    <ToastContext.Provider
      value={{
        showSuccess,
        showError,
        showInfo,
        showWarning
      }}
    >
      {children}
      <Snackbar
        open={toast.open}
        autoHideDuration={toast.duration}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          onClose={handleClose}
          severity={toast.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  );
};

export default ToastContext; 