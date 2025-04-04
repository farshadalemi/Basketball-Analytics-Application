import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useTheme } from '../../../context/ThemeContext';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  IconButton,
  Button,
  useMediaQuery,
  useTheme as useMuiTheme,
  Tooltip
} from '@mui/material';
import {
  Menu as MenuIcon,
  VideoLibrary as VideoIcon,
  CloudUpload as UploadIcon,
  Logout as LogoutIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon
} from '@mui/icons-material';
import Sidebar from './Sidebar';

/**
 * Main layout component with app bar and sidebar
 */
const MainLayout = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { mode, toggleTheme } = useTheme();
  const muiTheme = useMuiTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));
  const isSmallMobile = useMediaQuery(muiTheme.breakpoints.down('sm'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ px: { xs: 1, sm: 2 } }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleSidebar}
            sx={{ mr: { xs: 1, sm: 2 } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontSize: { xs: '1rem', sm: '1.25rem' },
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {isSmallMobile ? 'BB Analytics' : 'Basketball Analytics'}
          </Typography>

          {/* Theme toggle button */}
          <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
            <IconButton
              color="inherit"
              onClick={toggleTheme}
              sx={{ ml: { xs: 0.5, sm: 1 }, mr: { xs: 0.5, sm: 1 } }}
              size={isSmallMobile ? 'small' : 'medium'}
            >
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Upload button */}
          <Button
            color="inherit"
            startIcon={<UploadIcon />}
            onClick={() => navigate('/upload')}
            sx={{
              mr: { xs: 0.5, sm: 1 },
              display: { xs: 'none', sm: 'flex' },
              px: { sm: 1, md: 2 }
            }}
            size={isSmallMobile ? 'small' : 'medium'}
          >
            Upload
          </Button>

          {/* Upload icon for mobile */}
          <IconButton
            color="inherit"
            onClick={() => navigate('/upload')}
            sx={{
              mr: { xs: 0.5, sm: 1 },
              display: { xs: 'flex', sm: 'none' }
            }}
            size={isSmallMobile ? 'small' : 'medium'}
          >
            <UploadIcon />
          </IconButton>

          {/* Logout button */}
          <Tooltip title="Logout">
            <IconButton
              color="inherit"
              onClick={handleLogout}
              size={isSmallMobile ? 'small' : 'medium'}
            >
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClose={toggleSidebar} />

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 1, sm: 2, md: 3 },
          width: { sm: `calc(100% - ${sidebarOpen ? 240 : 0}px)` },
          ml: { sm: sidebarOpen ? '240px' : 0 },
          mt: { xs: '56px', sm: '64px' },  // Adjust for different AppBar heights
          transition: muiTheme.transitions.create(['width', 'margin'], {
            easing: muiTheme.transitions.easing.sharp,
            duration: muiTheme.transitions.duration.leavingScreen,
          }),
          overflow: 'auto'
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
