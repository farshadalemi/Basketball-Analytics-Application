import React, { createContext, useState, useContext, useEffect } from 'react';
import { getUserFromStorage } from '../models/auth';
import { login as loginUser, logout as logoutUser, checkAuth, register as registerUser } from '../controllers/authController';
import axios from 'axios';

// Create auth context
const AuthContext = createContext();

/**
 * Auth provider component
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const verifyAuth = async () => {
      try {
        const userData = await checkAuth();
        setUser(userData);
      } catch (error) {
        console.error('Auth verification failed:', error);
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

  // Set authentication token for all future requests
  useEffect(() => {
    if (user && user.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${user.token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [user]);

  // Login handler
  const login = async (email, password) => {
    try {
      const userData = await loginUser(
        email,
        password,
        (userData) => setUser(userData)
      );
      return userData;
    } catch (error) {
      throw error;
    }
  };

  // Register handler
  const register = async (email, username, password) => {
    try {
      return await registerUser(
        { email, username, password },
        () => {}
      );
    } catch (error) {
      throw error;
    }
  };

  // Logout handler
  const logout = () => {
    logoutUser();
    setUser(null);
  };

  // Context value
  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    register
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Hook to use auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
