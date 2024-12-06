from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import MobilePayment, MobilePaymentProvider, PaymentNotification
from .serializers import (
    MobilePaymentSerializer, PaymentInitiateSerializer,
    PaymentStatusSerializer, PaymentNotificationSerializer,
    WebhookSerializer, AirtelWebhookSerializer, MTNWebhookSerializer
)
from .services import MobilePaymentService, PaymentValidationError, PaymentProcessingError
from orders.models import Order

@extend_schema_view(
    list=extend_schema(
        description='List all mobile payments for the current user',
        responses={200: MobilePaymentSerializer(many=True)}
    ),
    retrieve=extend_schema(
        description='Get a specific mobile payment by ID',
        responses={200: MobilePaymentSerializer}
    ),
)
class MobilePaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for managing mobile payments.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MobilePaymentSerializer

    def get_queryset(self):
        return MobilePayment.objects.filter(user=self.request.user)

    @extend_schema(
        description='Initiate a mobile payment',
        request=PaymentInitiateSerializer,
        responses={
            200: MobilePaymentSerializer,
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        }
    )
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                order = get_object_or_404(
                    Order,
                    id=serializer.validated_data['order_id'],
                    user=request.user
                )
                
                provider = serializer.validated_data['provider']
                service = MobilePaymentService(provider)
                
                payment = service.initiate_payment(
                    order=order,
                    phone_number=serializer.validated_data['phone_number']
                )
                
                return Response(MobilePaymentSerializer(payment).data)
                
            except PaymentValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except PaymentProcessingError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Check payment status',
        request=PaymentStatusSerializer,
        responses={
            200: MobilePaymentSerializer,
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        }
    )
    @action(detail=False, methods=['post'])
    def check_status(self, request):
        serializer = PaymentStatusSerializer(data=request.data)
        if serializer.is_valid():
            try:
                payment = get_object_or_404(
                    MobilePayment,
                    transaction_id=serializer.validated_data['transaction_id'],
                    user=request.user
                )
                
                service = MobilePaymentService(payment.provider)
                status_info = service.check_payment_status(payment)
                
                return Response(status_info)
                
            except PaymentProcessingError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Retry a failed payment',
        responses={
            200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        }
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        try:
            payment = get_object_or_404(MobilePayment, id=pk, user=request.user)
            
            service = MobilePaymentService(payment.provider)
            success = service.retry_failed_payment(payment)
            
            if success:
                return Response({'success': True})
            else:
                return Response(
                    {'error': 'Maximum retry attempts reached or payment not eligible for retry'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except PaymentProcessingError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(APIView):
    """
    API endpoint for payment provider webhooks.
    """
    permission_classes = []  # Public endpoint

    @extend_schema(
        description='Handle payment provider webhooks',
        request=WebhookSerializer,
        responses={
            200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        }
    )
    def post(self, request, provider_code):
        try:
            provider = get_object_or_404(MobilePaymentProvider, code=provider_code.upper())
            
            # Validate webhook signature
            # TODO: Implement webhook signature validation
            
            # Use appropriate serializer based on provider
            if provider.code == 'MTN':
                serializer = MTNWebhookSerializer(data=request.data)
            elif provider.code == 'AIRTEL':
                serializer = AirtelWebhookSerializer(data=request.data)
            else:
                return Response(
                    {'error': 'Invalid provider'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if serializer.is_valid():
                service = MobilePaymentService(provider)
                service.handle_webhook(serializer.validated_data)
                return Response({'success': True})
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
