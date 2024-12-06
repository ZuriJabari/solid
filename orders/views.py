from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Order, OrderNote
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderNoteSerializer, AddNoteSerializer, UpdateStatusSerializer,
    TrackingNumberSerializer, CancelOrderSerializer
)
from core.serializers import ErrorSerializer, SuccessSerializer

@extend_schema_view(
    list=extend_schema(
        description='List all orders for the current user',
        responses={200: OrderListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        description='Get a specific order by ID',
        responses={200: OrderDetailSerializer}
    ),
    create=extend_schema(
        description='Create a new order',
        request=OrderCreateSerializer,
        responses={201: OrderDetailSerializer}
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing orders.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    @extend_schema(
        description='Add a note to an order',
        request=AddNoteSerializer,
        responses={
            200: OrderDetailSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        order = self.get_object()
        serializer = AddNoteSerializer(data=request.data)
        if serializer.is_valid():
            OrderNote.objects.create(
                order=order,
                note=serializer.validated_data['note'],
                is_public=serializer.validated_data['is_public'],
                created_by=request.user
            )
            return Response(self.get_serializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Update order status',
        request=UpdateStatusSerializer,
        responses={
            200: OrderDetailSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = UpdateStatusSerializer(data=request.data)
        if serializer.is_valid():
            order.status = serializer.validated_data['status']
            order.save()
            if 'notes' in serializer.validated_data:
                OrderNote.objects.create(
                    order=order,
                    note=serializer.validated_data['notes'],
                    created_by=request.user
                )
            return Response(self.get_serializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Update tracking number',
        request=TrackingNumberSerializer,
        responses={
            200: OrderDetailSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        order = self.get_object()
        serializer = TrackingNumberSerializer(data=request.data)
        if serializer.is_valid():
            order.tracking_number = serializer.validated_data['tracking_number']
            order.save()
            return Response(self.get_serializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description='Cancel an order',
        request=CancelOrderSerializer,
        responses={
            200: OrderDetailSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        serializer = CancelOrderSerializer(data=request.data)
        if serializer.is_valid():
            if order.status not in ['pending', 'processing']:
                return Response(
                    {'error': 'Order cannot be canceled in its current state'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.status = 'canceled'
            order.save()
            if 'reason' in serializer.validated_data:
                OrderNote.objects.create(
                    order=order,
                    note=f"Order canceled: {serializer.validated_data['reason']}",
                    created_by=request.user
                )
            return Response(self.get_serializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
