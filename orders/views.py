from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, OrderStatusHistory, OrderNote, DeliveryZone
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderStatusHistorySerializer, OrderNoteSerializer, DeliveryZoneSerializer
)

class DeliveryZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeliveryZone.objects.filter(is_active=True)
    serializer_class = DeliveryZoneSerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().select_related(
                'user', 'delivery_zone'
            ).prefetch_related(
                'items', 'items__product',
                'status_history', 'notes'
            )
        return Order.objects.filter(user=user).select_related(
            'delivery_zone'
        ).prefetch_related(
            'items', 'items__product',
            'status_history', 'notes'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return OrderDetailSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        order = serializer.save()
        # Send order confirmation email
        self._send_order_confirmation(order)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            created_by=request.user
        )

        # Update order status
        order.status = new_status
        order.save()

        # Send notification
        self._send_status_update_notification(order)

        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        order = self.get_object()
        serializer = OrderNoteSerializer(data=request.data)
        
        if serializer.is_valid():
            note = serializer.save(
                order=order,
                created_by=request.user
            )
            return Response(
                OrderNoteSerializer(note).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True)
    def status_history(self, request, pk=None):
        order = self.get_object()
        history = order.status_history.all()
        serializer = OrderStatusHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def my_orders(self, request):
        orders = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, permission_classes=[IsAdminUser])
    def pending_orders(self, request):
        orders = self.get_queryset().filter(
            Q(status='pending') | Q(status='paid')
        )
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, permission_classes=[IsAdminUser])
    def today_orders(self, request):
        today = timezone.now().date()
        orders = self.get_queryset().filter(
            created_at__date=today
        )
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    def _send_order_confirmation(self, order):
        subject = f'Order Confirmation - {order.order_number}'
        message = f"""
        Thank you for your order!

        Order Number: {order.order_number}
        Total Amount: ${order.total}
        
        {'Delivery' if order.delivery_method == 'delivery' else 'Pickup'} Details:
        {order.delivery_address if order.delivery_method == 'delivery' else order.pickup_location}
        
        We will notify you when your order status changes.
        """
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send order confirmation email: {e}")

    def _send_status_update_notification(self, order):
        subject = f'Order Status Update - {order.order_number}'
        message = f"""
        Your order status has been updated.

        Order Number: {order.order_number}
        New Status: {order.get_status_display()}
        
        {'Tracking Number: ' + order.tracking_number if order.tracking_number else ''}
        """
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send status update email: {e}")

class OrderNoteViewSet(viewsets.ModelViewSet):
    serializer_class = OrderNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return OrderNote.objects.all()
        return OrderNote.objects.filter(
            Q(order__user=user) & Q(is_public=True)
        )
