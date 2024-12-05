from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_or_create_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], serializer_class=CartItemSerializer)
    def add_item(self, request):
        cart = self.get_or_create_cart()
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Check if item already exists
                item = CartItem.objects.get(
                    cart=cart,
                    product_id=serializer.validated_data['product_id']
                )
                item.quantity += serializer.validated_data['quantity']
                item.save()
            except CartItem.DoesNotExist:
                serializer.save()
            
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = self.get_or_create_cart()
        item = get_object_or_404(CartItem, cart=cart, id=request.data.get('item_id'))
        
        quantity = request.data.get('quantity', 1)
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
            
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_or_create_cart()
        item = get_object_or_404(CartItem, cart=cart, id=request.data.get('item_id'))
        item.delete()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
