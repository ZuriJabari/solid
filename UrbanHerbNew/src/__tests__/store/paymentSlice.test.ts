import { configureStore } from '@reduxjs/toolkit';
import paymentReducer, {
  initiatePaymentStart,
  initiatePaymentSuccess,
  initiatePaymentFailure,
} from '../../store/paymentSlice';

interface TestStore {
  payment: ReturnType<typeof paymentReducer>;
}

let store: ReturnType<typeof configureStore>;

describe('paymentSlice', () => {
  beforeEach(() => {
    store = configureStore<TestStore>({
      reducer: {
        payment: paymentReducer,
      },
    });
  });

  it('handles payment initiation start', () => {
    store.dispatch(initiatePaymentStart());
    const state = store.getState().payment;

    expect(state.initiating).toBe(true);
    expect(state.error).toBeNull();
  });

  it('handles payment initiation success', () => {
    const mockPaymentData = {
      transactionId: '123456',
      amount: 100,
      status: 'completed',
    };

    store.dispatch(initiatePaymentSuccess(mockPaymentData));
    const state = store.getState().payment;

    expect(state.initiating).toBe(false);
    expect(state.currentPayment).toEqual(mockPaymentData);
    expect(state.error).toBeNull();
  });

  it('handles payment initiation failure', () => {
    const error = 'Payment initiation failed';
    store.dispatch(initiatePaymentFailure(error));
    const state = store.getState().payment;

    expect(state.initiating).toBe(false);
    expect(state.error).toBe(error);
  });
}); 