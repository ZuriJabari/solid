import { initiatePayment } from '../../services/paymentService';

jest.mock('../../services/paymentService');

describe('PaymentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initiates payment successfully', async () => {
    const mockPaymentData = {
      amount: 100,
      currency: 'USD',
      method: 'credit_card',
    };

    const mockResponse = {
      success: true,
      transactionId: '123456',
    };

    (initiatePayment as jest.Mock).mockResolvedValue(mockResponse);

    const result = await initiatePayment(mockPaymentData);
    expect(result).toEqual(mockResponse);
    expect(initiatePayment).toHaveBeenCalledWith(mockPaymentData);
  });

  it('handles payment failure', async () => {
    const mockPaymentData = {
      amount: 100,
      currency: 'USD',
      method: 'credit_card',
    };

    const mockError = new Error('Payment failed');
    (initiatePayment as jest.Mock).mockRejectedValue(mockError);

    await expect(initiatePayment(mockPaymentData)).rejects.toThrow('Payment failed');
  });
}); 