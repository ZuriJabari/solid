// API Configuration
export const BASE_URL = 'http://172.20.10.2:8000';

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
  LOGIN: '/api/auth/login/',
  REGISTER: '/api/auth/register/',
  PRODUCTS: '/api/products/products/',
  CATEGORIES: '/api/products/categories/',
  CART: '/api/cart/',
  ORDERS: '/api/orders/',
  PROFILE: '/api/auth/profile/',
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