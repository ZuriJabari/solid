import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface PaymentState {
  initiating: boolean;
  currentPayment: any | null;
  error: string | null;
}

const initialState: PaymentState = {
  initiating: false,
  currentPayment: null,
  error: null,
};

const paymentSlice = createSlice({
  name: 'payment',
  initialState,
  reducers: {
    initiatePaymentStart: (state) => {
      state.initiating = true;
      state.error = null;
    },
    initiatePaymentSuccess: (state, action: PayloadAction<any>) => {
      state.initiating = false;
      state.currentPayment = action.payload;
      state.error = null;
    },
    initiatePaymentFailure: (state, action: PayloadAction<string>) => {
      state.initiating = false;
      state.error = action.payload;
    },
  },
});

export const {
  initiatePaymentStart,
  initiatePaymentSuccess,
  initiatePaymentFailure,
} = paymentSlice.actions;

export default paymentSlice.reducer; 