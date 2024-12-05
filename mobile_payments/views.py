from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from orders.models import CustomerOrder
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification
from .serializers import (
    MobilePaymentProviderSerializer, MobilePaymentSerializer,
    PaymentNotificationSerializer, InitiatePaymentSerializer,
    CheckPaymentStatusSerializer
)
from .providers import get_provider, PaymentError
import logging

logger = logging.getLogger(__name__)

class MobilePaymentProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for listing available payment providers"""
    queryset = MobilePaymentProvider.objects.filter(is_active=True)
    serializer_class = MobilePaymentProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # For debugging, print the queryset
        qs = MobilePaymentProvider.objects.filter(is_active=True)
        print("\nViewSet queryset:", qs.values_list('name', 'is_active'))
        return qs

class MobilePaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mobile money payments"""
    serializer_class = MobilePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments by user"""
        return MobilePayment.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a new mobile money payment"""
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get order
            order = get_object_or_404(
                CustomerOrder,
                id=serializer.validated_data['order_id'],
                user=request.user
            )
            
            # Get provider
            provider = get_provider(serializer.validated_data['provider_code'])
            provider_model = provider.provider
            
            # Create payment record
            payment = MobilePayment.objects.create(
                user=request.user,
                order=order,
                provider=provider_model,
                amount=order.total,
                currency='UGX',
                phone_number=serializer.validated_data['phone_number']
            )
            
            # Initiate payment with provider
            result = provider.initiate_payment(payment)
            
            return Response({
                'message': 'Payment initiated successfully',
                'payment': MobilePaymentSerializer(payment).data,
                'provider_response': result
            })
            
        except PaymentError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to initiate payment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def check_status(self, request):
        """Check payment status"""
        serializer = CheckPaymentStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get payment
            payment = get_object_or_404(
                MobilePayment,
                provider_tx_ref=serializer.validated_data['provider_tx_ref'],
                user=request.user
            )
            
            # Get provider
            provider = get_provider(payment.provider.code)
            
            # Check payment status
            result = provider.check_payment_status(payment)
            
            return Response({
                'payment': MobilePaymentSerializer(payment).data,
                'provider_response': result
            })
            
        except PaymentError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to check payment status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentWebhookView(viewsets.ViewSet):
    """ViewSet for handling payment webhooks"""
    permission_classes = []  # No authentication required for webhooks
    
    @action(detail=False, methods=['post'])
    def mtn(self, request):
        """Handle MTN Mobile Money webhooks"""
        try:
            provider = get_provider('MTN')
            signature = request.headers.get('X-Signature', '')
            
            if not provider.validate_notification(request.data, signature):
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get payment from notification
            payment = get_object_or_404(
                MobilePayment,
                provider_tx_ref=request.data.get('referenceId')
            )
            
            # Create notification record
            notification = PaymentNotification.objects.create(
                payment=payment,
                provider=payment.provider,
                notification_type='PAYMENT_STATUS',
                status=request.data.get('status'),
                raw_payload=request.data
            )
            
            # Process notification
            provider.process_notification(notification)
            
            return Response({'status': 'success'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def airtel(self, request):
        """Handle Airtel Money webhooks"""
        try:
            provider = get_provider('AIRTEL')
            signature = request.headers.get('X-Auth-Token', '')
            
            if not provider.validate_notification(request.data, signature):
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get transaction data
            transaction = request.data.get('transaction', {})
            if not transaction:
                return Response(
                    {'error': 'Missing transaction data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get payment from notification
            payment = get_object_or_404(
                MobilePayment,
                provider_tx_ref=transaction.get('id')
            )
            
            # Map Airtel status to our status
            status_mapping = {
                'SUCCESS': 'SUCCESSFUL',
                'FAILED': 'FAILED',
                'CANCELLED': 'CANCELLED'
            }
            
            # Create notification record
            notification = PaymentNotification.objects.create(
                payment=payment,
                provider=payment.provider,
                notification_type='PAYMENT_STATUS',
                status=status_mapping.get(transaction.get('status', ''), 'FAILED'),
                raw_payload=request.data
            )
            
            # Process notification
            provider.process_notification(notification)
            
            return Response({'status': 'success'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
