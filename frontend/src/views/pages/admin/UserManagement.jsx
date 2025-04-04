import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Block as BlockIcon,
  Delete as DeleteIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../../context/AuthContext';
import { useToast } from '../../../context/ToastContext';
import { getUsers } from '../../../controllers/userController';
import { activateUser, deactivateUser, deleteUser } from '../../../controllers/adminController';

// User Management Page
const UserManagement = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialog states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [blockDialogOpen, setBlockDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionType, setActionType] = useState('');
  
  // Check if user is admin
  useEffect(() => {
    if (isAuthenticated && user && !user.is_admin) {
      showError('You do not have permission to access the admin panel');
      navigate('/');
    }
  }, [isAuthenticated, user, navigate, showError]);
  
  // Load users
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const data = await getUsers();
        setUsers(data);
        setFilteredUsers(data);
      } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users');
      } finally {
        setLoading(false);
      }
    };
    
    if (isAuthenticated && user?.is_admin) {
      fetchUsers();
    }
  }, [isAuthenticated, user, showError]);
  
  // Filter users based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredUsers(users);
      return;
    }
    
    const query = searchQuery.toLowerCase();
    const filtered = users.filter(
      user => 
        user.username.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query)
    );
    
    setFilteredUsers(filtered);
  }, [searchQuery, users]);
  
  // Handle search input change
  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };
  
  // Handle user activation/deactivation
  const handleToggleActive = (user) => {
    setSelectedUser(user);
    setActionType(user.is_active ? 'deactivate' : 'activate');
    setBlockDialogOpen(true);
  };
  
  // Handle user deletion
  const handleDeleteClick = (user) => {
    setSelectedUser(user);
    setActionType('delete');
    setDeleteDialogOpen(true);
  };
  
  // Confirm user activation/deactivation
  const confirmToggleActive = async () => {
    if (!selectedUser) return;
    
    try {
      if (selectedUser.is_active) {
        // Deactivate user
        await deactivateUser(
          selectedUser.id,
          () => {
            showSuccess(`User ${selectedUser.username} has been deactivated`);
            // Update local state
            setUsers(users.map(u => 
              u.id === selectedUser.id ? { ...u, is_active: false } : u
            ));
            setFilteredUsers(filteredUsers.map(u => 
              u.id === selectedUser.id ? { ...u, is_active: false } : u
            ));
          },
          (error) => showError(error)
        );
      } else {
        // Activate user
        await activateUser(
          selectedUser.id,
          () => {
            showSuccess(`User ${selectedUser.username} has been activated`);
            // Update local state
            setUsers(users.map(u => 
              u.id === selectedUser.id ? { ...u, is_active: true } : u
            ));
            setFilteredUsers(filteredUsers.map(u => 
              u.id === selectedUser.id ? { ...u, is_active: true } : u
            ));
          },
          (error) => showError(error)
        );
      }
    } catch (error) {
      console.error('Error toggling user status:', error);
    } finally {
      setBlockDialogOpen(false);
      setSelectedUser(null);
    }
  };
  
  // Confirm user deletion
  const confirmDelete = async () => {
    if (!selectedUser) return;
    
    try {
      await deleteUser(
        selectedUser.id,
        () => {
          showSuccess(`User ${selectedUser.username} has been deleted`);
          // Update local state
          setUsers(users.filter(u => u.id !== selectedUser.id));
          setFilteredUsers(filteredUsers.filter(u => u.id !== selectedUser.id));
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error deleting user:', error);
    } finally {
      setDeleteDialogOpen(false);
      setSelectedUser(null);
    }
  };
  
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
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          User Management
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => navigate('/admin')}
        >
          Back to Dashboard
        </Button>
      </Box>
      
      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search users by name or email..."
          value={searchQuery}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>
      
      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.length > 0 ? (
              filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.id}</TableCell>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    {user.is_admin ? (
                      <Chip 
                        icon={<AdminIcon />} 
                        label="Admin" 
                        color="secondary" 
                        size="small" 
                      />
                    ) : (
                      <Chip 
                        icon={<UserIcon />} 
                        label="User" 
                        color="primary" 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    {user.is_active ? (
                      <Chip 
                        icon={<ActiveIcon />} 
                        label="Active" 
                        color="success" 
                        size="small" 
                      />
                    ) : (
                      <Chip 
                        icon={<InactiveIcon />} 
                        label="Inactive" 
                        color="error" 
                        size="small" 
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {!user.is_admin && (
                      <>
                        <Tooltip title={user.is_active ? "Deactivate User" : "Activate User"}>
                          <IconButton 
                            color={user.is_active ? "error" : "success"}
                            onClick={() => handleToggleActive(user)}
                            disabled={user.id === selectedUser?.id}
                          >
                            {user.is_active ? <BlockIcon /> : <ActiveIcon />}
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Delete User">
                          <IconButton 
                            color="error"
                            onClick={() => handleDeleteClick(user)}
                            disabled={user.id === selectedUser?.id}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No users found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Block/Unblock Dialog */}
      <Dialog
        open={blockDialogOpen}
        onClose={() => setBlockDialogOpen(false)}
      >
        <DialogTitle>
          {actionType === 'deactivate' ? 'Deactivate User' : 'Activate User'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {actionType === 'deactivate' 
              ? `Are you sure you want to deactivate ${selectedUser?.username}? They will no longer be able to log in.`
              : `Are you sure you want to activate ${selectedUser?.username}? They will be able to log in again.`
            }
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBlockDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmToggleActive} 
            color={actionType === 'deactivate' ? 'error' : 'success'}
            variant="contained"
          >
            {actionType === 'deactivate' ? 'Deactivate' : 'Activate'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete {selectedUser?.username}? This action cannot be undone and will also delete all their content.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmDelete} 
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;
