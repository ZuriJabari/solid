from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import MobilePayment
from .serializers import (
    MobilePaymentSerializer, PaymentInitiateSerializer,
    PaymentStatusSerializer, WebhookSerializer,
    AirtelWebhookSerializer, MTNWebhookSerializer
)
from core.serializers import ErrorSerializer, SuccessSerializer
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
        if getattr(self, 'swagger_fake_view', False):
            return MobilePayment.objects.none()
        return MobilePayment.objects.filter(order__user=self.request.user)

    @extend_schema(
        description='Initiate a mobile payment',
        request=PaymentInitiateSerializer,
        responses={
            200: MobilePaymentSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                order = Order.objects.get(
                    id=serializer.validated_data['order_id'],
                    user=request.user
                )
                payment = MobilePayment.objects.create(
                    order=order,
                    user=request.user,
                    provider=serializer.validated_data['provider'],
                    phone_number=serializer.validated_data['phone_number'],
                    amount=order.total
                )
                return Response(MobilePaymentSerializer(payment).data)
            except Order.DoesNotExist:
                return Response(
                    {'error': 'Order not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Check payment status',
        request=PaymentStatusSerializer,
        responses={
            200: MobilePaymentSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=False, methods=['post'])
    def check_status(self, request):
        serializer = PaymentStatusSerializer(data=request.data)
        if serializer.is_valid():
            try:
                payment = MobilePayment.objects.get(
                    transaction_id=serializer.validated_data['transaction_id'],
                    order__user=request.user
                )
                return Response(MobilePaymentSerializer(payment).data)
            except MobilePayment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(APIView):
    """
    API endpoint for payment provider webhooks.
    """
    permission_classes = []

    @extend_schema(
        description='Airtel Money webhook endpoint',
        request=AirtelWebhookSerializer,
        responses={
            200: SuccessSerializer,
            400: ErrorSerializer,
        }
    )
    def post(self, request, provider):
        if provider == 'airtel':
            serializer = AirtelWebhookSerializer(data=request.data)
        elif provider == 'mtn':
            serializer = MTNWebhookSerializer(data=request.data)
        else:
            return Response(
                {'error': 'Invalid payment provider'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            try:
                payment = MobilePayment.objects.get(
                    transaction_id=serializer.validated_data['transaction_id']
                )
                payment.status = serializer.validated_data['status']
                payment.save()
                return Response({'success': True})
            except MobilePayment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
