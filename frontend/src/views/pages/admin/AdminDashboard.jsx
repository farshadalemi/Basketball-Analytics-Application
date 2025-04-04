import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Button,
} from '@mui/material';
import {
  PeopleOutline as UsersIcon,
  VideoLibrary as VideosIcon,
  Storage as StorageIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../../context/AuthContext';
import { useToast } from '../../../context/ToastContext';
import { getSystemStats, getUserStats, getStorageStats } from '../../../controllers/adminController';

// Stat Card Component
const StatCard = ({ title, value, icon, color }) => {
  const theme = useTheme();
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Avatar sx={{ bgcolor: color || theme.palette.primary.main }}>
              {icon}
            </Avatar>
          </Grid>
          <Grid item xs>
            <Typography variant="h6" component="div">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {value}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Admin Dashboard Page
const AdminDashboard = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { showError } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [systemStats, setSystemStats] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  
  // Check if user is admin
  useEffect(() => {
    if (isAuthenticated && user && !user.is_admin) {
      showError('You do not have permission to access the admin panel');
      navigate('/');
    }
  }, [isAuthenticated, user, navigate, showError]);
  
  // Load statistics
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        
        // Fetch all stats in parallel
        const [systemData, userData, storageData] = await Promise.all([
          getSystemStats(),
          getUserStats(),
          getStorageStats()
        ]);
        
        setSystemStats(systemData);
        setUserStats(userData);
        setStorageStats(storageData);
      } catch (error) {
        console.error('Error loading admin statistics:', error);
        showError('Failed to load admin statistics');
      } finally {
        setLoading(false);
      }
    };
    
    if (isAuthenticated && user?.is_admin) {
      fetchStats();
    }
  }, [isAuthenticated, user, showError]);
  
  // Show loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }
  
  // Show error if no stats
  if (!systemStats || !userStats || !storageStats) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <WarningIcon color="error" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            Failed to load statistics
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => window.location.reload()}
            sx={{ mt: 2 }}
          >
            Retry
          </Button>
        </Paper>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      
      {/* User Statistics */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        User Statistics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Users" 
            value={userStats.total_users} 
            icon={<UsersIcon />} 
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Active Users" 
            value={userStats.active_users} 
            icon={<UsersIcon />} 
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Inactive Users" 
            value={userStats.inactive_users} 
            icon={<UsersIcon />} 
            color={theme.palette.error.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Admin Users" 
            value={userStats.admin_users} 
            icon={<UsersIcon />} 
            color={theme.palette.secondary.main}
          />
        </Grid>
      </Grid>
      
      {/* Video Statistics */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Content Statistics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Videos" 
            value={systemStats.video_stats.total_videos} 
            icon={<VideosIcon />} 
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Completed Videos" 
            value={systemStats.video_stats.completed_videos} 
            icon={<VideosIcon />} 
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Processing Videos" 
            value={systemStats.video_stats.processing_videos} 
            icon={<VideosIcon />} 
            color={theme.palette.warning.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Failed Videos" 
            value={systemStats.video_stats.failed_videos} 
            icon={<VideosIcon />} 
            color={theme.palette.error.main}
          />
        </Grid>
      </Grid>
      
      {/* Storage Statistics */}
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Storage Statistics
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard 
            title="Total Storage (MB)" 
            value={storageStats.total_storage_mb.toFixed(2)} 
            icon={<StorageIcon />} 
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard 
            title="Total Videos" 
            value={storageStats.total_videos} 
            icon={<VideosIcon />} 
            color={theme.palette.info.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard 
            title="Avg Video Size (MB)" 
            value={storageStats.avg_video_size_mb.toFixed(2)} 
            icon={<StorageIcon />} 
            color={theme.palette.secondary.main}
          />
        </Grid>
      </Grid>
      
      {/* Top Users */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Top Users by Content
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {userStats.top_users_by_content.map((user, index) => (
                <ListItem key={user.id} divider={index < userStats.top_users_by_content.length - 1}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                      <PersonIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={user.username}
                    secondary={`${user.email} • ${user.video_count} videos`}
                  />
                </ListItem>
              ))}
              {userStats.top_users_by_content.length === 0 && (
                <ListItem>
                  <ListItemText primary="No users with content found" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Top Storage Users
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              {storageStats.top_storage_users.map((user, index) => (
                <ListItem key={user.id} divider={index < storageStats.top_storage_users.length - 1}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: theme.palette.secondary.main }}>
                      <StorageIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={user.username}
                    secondary={`${user.storage_used_mb.toFixed(2)} MB • ${user.video_count} videos`}
                  />
                </ListItem>
              ))}
              {storageStats.top_storage_users.length === 0 && (
                <ListItem>
                  <ListItemText primary="No storage usage data found" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Admin Actions */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => navigate('/admin/users')}
        >
          Manage Users
        </Button>
        <Button 
          variant="contained" 
          color="secondary"
          onClick={() => navigate('/admin/videos')}
        >
          Manage Videos
        </Button>
      </Box>
    </Container>
  );
};

export default AdminDashboard;
