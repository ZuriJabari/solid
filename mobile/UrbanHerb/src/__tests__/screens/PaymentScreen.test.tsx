import React from 'react';
import { render } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { NavigationContainer } from '@react-navigation/native';
import PaymentScreen from '../../screens/PaymentScreen';
import { configureStore } from '@reduxjs/toolkit';
import paymentReducer from '../../store/paymentSlice';

const mockStore = configureStore({
  reducer: {
    payment: paymentReducer,
  },
});

describe('PaymentScreen', () => {
  it('renders correctly', () => {
    const { getByText } = render(
      <Provider store={mockStore}>
        <NavigationContainer>
          <PaymentScreen />
        </NavigationContainer>
      </Provider>
    );
    expect(getByText('Select Payment Method')).toBeTruthy();
  });
}); 