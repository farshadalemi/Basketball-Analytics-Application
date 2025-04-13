import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, createRoutesFromElements } from 'react-router-dom';
import { UNSAFE_DataRouterContext, UNSAFE_DataRouterStateContext } from 'react-router';
import { CssBaseline } from '@mui/material';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import ErrorBoundary from './views/components/common/ErrorBoundary';
import Loading from './views/components/common/Loading';
import setupFetchInterceptor from './utils/fetchInterceptor';
import MainLayout from './views/components/layout/MainLayout';

// Set React Router future flags
UNSAFE_DataRouterContext.displayName = 'DataRouterContext';
UNSAFE_DataRouterStateContext.displayName = 'DataRouterStateContext';
window.__reactRouterFutureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true
};


// Lazy load page components
const LoginPage = React.lazy(() => import('./views/pages/LoginPage'));
const RegisterPage = React.lazy(() => import('./views/pages/RegisterPage'));
const Dashboard = React.lazy(() => import('./views/pages/Dashboard'));
const MyVideosPage = React.lazy(() => import('./views/pages/MyVideosPage'));
const VideoDetailsPage = React.lazy(() => import('./views/pages/VideoDetailsPage'));
const UploadVideoPage = React.lazy(() => import('./views/pages/UploadVideoPage'));
const ProfilePage = React.lazy(() => import('./views/pages/ProfilePage'));

// Scouting report pages
const ScoutingReportPage = React.lazy(() => import('./views/pages/ScoutingReportPage'));
const ReportDetailsPage = React.lazy(() => import('./views/pages/ReportDetailsPage'));

// Admin pages
const AdminDashboard = React.lazy(() => import('./views/pages/admin/AdminDashboard'));
const UserManagement = React.lazy(() => import('./views/pages/admin/UserManagement'));
const VideoManagement = React.lazy(() => import('./views/pages/admin/VideoManagement'));

/**
 * Protected route component
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <Loading />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return children;
};

/**
 * Main application component
 */
const App = () => {
  // Set up fetch interceptor
  useEffect(() => {
    setupFetchInterceptor();
  }, []);
  return (
    <ErrorBoundary>
      <Router>
        <ThemeProvider>
          <CssBaseline />
          <AuthProvider>
            <ToastProvider>
              <Suspense fallback={<Loading />}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />

                  {/* Protected routes with layout */}
                  <Route element={
                    <ProtectedRoute>
                      <MainLayout />
                    </ProtectedRoute>
                  }>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/videos" element={<MyVideosPage />} />
                    <Route path="/videos/:id" element={<VideoDetailsPage />} />
                    <Route path="/upload" element={<UploadVideoPage />} />
                    <Route path="/profile" element={<ProfilePage />} />

                    {/* Scouting Report Routes */}
                    <Route path="/scouting" element={<ScoutingReportPage />} />
                    <Route path="/scouting/reports/:reportId" element={<ReportDetailsPage />} />

                    {/* Admin Routes */}
                    <Route path="/admin" element={<AdminDashboard />} />
                    <Route path="/admin/users" element={<UserManagement />} />
                    <Route path="/admin/videos" element={<VideoManagement />} />
                  </Route>

                  {/* Fallback route */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </Router>
    </ErrorBoundary>
  );
};

export default App;
