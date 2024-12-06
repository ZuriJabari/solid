from django.contrib.auth import get_user_model, login, logout
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Address, UserPreference
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    AddressSerializer, UserPreferenceSerializer,
    PasswordChangeSerializer, LoginSerializer,
    LogoutSerializer, ProductIdSerializer,
    DefaultAddressesSerializer
)
from core.serializers import ErrorSerializer, MessageSerializer, SuccessSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password changed successfully'})
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing addresses.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing user preferences.
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserPreference.objects.none()
        return UserPreference.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_to_wishlist(self, request, pk=None):
        """Add a product to the user's wishlist"""
        preference = self.get_object()
        serializer = ProductIdSerializer(data=request.data)
        if serializer.is_valid():
            preference.wishlist_items.add(serializer.validated_data['product_id'])
            return Response(self.get_serializer(preference).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_from_wishlist(self, request, pk=None):
        """Remove a product from the user's wishlist"""
        preference = self.get_object()
        serializer = ProductIdSerializer(data=request.data)
        if serializer.is_valid():
            preference.wishlist_items.remove(serializer.validated_data['product_id'])
            return Response(self.get_serializer(preference).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_to_saved(self, request, pk=None):
        """Add a product to the user's saved items"""
        preference = self.get_object()
        serializer = ProductIdSerializer(data=request.data)
        if serializer.is_valid():
            preference.saved_items.add(serializer.validated_data['product_id'])
            return Response(self.get_serializer(preference).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_from_saved(self, request, pk=None):
        """Remove a product from the user's saved items"""
        preference = self.get_object()
        serializer = ProductIdSerializer(data=request.data)
        if serializer.is_valid():
            preference.saved_items.remove(serializer.validated_data['product_id'])
            return Response(self.get_serializer(preference).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_default_addresses(self, request, pk=None):
        """Update default shipping and billing addresses"""
        preference = self.get_object()
        serializer = DefaultAddressesSerializer(data=request.data)
        if serializer.is_valid():
            if 'default_shipping_address' in serializer.validated_data:
                address = get_object_or_404(
                    Address,
                    id=serializer.validated_data['default_shipping_address'],
                    user=request.user
                )
                preference.default_shipping_address = address
            if 'default_billing_address' in serializer.validated_data:
                address = get_object_or_404(
                    Address,
                    id=serializer.validated_data['default_billing_address'],
                    user=request.user
                )
                preference.default_billing_address = address
            preference.save()
            return Response(self.get_serializer(preference).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'message': 'Registration successful'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                request,
                username=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user and user.is_active:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return Response({'message': 'Login successful'})
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    API endpoint for user logout.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})
