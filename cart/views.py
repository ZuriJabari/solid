from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import F, Sum
from .models import Cart, CartItem
from .serializers import (
    CartSerializer, CartItemSerializer,
    CartItemUpdateSerializer, CartItemRemoveSerializer
)
from core.serializers import ErrorSerializer, SuccessSerializer
from products.models import Product

class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing shopping carts.
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create cart for current user"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add an item to the cart"""
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']

            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity = F('quantity') + quantity
                cart_item.save()
                cart_item.refresh_from_db()

            cart.update_totals()
            return Response(self.get_serializer(cart).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_item(self, request, pk=None):
        """Update item quantity in cart"""
        cart = self.get_object()
        serializer = CartItemUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                item = cart.items.get(id=serializer.validated_data['item_id'])
                if serializer.validated_data['quantity'] == 0:
                    item.delete()
                else:
                    item.quantity = serializer.validated_data['quantity']
                    item.save()
                cart.update_totals()
                return Response(self.get_serializer(cart).data)
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Item not found in cart'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from cart"""
        cart = self.get_object()
        serializer = CartItemRemoveSerializer(data=request.data)
        if serializer.is_valid():
            try:
                item = cart.items.get(id=serializer.validated_data['item_id'])
                item.delete()
                cart.update_totals()
                return Response(self.get_serializer(cart).data)
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Item not found in cart'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Remove all items from cart"""
        cart = self.get_object()
        cart.items.all().delete()
        cart.update_totals()
        return Response(self.get_serializer(cart).data)
