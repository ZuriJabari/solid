import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_KEY } from '../config/constants';

// Use your computer's local IP address
const BASE_URL = 'http://172.20.10.2:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh or logout here
      await AsyncStorage.removeItem(TOKEN_KEY);
    }
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const fetchHerbs = async () => {
  try {
    const response = await api.get('/api/products/products/');
    console.log('API Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching herbs:', error);
    throw error;
  }
};

export const fetchHerbDetails = async (herbId: number) => {
  try {
    const response = await api.get(`/api/products/products/${herbId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching herb details:', error);
    throw error;
  }
};

export default api; 