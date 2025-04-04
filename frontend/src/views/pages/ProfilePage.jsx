import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  TextField,
  Typography,
  CircularProgress,
  Avatar
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { PersonOutline as PersonIcon } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { getUserProfile, updateUserProfile } from '../../controllers/userController';

/**
 * User Profile Page
 */
const ProfilePage = () => {
  const theme = useTheme();
  const { user, isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  // Load user profile
  useEffect(() => {
    const fetchProfile = async () => {
      if (!isAuthenticated) return;

      try {
        setLoading(true);
        const userData = await getUserProfile(
          (data) => {
            console.log('Profile data loaded successfully:', data);
          },
          (error) => {
            console.error('Error in profile callback:', error);
            showError('Failed to load profile: ' + error);
          }
        );

        if (userData) {
          setProfile(userData);
          setFormData({
            username: userData.username || '',
            email: userData.email || '',
            password: '',
            confirmPassword: ''
          });
        }
      } catch (error) {
        showError('Failed to load profile');
        console.error('Error loading profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isAuthenticated, showError]);

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate passwords match if provided
    if (formData.password && formData.password !== formData.confirmPassword) {
      showError('Passwords do not match');
      return;
    }

    // Prepare update data (only include fields that have changed)
    const updateData = {};
    if (formData.username !== profile.username) updateData.username = formData.username;
    if (formData.email !== profile.email) updateData.email = formData.email;
    if (formData.password) updateData.password = formData.password;

    // Skip if no changes
    if (Object.keys(updateData).length === 0) {
      showSuccess('No changes to save');
      return;
    }

    try {
      setSaving(true);
      const updatedProfile = await updateUserProfile(updateData);
      setProfile(updatedProfile);
      setFormData({
        ...formData,
        password: '',
        confirmPassword: ''
      });
      showSuccess('Profile updated successfully');
    } catch (error) {
      showError('Failed to update profile');
      console.error('Error updating profile:', error);
    } finally {
      setSaving(false);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        My Profile
      </Typography>

      <Grid container spacing={3}>
        {/* Profile Summary Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  margin: '0 auto 16px',
                  bgcolor: theme.palette.primary.main
                }}
              >
                <PersonIcon fontSize="large" />
              </Avatar>

              <Typography variant="h5" gutterBottom>
                {profile?.username || 'User'}
              </Typography>

              <Typography variant="body2" color="textSecondary">
                {profile?.email || 'No email'}
              </Typography>

              {profile?.is_admin && (
                <Typography
                  variant="body2"
                  sx={{
                    mt: 1,
                    color: theme.palette.secondary.main,
                    fontWeight: 'bold'
                  }}
                >
                  Administrator
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Profile Edit Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Edit Profile
              </Typography>

              <Divider sx={{ mb: 3 }} />

              <Box component="form" onSubmit={handleSubmit} noValidate>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Username"
                      name="username"
                      value={formData.username}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Change Password (leave blank to keep current)
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="New Password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Confirm Password"
                      name="confirmPassword"
                      type="password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      disabled={saving}
                      sx={{ mt: 2 }}
                    >
                      {saving ? <CircularProgress size={24} /> : 'Save Changes'}
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ProfilePage;
