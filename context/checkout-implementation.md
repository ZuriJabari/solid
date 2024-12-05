# Checkout Process Implementation

## Backend Implementation

### 1. Order Models (orders/models.py)
```python
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PROCESSING', 'Processing'),
        ('CONFIRMED', 'Confirmed'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('READY_FOR_PICKUP', 'Ready for Pickup'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    DELIVERY_CHOICES = [
        ('DELIVERY', 'Home Delivery'),
        ('PICKUP', 'Store Pickup'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    
    # Delivery Information
    delivery_address = models.TextField(blank=True)
    delivery_location = gis_models.PointField(null=True, blank=True)
    delivery_instructions = models.TextField(blank=True)
    delivery_zone = models.ForeignKey('locations.DeliveryZone', 
                                    on_delete=models.SET_NULL,
                                    null=True, blank=True)
    
    # Pickup Information
    pickup_location = models.ForeignKey('locations.PickupLocation',
                                      on_delete=models.SET_NULL,
                                      null=True, blank=True)
    pickup_time = models.DateTimeField(null=True, blank=True)
    
    # Payment Information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='PENDING')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        import random
        import string
        prefix = 'CBD'
        random_chars = ''.join(random.choices(string.digits, k=8))
        return f"{prefix}{random_chars}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.ForeignKey(Order, related_name='payments', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    provider = models.CharField(max_length=50)  # e.g., 'FLUTTERWAVE', 'MTN_MOMO'
    reference = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. Checkout Views (orders/views.py)
```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .serializers import OrderCreateSerializer, OrderDetailSerializer
from .services import PaymentService, OrderService

class CheckoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Create order
            order = OrderService.create_order(
                user=request.user,
                cart_items=serializer.validated_data['items'],
                delivery_type=serializer.validated_data['delivery_type'],
                delivery_address=serializer.validated_data.get('delivery_address'),
                delivery_location=serializer.validated_data.get('delivery_location'),
                pickup_location=serializer.validated_data.get('pickup_location'),
                payment_method=serializer.validated_data['payment_method']
            )

            # Initialize payment
            payment = PaymentService.initialize_payment(
                order=order,
                payment_method=serializer.validated_data['payment_method']
            )

            return Response({
                'order': OrderDetailSerializer(order).data,
                'payment': {
                    'reference': payment.reference,
                    'authorization_url': payment.authorization_url
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(generics.CreateAPIView):
    permission_classes = []  # Public endpoint for payment provider

    def create(self, request, *args, **kwargs):
        try:
            PaymentService.handle_webhook(request.data)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

### 3. Payment Service (orders/services.py)
```python
from typing import Dict, Any
import requests
from django.conf import settings
from .models import Order, Payment

class PaymentService:
    @staticmethod
    def initialize_payment(order: Order, payment_method: str) -> Dict[str, Any]:
        if payment_method == 'FLUTTERWAVE':
            return FlutterwavePayment.initialize(order)
        elif payment_method == 'MTN_MOMO':
            return MobileMoneyPayment.initialize(order)
        raise ValueError(f"Unsupported payment method: {payment_method}")

    @staticmethod
    def handle_webhook(payload: Dict[str, Any]) -> None:
        # Verify webhook signature
        if not PaymentService.verify_webhook_signature(payload):
            raise ValueError("Invalid webhook signature")

        payment = Payment.objects.get(reference=payload['txRef'])
        
        if payload['status'] == 'successful':
            payment.status = 'SUCCESSFUL'
            payment.transaction_id = payload['transaction_id']
            payment.save()

            # Update order status
            payment.order.payment_status = 'PAID'
            payment.order.status = 'CONFIRMED'
            payment.order.save()

            # Send confirmation email
            OrderService.send_confirmation_email(payment.order)

class FlutterwavePayment:
    @staticmethod
    def initialize(order: Order) -> Dict[str, Any]:
        payload = {
            "tx_ref": order.order_number,
            "amount": float(order.total),
            "currency": "UGX",
            "redirect_url": f"{settings.FRONTEND_URL}/payment/callback",
            "payment_options": "card,mobilemoney",
            "meta": {
                "order_id": order.id
            },
            "customer": {
                "email": order.user.email,
                "name": f"{order.user.first_name} {order.user.last_name}",
                "phone_number": str(order.user.phone)
            },
            "customizations": {
                "title": "CBD Products Payment",
                "description": f"Payment for order {order.order_number}",
                "logo": settings.LOGO_URL
            }
        }

        response = requests.post(
            f"{settings.FLUTTERWAVE_API_URL}/payments",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
            }
        )
        
        data = response.json()
        
        if data['status'] == 'success':
            Payment.objects.create(
                order=order,
                amount=order.total,
                provider='FLUTTERWAVE',
                reference=order.order_number
            )
            
            return {
                'reference': order.order_number,
                'authorization_url': data['data']['link']
            }
        
        raise ValueError("Payment initialization failed")

class MobileMoneyPayment:
    @staticmethod
    def initialize(order: Order) -> Dict[str, Any]:
        # Similar implementation for MTN Mobile Money
        pass
```

## Frontend Implementation (Web)

### 1. Checkout Flow (src/pages/CheckoutPage.tsx)
```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../hooks/useCart';
import { createOrder } from '../services/api';
import DeliveryForm from '../components/checkout/DeliveryForm';
import PickupForm from '../components/checkout/PickupForm';
import PaymentForm from '../components/checkout/PaymentForm';

const CheckoutPage: React.FC = () => {
  const navigate = useNavigate();
  const { cartItems, cartTotal } = useCart();
  const [step, setStep] = useState(1);
  const [deliveryType, setDeliveryType] = useState<'DELIVERY' | 'PICKUP'>('DELIVERY');
  const [checkoutData, setCheckoutData] = useState({
    deliveryAddress: '',
    deliveryLocation: null,
    pickupLocation: null,
    paymentMethod: '',
  });

  const handleDeliverySubmit = (data) => {
    setCheckoutData((prev) => ({ ...prev, ...data }));
    setStep(2);
  };

  const handlePaymentSubmit = async (paymentData) => {
    try {
      const orderData = {
        items: cartItems.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        delivery_type: deliveryType,
        ...(deliveryType === 'DELIVERY' ? {
          delivery_address: checkoutData.deliveryAddress,
          delivery_location: checkoutData.deliveryLocation,
        } : {
          pickup_location: checkoutData.pickupLocation,
        }),
        payment_method: paymentData.method,
      };

      const response = await createOrder(orderData);
      
      // Handle payment based on selected method
      if (paymentData.method === 'FLUTTERWAVE') {
        window.location.href = response.payment.authorization_url;
      } else if (paymentData.method === 'MTN_MOMO') {
        navigate(`/payment/mobile/${response.order.order_number}`);
      }
    } catch (error) {
      console.error('Checkout error:', error);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8">
      <div className="space-y-8">
        {/* Progress Steps */}
        <nav className="flex items-center justify-center" aria-label="Progress">
          <ol className="flex items-center space-x-5">
            <li className={`${step >= 1 ? 'text-indigo-600' : 'text-gray-500'}`}>
              Delivery
            </li>
            <li className={`${step >= 2 ? 'text-indigo-600' : 'text-gray-500'}`}>
              Payment
            </li>
          </ol>
        </nav>

        {/* Step 1: Delivery */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="flex space-x-4">
              <button
                className={`flex-1 py-2 px-4 rounded-md ${
                  deliveryType === 'DELIVERY'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
                onClick={() => setDeliveryType('DELIVERY')}
              >
                Home Delivery
              </button>
              <button
                className={`flex-1 py-2 px-4 rounded-md ${
                  deliveryType === 'PICKUP'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
                onClick={() => setDeliveryType('PICKUP')}
              >
                Store Pickup
              </button>
            </div>

            {deliveryType === 'DELIVERY' ? (
              <DeliveryForm onSubmit={handleDeliverySubmit} />
            ) : (
              <PickupForm onSubmit={handleDeliverySubmit} />
            )}
          </div>
        )}

        {/* Step 2: Payment */}
        {step === 2 && (
          <PaymentForm
            amount={cartTotal}
            onSubmit={handlePaymentSubmit}
          />
        )}
      </div>
    </div>
  );
};

export default CheckoutPage;
```

## Mobile Implementation

### 1. Checkout Navigation (src/navigation/CheckoutNavigator.tsx)
```typescript
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import DeliveryScreen from '../screens/checkout/DeliveryScreen';
import PickupScreen from '../screens/checkout/PickupScreen';
import PaymentScreen from '../screens/checkout/PaymentScreen';
import PaymentWebviewScreen from '../screens/checkout/PaymentWebviewScreen';

const Stack = createStackNavigator();

const CheckoutNavigator = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Delivery" component={DeliveryScreen} />
      <Stack.Screen name="Pickup" component={PickupScreen} />
      <Stack.Screen name="Payment" component={PaymentScreen} />
      <Stack.Screen 
        name="PaymentWebview" 
        component={PaymentWebviewScreen}
        options={{ headerShown: false }}
      />
    </Stack.Navigator>
  );
};

export default CheckoutNavigator;
```

### 2. Payment Screen (src/screens/checkout/PaymentScreen.tsx)
```typescript
import React, { useState } from 'react';