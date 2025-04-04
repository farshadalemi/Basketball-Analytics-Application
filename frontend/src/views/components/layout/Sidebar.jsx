import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Typography,
  useTheme,
  useMediaQuery,
  Avatar
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  VideoLibrary as VideoIcon,
  CloudUpload as UploadIcon,
  Person as UserIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminIcon,
  PeopleOutline as UsersIcon
} from '@mui/icons-material';

/**
 * Sidebar component for navigation
 */
const Sidebar = ({ open, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const theme = useTheme();

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/'
    },
    {
      text: 'My Videos',
      icon: <VideoIcon />,
      path: '/videos'
    },
    {
      text: 'Upload Video',
      icon: <UploadIcon />,
      path: '/upload'
    }
  ];

  const accountItems = [
    {
      text: 'Profile',
      icon: <UserIcon />,
      path: '/profile',
      disabled: false
    },
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      path: '/settings',
      disabled: true // Keep settings disabled for now
    }
  ];

  // Admin items (only shown to admin users)
  const adminItems = [
    {
      text: 'Admin Dashboard',
      icon: <AdminIcon />,
      path: '/admin'
    },
    {
      text: 'Manage Users',
      icon: <UsersIcon />,
      path: '/admin/users'
    },
    {
      text: 'Manage Videos',
      icon: <VideoIcon />,
      path: '/admin/videos'
    }
  ];

  const handleNavigation = (path) => {
    navigate(path);
    if (window.innerWidth < 600) {
      onClose();
    }
  };

  const drawerWidth = 240;
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Drawer
      variant={isMobile ? "temporary" : "persistent"}
      anchor="left"
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: { xs: '85%', sm: drawerWidth },
          maxWidth: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: theme.spacing(0, 1),
        ...theme.mixins.toolbar
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
          {user && (
            <Avatar
              sx={{
                width: 32,
                height: 32,
                mr: 1,
                bgcolor: 'primary.main',
                fontSize: '0.875rem'
              }}
            >
              {user.username ? user.username[0].toUpperCase() : 'U'}
            </Avatar>
          )}
          <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
            {user ? (user.username || 'User') : 'Menu'}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <ChevronLeftIcon />
        </IconButton>
      </Box>

      <Divider />

      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              disabled={item.disabled}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      <List>
        <ListItem>
          <Typography variant="body2" color="text.secondary">
            Account
          </Typography>
        </ListItem>
        {accountItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              disabled={item.disabled}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Admin Navigation - Only shown to admin users */}
      {user?.is_admin && (
        <>
          <Divider />
          <List>
            <ListItem>
              <Typography variant="body2" color="text.secondary">
                Admin Panel
              </Typography>
            </ListItem>
            {adminItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => handleNavigation(item.path)}
                >
                  <ListItemIcon>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Drawer>
  );
};

export default Sidebar;
