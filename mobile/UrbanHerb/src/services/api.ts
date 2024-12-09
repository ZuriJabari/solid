import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TOKEN_KEY } from '../config/constants';

const BASE_URL = 'http://127.0.0.1:8002/api';

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
    return Promise.reject(error);
  }
);

export const fetchHerbs = async () => {
  try {
    const response = await api.get('/products/herbs/');
    return response.data;
  } catch (error) {
    console.error('Error fetching herbs:', error);
    throw error;
  }
};

export const fetchHerbDetails = async (herbId: number) => {
  try {
    const response = await api.get(`/products/herbs/${herbId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching herb details:', error);
    throw error;
  }
};

export default api; 