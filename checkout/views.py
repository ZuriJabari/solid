from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import DeliveryZone, PickupLocation, PaymentMethod, CheckoutSession
from .serializers import (
    DeliveryZoneSerializer, PickupLocationSerializer,
    PaymentMethodSerializer, CheckoutSessionSerializer,
    CheckoutSessionCreateSerializer
)
from cart.models import Cart
from core.serializers import ErrorSerializer, SuccessSerializer

class DeliveryZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for delivery zones.
    """
    queryset = DeliveryZone.objects.filter(is_active=True).order_by('name')
    serializer_class = DeliveryZoneSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

class PickupLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for pickup locations.
    """
    queryset = PickupLocation.objects.filter(is_active=True).order_by('name')
    serializer_class = PickupLocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for payment methods.
    """
    queryset = PaymentMethod.objects.filter(is_active=True).order_by('name')
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

class CheckoutSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing checkout sessions.
    """
    serializer_class = CheckoutSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get checkout sessions for the current user"""
        return CheckoutSession.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return CheckoutSessionCreateSerializer
        return CheckoutSessionSerializer

    def perform_create(self, serializer):
        """Create a new checkout session"""
        # Get or create active cart
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        
        # Calculate totals
        subtotal = cart.total_price
        delivery_fee = (
            serializer.validated_data['delivery_zone'].delivery_fee
            if serializer.validated_data.get('delivery_zone')
            else 0
        )
        total = subtotal + delivery_fee

        # Set expiration time (30 minutes from now)
        expires_at = timezone.now() + timedelta(minutes=30)

        # Create checkout session
        serializer.save(
            user=self.request.user,
            cart=cart,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            expires_at=expires_at
        )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm checkout session and proceed to payment
        """
        session = self.get_object()

        # Validate session status
        if session.status != 'PENDING':
            return Response(
                {'error': 'Invalid session status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if session is expired
        if session.expires_at < timezone.now():
            session.status = 'EXPIRED'
            session.save()
            return Response(
                {'error': 'Checkout session has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update session status
        session.status = 'PAYMENT_PENDING'
        session.save()

        # Initialize payment based on method
        payment_method = session.payment_method
        if payment_method.provider == 'CARD':
            # Initialize card payment
            pass
        elif payment_method.provider in ['MTN_MOMO', 'AIRTEL_MONEY']:
            # Initialize mobile money payment
            pass
        elif payment_method.provider == 'CASH':
            # Handle cash on delivery
            pass

        return Response(
            {'message': 'Checkout session confirmed'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel checkout session
        """
        session = self.get_object()
        
        if session.status not in ['PENDING', 'PAYMENT_PENDING']:
            return Response(
                {'error': 'Session cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.status = 'CANCELLED'
        session.save()

        return Response(
            {'message': 'Checkout session cancelled'},
            status=status.HTTP_200_OK
        )
