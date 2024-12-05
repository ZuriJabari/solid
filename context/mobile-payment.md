# Mobile Payment Implementation

### 1. Payment Screen (screens/checkout/PaymentScreen.tsx)
```typescript
import React, { useState } from 'react';
import { View, ScrollView } from 'react-native';
import { Text, Button, RadioButton, Surface } from 'react-native-paper';
import { useCart } from '../../hooks/useCart';
import { createOrder } from '../../services/api';
import { formatCurrency } from '../../utils/format';

const PaymentScreen = ({ navigation, route }) => {
  const { cartTotal } = useCart();
  const { deliveryData } = route.params;
  const [paymentMethod, setPaymentMethod] = useState('');
  const [loading, setLoading] = useState(false);

  const paymentMethods = [
    {
      id: 'FLUTTERWAVE',
      name: 'Card Payment',
      icon: 'credit-card',
      description: 'Pay securely with your credit/debit card',
    },
    {
      id: 'MTN_MOMO',
      name: 'MTN Mobile Money',
      icon: 'phone',
      description: 'Pay using MTN Mobile Money',
    },
    {
      id: 'AIRTEL_MONEY',
      name: 'Airtel Money',
      icon: 'phone',
      description: 'Pay using Airtel Money',
    },
  ];

  const handlePayment = async () => {
    try {
      setLoading(true);
      const orderData = {
        ...deliveryData,
        payment_method: paymentMethod,
      };

      const response = await createOrder(orderData);

      if (paymentMethod === 'FLUTTERWAVE') {
        navigation.navigate('PaymentWebview', {
          url: response.payment.authorization_url,
          orderNumber: response.order.order_number,
        });
      } else {
        // Handle mobile money flow
        navigation.navigate('MobileMoneyPayment', {
          orderNumber: response.order.order_number,
          amount: cartTotal,
          provider: paymentMethod,
        });
      }
    } catch (error) {
      console.error('Payment error:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="flex-1 bg-white">
      <ScrollView className="flex-1">
        <View className="p-4 space-y-4">
          <Text variant="titleLarge">Select Payment Method</Text>

          <Surface className="p-4 rounded-lg">
            <Text variant="titleMedium" className="mb-2">
              Order Summary
            </Text>
            <View className="space-y-2">
              <View className="flex-row justify-between">
                <Text>Subtotal</Text>
                <Text>{formatCurrency(cartTotal)}</Text>
              </View>
              <View className="flex-row justify-between">
                <Text>Delivery Fee</Text>
                <Text>{formatCurrency(deliveryData.delivery_fee)}</Text>
              </View>
              <View className="flex-row justify-between border-t border-gray-200 pt-2">
                <Text className="font-bold">Total</Text>
                <Text className="font-bold">
                  {formatCurrency(cartTotal + deliveryData.delivery_fee)}
                </Text>
              </View>
            </View>
          </Surface>

          <View className="space-y-4">
            {paymentMethods.map((method) => (
              <Surface key={method.id} className="rounded-lg overflow-hidden">
                <RadioButton.Item
                  label={method.name}
                  value={method.id}
                  status={paymentMethod === method.id ? 'checked' : 'unchecked'}
                  onPress={() => setPaymentMethod(method.id)}
                  className="p-4"
                />
                <View className="px-4 pb-4">
                  <Text className="text-gray-600">{method.description}</Text>
                </View>
              </Surface>
            ))}
          </View>
        </View>
      </ScrollView>

      <View className="p-4 border-t border-gray-200">
        <Button
          mode="contained"
          onPress={handlePayment}
          loading={loading}
          disabled={!paymentMethod || loading}
        >
          Pay {formatCurrency(cartTotal + deliveryData.delivery_fee)}
        </Button>
      </View>
    </View>
  );
};

export default PaymentScreen;
```

### 2. Payment Webview Screen (screens/checkout/PaymentWebviewScreen.tsx)
```typescript
import React from 'react';
import { View } from 'react-native';
import { WebView } from 'react-native-webview';
import { useNavigation } from '@react-navigation/native';

const PaymentWebviewScreen = ({ route }) => {
  const navigation = useNavigation();
  const { url, orderNumber } = route.params;

  const handleNavigationStateChange = (navState) => {
    // Check if we've reached the callback URL
    if (navState.url.includes('/payment/callback')) {
      // Extract status from URL parameters
      const status = new URL(navState.url).searchParams.get('status');
      
      if (status === 'successful') {
        navigation.replace('PaymentSuccess', { orderNumber });
      } else {
        navigation.replace('PaymentFailure', { orderNumber });
      }
    }
  };

  return (
    <View className="flex-1">
      <WebView
        source={{ uri: url }}
        onNavigationStateChange={handleNavigationStateChange}
        startInLoadingState={true}
        javaScriptEnabled={true}
        domStorageEnabled={true}
      />
    </View>
  );
};

export default PaymentWebviewScreen;
```

### 3. Mobile Money Payment Screen (screens/checkout/MobileMoneyPaymentScreen.tsx)
```typescript
import React, { useState, useEffect } from 'react';
import { View } from 'react-native';
import { Text, TextInput, Button, Surface } from 'react-native-paper';
import { checkPaymentStatus } from '../../services/api';

const MobileMoneyPaymentScreen = ({ route, navigation }) => {
  const { orderNumber, amount, provider } = route.params;
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('PENDING');

  useEffect(() => {
    if (status === 'PENDING') {
      const interval = setInterval(async () => {
        try {
          const response = await checkPaymentStatus(orderNumber);
          if (response.status !== 'PENDING') {
            setStatus(response.status);
            if (response.status === 'SUCCESSFUL') {
              navigation.replace('PaymentSuccess', { orderNumber });
            } else if (response.status === 'FAILED') {
              navigation.replace('PaymentFailure', { orderNumber });
            }
          }
        } catch (error) {
          console.error('Error checking payment status:', error);
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [status, orderNumber]);

  const handlePayment = async () => {
    try {
      setLoading(true);
      await initiateMoneyPayment({
        orderNumber,
        phoneNumber,
        provider,
        amount,
      });
      // Show instructions dialog
    } catch (error) {
      console.error('Mobile money payment error:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="flex-1 bg-white p-4">
      <Surface className="p-4 rounded-lg mb-4">
        <Text variant="titleMedium" className="mb-2">
          Payment Details
        </Text>
        <View className="space-y-2">
          <View className="flex-row justify-between">
            <Text>Amount</Text>
            <Text className="font-bold">{formatCurrency(amount)}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text>Provider</Text>
            <Text>{provider.replace('_', ' ')}</Text>
          </View>
        </View>
      </Surface>

      <TextInput
        label="Phone Number"
        value={phoneNumber}
        onChangeText={setPhoneNumber}
        keyboardType="phone-pad"
        mode="outlined"
        className="mb-4"
      />

      <Button
        mode="contained"
        onPress={handlePayment}
        loading={loading}
        disabled={!phoneNumber || loading}
      >
        Pay Now
      </Button>

      {status === 'PENDING' && (
        <View className="mt-4">
          <Text className="text-center text-gray-600">
            Waiting for payment confirmation...
          </Text>
        </View>
      )}
    </View>
  );
};

export default MobileMoneyPaymentScreen;
```

This implementation provides:
1. Multiple payment methods (Card, MTN Mobile Money, Airtel Money)
2. Real-time payment status checking
3. Secure payment processing with Flutterwave
4. Mobile money integration
5. Clear payment status feedback
6. Error handling and retry options

Next, we can implement:
1. Order confirmation screens
2. Email notifications
3. Order tracking
4. Delivery status updates

Would you like me to continue with any of these features?