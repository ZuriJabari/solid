from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification
from .serializers import (
    MobilePaymentProviderSerializer, MobilePaymentSerializer,
    PaymentNotificationSerializer, InitiatePaymentSerializer,
    CheckPaymentStatusSerializer
)
from .providers import get_provider, PaymentError
from orders.models import Order

class MobilePaymentProviderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobilePaymentProvider.objects.filter(is_active=True)
    serializer_class = MobilePaymentProviderSerializer
    permission_classes = [IsAuthenticated]

class MobilePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = MobilePaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MobilePayment.objects.filter(
            user=self.request.user
        ).select_related('provider')

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                order = Order.objects.get(
                    id=serializer.validated_data['order_id'],
                    user=request.user
                )
                
                provider = get_provider(
                    serializer.validated_data['provider_code']
                )
                
                # Create payment record
                payment = MobilePayment.objects.create(
                    user=request.user,
                    order=order,
                    provider=provider.provider,
                    amount=order.total,
                    currency='UGX',
                    phone_number=serializer.validated_data['phone_number']
                )
                
                # Initiate payment with provider
                result = provider.initiate_payment(payment)
                
                return Response(
                    MobilePaymentSerializer(payment).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except PaymentError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False)
    def check_status(self, request):
        serializer = CheckPaymentStatusSerializer(data=request.data)
        if serializer.is_valid():
            try:
                payment = MobilePayment.objects.get(
                    provider_tx_ref=serializer.validated_data['provider_tx_ref'],
                    user=request.user
                )
                
                provider = get_provider(payment.provider.code)
                result = provider.check_payment_status(payment)
                
                return Response(
                    MobilePaymentSerializer(payment).data
                )
                
            except MobilePayment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except PaymentError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class PaymentWebhookView(viewsets.ViewSet):
    permission_classes = []  # Public endpoint
    
    def _handle_webhook(self, request, provider_code):
        try:
            provider = get_provider(provider_code)
            signature = request.headers.get('X-Webhook-Signature')
            
            if not provider.validate_notification(request.data, signature):
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create notification record
            notification = PaymentNotification.objects.create(
                provider=provider.provider,
                notification_type=request.data.get('type'),
                status=request.data.get('status'),
                raw_payload=request.data
            )
            
            # Process notification
            provider.process_notification(notification)
            
            return Response({'status': 'success'})
            
        except PaymentError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def mtn(self, request):
        return self._handle_webhook(request, 'MTN')
    
    @action(detail=False, methods=['post'])
    def airtel(self, request):
        return self._handle_webhook(request, 'AIRTEL')
