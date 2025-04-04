/**
 * User model
 * Handles user data and operations
 */

/**
 * Format user data from API response
 * @param {Object} userData - Raw user data from API
 * @returns {Object} Formatted user data
 */
export const formatUserData = (userData) => {
  if (!userData) return null;
  
  return {
    id: userData.id,
    email: userData.email,
    username: userData.username || userData.email,
    isAdmin: userData.is_admin || false,
    isActive: userData.is_active !== false
  };
};

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if email is valid
 */
export const isValidEmail = (email) => {
  if (!email) return false;
  
  // Basic email validation regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {Object} Validation result with isValid and message
 */
export const validatePassword = (password) => {
  if (!password) {
    return { 
      isValid: false, 
      message: 'Password is required' 
    };
  }
  
  if (password.length < 6) {
    return { 
      isValid: false, 
      message: 'Password must be at least 6 characters long' 
    };
  }
  
  return { 
    isValid: true, 
    message: '' 
  };
};

/**
 * Validate registration form data
 * @param {Object} formData - Registration form data
 * @returns {Object} Validation result with isValid and errors
 */
export const validateRegistration = (formData) => {
  const errors = {};
  
  // Validate email
  if (!formData.email) {
    errors.email = 'Email is required';
  } else if (!isValidEmail(formData.email)) {
    errors.email = 'Invalid email format';
  }
  
  // Validate username
  if (!formData.username) {
    errors.username = 'Username is required';
  } else if (formData.username.length < 3) {
    errors.username = 'Username must be at least 3 characters long';
  }
  
  // Validate password
  const passwordValidation = validatePassword(formData.password);
  if (!passwordValidation.isValid) {
    errors.password = passwordValidation.message;
  }
  
  // Validate password confirmation
  if (formData.password !== formData.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
