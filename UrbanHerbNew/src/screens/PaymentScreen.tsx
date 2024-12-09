import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, RadioButton, Button } from 'react-native-paper';
import { useDispatch } from 'react-redux';
import { initiatePaymentStart, initiatePaymentSuccess, initiatePaymentFailure } from '../store/paymentSlice';
import { initiatePayment } from '../services/paymentService';

const PaymentScreen = () => {
  const [paymentMethod, setPaymentMethod] = useState('credit_card');
  const dispatch = useDispatch();

  const handlePayment = async () => {
    try {
      dispatch(initiatePaymentStart());
      const response = await initiatePayment({
        amount: 100,
        currency: 'USD',
        method: paymentMethod,
      });
      dispatch(initiatePaymentSuccess(response));
    } catch (error) {
      dispatch(initiatePaymentFailure('Payment failed. Please try again.'));
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Select Payment Method</Text>
      
      <RadioButton.Group onValueChange={value => setPaymentMethod(value)} value={paymentMethod}>
        <View style={styles.radioItem}>
          <RadioButton.Android value="credit_card" testID="payment-method-credit-card" />
          <Text>Credit Card</Text>
        </View>
        <View style={styles.radioItem}>
          <RadioButton.Android value="paypal" testID="payment-method-paypal" />
          <Text>PayPal</Text>
        </View>
      </RadioButton.Group>

      <Button mode="contained" onPress={handlePayment} style={styles.button}>
        Pay Now
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  button: {
    marginTop: 24,
  },
});

export default PaymentScreen; 