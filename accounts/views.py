from django.shortcuts import render
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import Address, UserPreference
from .serializers import (
    UserSerializer, UserRegistrationSerializer, AddressSerializer,
    UserPreferenceSerializer, PasswordChangeSerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # Regular users can only see their own profile
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Wrong password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'status': 'password changed'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address_type = address.address_type
        
        # Remove default status from other addresses of the same type
        Address.objects.filter(
            user=request.user,
            address_type=address_type,
            is_default=True
        ).update(is_default=False)
        
        # Set this address as default
        address.is_default = True
        address.save()
        
        return Response({'status': f'Address set as default {address_type.lower()}'})

class UserPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default_addresses(self, request, pk=None):
        preference = self.get_object()
        shipping_address_id = request.data.get('default_shipping_address')
        billing_address_id = request.data.get('default_billing_address')
        
        if shipping_address_id:
            try:
                shipping_address = Address.objects.get(
                    id=shipping_address_id,
                    user=request.user
                )
                preference.default_shipping_address = shipping_address
            except Address.DoesNotExist:
                return Response(
                    {'error': 'Invalid shipping address ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if billing_address_id:
            try:
                billing_address = Address.objects.get(
                    id=billing_address_id,
                    user=request.user
                )
                preference.default_billing_address = billing_address
            except Address.DoesNotExist:
                return Response(
                    {'error': 'Invalid billing address ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        preference.save()
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
