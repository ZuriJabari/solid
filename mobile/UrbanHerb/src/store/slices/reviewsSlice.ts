import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../services/api';

interface Review {
  id: number;
  productId: number;
  userId: number;
  userName: string;
  rating: number;
  comment: string;
  createdAt: string;
  images?: string[];
}

interface ReviewsState {
  items: { [key: number]: Review[] }; // Keyed by productId
  loading: boolean;
  error: string | null;
}

const initialState: ReviewsState = {
  items: {},
  loading: false,
  error: null,
};

export const fetchProductReviews = createAsyncThunk(
  'reviews/fetchProductReviews',
  async (productId: number) => {
    const response = await api.get(`/products/${productId}/reviews/`);
    return { productId, reviews: response.data };
  }
);

export const addProductReview = createAsyncThunk(
  'reviews/addProductReview',
  async ({ productId, rating, comment, images }: any) => {
    const response = await api.post(`/products/${productId}/reviews/`, {
      rating,
      comment,
      images,
    });
    return response.data;
  }
);

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    clearReviews: (state) => {
      state.items = {};
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductReviews.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProductReviews.fulfilled, (state, action) => {
        state.loading = false;
        state.items[action.payload.productId] = action.payload.reviews;
      })
      .addCase(fetchProductReviews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch reviews';
      })
      .addCase(addProductReview.fulfilled, (state, action) => {
        const review = action.payload;
        if (!state.items[review.productId]) {
          state.items[review.productId] = [];
        }
        state.items[review.productId].unshift(review);
      });
  },
});

export const { clearReviews } = reviewsSlice.actions;
export default reviewsSlice.reducer; 