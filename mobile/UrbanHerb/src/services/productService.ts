import axios from 'axios';
import { API_URL } from '../config/constants';

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  inStock: boolean;
  details: {
    origin: string;
    benefits: string[];
    usage: string;
    storage: string;
  };
}

class ProductService {
  async getProducts(): Promise<Product[]> {
    try {
      const response = await axios.get(`${API_URL}/products`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getProductById(id: string): Promise<Product> {
    try {
      const response = await axios.get(`${API_URL}/products/${id}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getProductsByCategory(category: string): Promise<Product[]> {
    try {
      const response = await axios.get(`${API_URL}/products?category=${category}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async searchProducts(query: string): Promise<Product[]> {
    try {
      const response = await axios.get(`${API_URL}/products/search?q=${query}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || 'An error occurred';
      return new Error(message);
    }
    return error;
  }
}

export const productService = new ProductService(); 