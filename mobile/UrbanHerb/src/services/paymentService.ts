import axios from 'axios';

interface PaymentData {
  amount: number;
  currency: string;
  method: string;
}

interface PaymentResponse {
  success: boolean;
  transactionId: string;
}

export const initiatePayment = async (paymentData: PaymentData): Promise<PaymentResponse> => {
  try {
    const response = await axios.post('/api/payments/initiate', paymentData);
    return response.data;
  } catch (error) {
    throw new Error('Payment failed');
  }
}; 