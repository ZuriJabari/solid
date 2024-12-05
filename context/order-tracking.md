# Order Confirmation and Tracking Implementation

## Backend Implementation

### 1. Order Status Management (orders/services.py)
```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order

class OrderService:
    @staticmethod
    def send_confirmation_email(order: Order) -> None:
        context = {
            'order': order,
            'items': order.items.all().select_related('product'),
            'total': order.total,
            'delivery_info': OrderService.get_delivery_info(order),
            'legal_notices': OrderService.get_legal_notices(),
        }
        
        html_content = render_to_string('emails/order_confirmation.html', context)
        
        send_mail(
            subject=f'Order Confirmation - {order.order_number}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_content
        )

    @staticmethod
    def update_order_status(order: Order, status: str, notify: bool = True) -> None:
        old_status = order.status
        order.status = status
        order.save()

        if notify:
            OrderService.send_status_update_email(order, old_status)
            OrderService.send_status_update_sms(order)

    @staticmethod
    def get_delivery_info(order: Order) -> dict:
        if order.delivery_type == 'DELIVERY':
            return {
                'type': 'Home Delivery',
                'address': order.delivery_address,
                'instructions': order.delivery_instructions,
                'verification_required': True,
                'age_check_required': True,
            }
        else:
            return {
                'type': 'Store Pickup',
                'location': order.pickup_location,
                'pickup_time': order.pickup_time,
                'verification_required': True,
                'id_required': True,
            }

    @staticmethod
    def get_legal_notices() -> list:
        return [
            'Must be 18 or older to receive delivery',
            'Valid ID required for pickup/delivery',
            'Products are for personal use only',
            'Keep products away from children',
        ]

class DeliveryService:
    @staticmethod
    def assign_delivery(order: Order) -> None:
        # Logic to assign delivery personnel
        pass

    @staticmethod
    def update_delivery_status(order: Order, location=None) -> None:
        # Update real-time delivery status
        pass

    @staticmethod
    def verify_delivery(order: Order, verification_data: dict) -> bool:
        # Verify age and identity at delivery
        pass
```

### 2. Order Tracking Views (orders/views.py)
```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderTrackingSerializer

class OrderTrackingView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderTrackingSerializer
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderTrackingSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
```

## Frontend Implementation (Web)

### 1. Order Confirmation Page (pages/OrderConfirmationPage.tsx)
```typescript
import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchOrder } from '../services/api';
import { ReceiptIcon, TruckIcon, MapPinIcon } from 'lucide-react';

const OrderConfirmationPage = () => {
  const { orderNumber } = useParams();
  const { data: order, isLoading } = useQuery(
    ['order', orderNumber],
    () => fetchOrder(orderNumber)
  );

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <div className="text-center mb-8">
        <div className="mb-4">
          <div className="h-12 w-12 mx-auto bg-green-100 rounded-full flex items-center justify-center">
            <ReceiptIcon className="h-6 w-6 text-green-600" />
          </div>
        </div>
        <h1 className="text-3xl font-bold">Order Confirmed!</h1>
        <p className="text-gray-600 mt-2">Order #{orderNumber}</p>
      </div>

      <div className="space-y-6">
        {/* Order Summary */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium mb-4">Order Summary</h2>
          <div className="space-y-4">
            {order.items.map((item) => (
              <div key={item.id} className="flex justify-between">
                <div>
                  <p className="font-medium">{item.product.name}</p>
                  <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                </div>
                <p className="font-medium">${item.total}</p>
              </div>
            ))}
            <div className="border-t pt-4">
              <div className="flex justify-between">
                <p>Subtotal</p>
                <p className="font-medium">${order.subtotal}</p>
              </div>
              <div className="flex justify-between mt-2">
                <p>Delivery Fee</p>
                <p className="font-medium">${order.delivery_fee}</p>
              </div>
              <div className="flex justify-between mt-2 font-bold">
                <p>Total</p>
                <p>${order.total}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Delivery Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium mb-4">
            {order.delivery_type === 'DELIVERY' ? 'Delivery' : 'Pickup'} Information
          </h2>
          {order.delivery_type === 'DELIVERY' ? (
            <div className="space-y-4">
              <div className="flex items-start">
                <MapPinIcon className="h-5 w-5 text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="font-medium">Delivery Address</p>
                  <p className="text-gray-600">{order.delivery_address}</p>
                </div>
              </div>
              <div className="flex items-start">
                <TruckIcon className="h-5 w-5 text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="font-medium">Delivery Instructions</p>
                  <p className="text-gray-600">{order.delivery_instructions}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start">
                <MapPinIcon className="h-5 w-5 text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="font-medium">Pickup Location</p>
                  <p className="text-gray-600">{order.pickup_location.address}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Important Notices */}
        <div className="bg-yellow-50 rounded-lg p-6">
          <h2 className="text-lg font-medium text-yellow-800 mb-4">
            Important Information
          </h2>
          <ul className="space-y-2 text-yellow-700">
            <li>• Valid ID required for {order.delivery_type.toLowerCase()}</li>
            <li>• Must be 18 or older to receive products</li>
            <li>• Keep products in original packaging</li>
            <li>• Store in a cool, dry place away from children</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmationPage;
```

### 2. Order Tracking Page (pages/OrderTrackingPage.tsx)
```typescript
import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchOrderTracking } from '../services/api';

const OrderTrackingPage = () => {
  const { orderNumber } = useParams();
  const { data: tracking, isLoading } = useQuery(
    ['orderTracking', orderNumber],
    () => fetchOrderTracking(orderNumber),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  if (isLoading) return <div>Loading...</div>;

  const steps = [
    { status: 'CONFIRMED', label: 'Order Confirmed' },
    { status: 'PROCESSING', label: 'Processing Order' },
    { status: tracking?.delivery_type === 'DELIVERY' ? 'OUT_FOR_DELIVERY' : 'READY_FOR_PICKUP', 
      label: tracking?.delivery_type === 'DELIVERY' ? 'Out for Delivery' : 'Ready for Pickup' },
    { status: 'COMPLETED', label: 'Completed' },
  ];

  const currentStepIndex = steps.findIndex(step => step.status === tracking.status);

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <h1 className="text-2xl font-bold mb-8">Track Your Order</h1>

      {/* Progress Steps */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="h-0.5 w-full bg-gray-200" />
        </div>
        <div className="relative flex justify-between">
          {steps.map((step, index) => (
            <div key={step.status} className="flex flex-col items-center">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center relative bg-white border-2 
                  ${index <= currentStepIndex ? 'border-indigo-600' : 'border-gray-300'}`}
              >
                {index < currentStepIndex ? (
                  <CheckIcon className="h-5 w-5 text-indigo-600" />
                ) : index === currentStepIndex ? (
                  <div className="h-2.5 w-2.5 rounded-full bg-indigo-600" />
                ) : null}
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900">{step.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Status Details */}
      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium mb-4">Status Updates</h2>
        <div className="space-y-4">
          {tracking.updates.map((update) => (
            <div key={update.id} className="flex items-start">
              <div className="min-w-[120px] text-sm text-gray-500">
                {new Date(update.timestamp).toLocaleString()}
              </div>
              <div className="ml-4">
                <p className="font-medium">{update.status}</p>
                <p className="text-sm text-gray-600">{update.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrderTrackingPage;
```

This implementation includes:
1. Detailed order confirmation with legal notices
2. Real-time order tracking
3. Age verification requirements
4. Delivery/pickup instructions
5. Email notifications
6. Status updates

Next, we can implement:
1. Mobile order tracking screens
2. Delivery personnel interface
3. Admin dashboard for order management
4. Analytics and reporting

Would you like me to continue with any of these features?