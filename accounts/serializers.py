from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, UserPreference
from products.models import Category
from products.serializers import ProductSerializer

User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'is_default', 'full_name', 'street_address1',
            'street_address2', 'city', 'state', 'postal_code', 'country',
            'phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserPreferenceSerializer(serializers.ModelSerializer):
    default_shipping_address = AddressSerializer(read_only=True)
    default_billing_address = AddressSerializer(read_only=True)
    wishlist_items = ProductSerializer(many=True, read_only=True)
    saved_items = ProductSerializer(many=True, read_only=True)
    preferred_categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=False
    )

    class Meta:
        model = UserPreference
        fields = [
            'id', 'theme', 'email_notifications', 'push_notifications',
            'default_shipping_address', 'default_billing_address',
            'wishlist_items', 'saved_items', 'preferred_categories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    preferences = UserPreferenceSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'date_of_birth', 'email_verified', 'newsletter_subscribed',
            'marketing_preferences', 'is_active', 'created_at',
            'updated_at', 'addresses', 'preferences'
        ]
        read_only_fields = [
            'id', 'email_verified', 'created_at', 'updated_at',
            'addresses', 'preferences'
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone',
            'date_of_birth', 'newsletter_subscribed'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        fields = ['email', 'password']

class LogoutSerializer(serializers.Serializer):
    class Meta:
        fields = []

class ProductIdSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)

class DefaultAddressesSerializer(serializers.Serializer):
    default_shipping_address = serializers.IntegerField(required=False, allow_null=True)
    default_billing_address = serializers.IntegerField(required=False, allow_null=True)
  