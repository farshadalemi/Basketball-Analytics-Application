import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ENDPOINTS } from '../config/api';

// Create auth context
const AuthContext = createContext(null);

/**
 * Auth provider component
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Set up axios interceptor for authentication
  useEffect(() => {
    // Add a request interceptor to include the token in all requests
    const interceptor = axios.interceptors.request.use(
      (config) => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const userData = JSON.parse(userStr);
          if (userData.token) {
            config.headers.Authorization = `Bearer ${userData.token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add a response interceptor to handle authentication errors
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          // Unauthorized - clear user data and redirect to login
          console.log('Authentication error, redirecting to login');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/login');
        }
        return Promise.reject(error);
      }
    );

    // Clean up interceptors when component unmounts
    return () => {
      axios.interceptors.request.eject(interceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, [navigate]);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const userData = JSON.parse(userStr);

          // Set default auth header
          axios.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`;

          // Fetch current user data
          const response = await axios.get(ENDPOINTS.AUTH.ME);
          setUser(response.data);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('user');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   */
  const login = async (email, password) => {
    try {
      console.log('AuthContext: Attempting login for', email);

      // Create URLSearchParams for proper form encoding
      const formData = new URLSearchParams();
      formData.append('username', email);    // OAuth2 expects 'username'
      formData.append('password', password);

      const response = await axios.post(ENDPOINTS.AUTH.LOGIN, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      if (response.data && response.data.access_token) {
        console.log('AuthContext: Login successful, saving user data');

        const userData = {
          token: response.data.access_token,
          type: response.data.token_type,
          user: response.data.user || { email }
        };

        localStorage.setItem('user', JSON.stringify(userData));

        // Set auth header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`;

        setUser(userData.user);
        return true;
      } else {
        console.error('AuthContext: Invalid response format', response.data);
        return false;
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  /**
   * Logout user
   */
  const logout = () => {
    localStorage.removeItem('user');
    setUser(null);
    navigate('/login');
  };

  // Show loading state
  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isAuthenticated: !!user,
      loading
    }}>
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