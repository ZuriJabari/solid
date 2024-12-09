// API Configuration
export const API_URL = 'http://localhost:8000/api';

// Authentication
export const TOKEN_KEY = '@urbanherb:token';
export const USER_KEY = '@urbanherb:user';

// Theme Colors
export const COLORS = {
  primary: '#2E7D32',
  secondary: '#81C784',
  background: '#F5F6F8',
  text: '#333333',
  error: '#D32F2F',
  success: '#388E3C',
  white: '#FFFFFF',
  black: '#000000',
  gray: '#666666',
  lightGray: '#E0E0E0',
};

export const API_ENDPOINTS = {
  LOGIN: '/auth/login/',
  REGISTER: '/auth/register/',
  HERBS: '/products/herbs/',
  CART: '/cart/',
  ORDERS: '/orders/',
  PROFILE: '/accounts/profile/',
};

export const ROUTES = {
  HOME: 'Home',
  HERBS: 'Herbs',
  CART: 'Cart',
  PROFILE: 'Profile',
  HERB_DETAILS: 'HerbDetails',
  LOGIN: 'Login',
  REGISTER: 'Register',
}; 