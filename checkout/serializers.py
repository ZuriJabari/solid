from rest_framework import serializers
from .models import DeliveryZone, PickupLocation, PaymentMethod, CheckoutSession
from cart.serializers import CartSerializer

class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'description', 'delivery_fee',
            'estimated_days', 'is_active'
        ]

class PickupLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupLocation
        fields = [
            'id', 'name', 'address', 'contact_phone',
            'operating_hours', 'is_active'
        ]

class PaymentMethodSerializer(serializers.ModelSerializer):
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'provider', 'provider_display',
            'description', 'icon', 'is_active',
            'requires_verification', 'min_amount', 'max_amount'
        ]

class CheckoutSessionSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)
    delivery_zone = DeliveryZoneSerializer(read_only=True)
    pickup_location = PickupLocationSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CheckoutSession
        fields = [
            'id', 'user', 'cart', 'delivery_type',
            'delivery_zone', 'pickup_location',
            'delivery_address', 'delivery_instructions',
            'payment_method', 'subtotal', 'delivery_fee',
            'total', 'status', 'status_display',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['user', 'subtotal', 'total', 'expires_at', 'created_at']

class CheckoutSessionCreateSerializer(serializers.ModelSerializer):
    delivery_zone_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryZone.objects.filter(is_active=True),
        required=False,
        write_only=True,
        source='delivery_zone'
    )
    pickup_location_id = serializers.PrimaryKeyRelatedField(
        queryset=PickupLocation.objects.filter(is_active=True),
        required=False,
        write_only=True,
        source='pickup_location'
    )
    payment_method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        required=True,
        write_only=True,
        source='payment_method'
    )

    class Meta:
        model = CheckoutSession
        fields = [
            'delivery_type', 'delivery_zone_id',
            'pickup_location_id', 'delivery_address',
            'delivery_instructions', 'payment_method_id',
            'status'
        ]
        read_only_fields = ['status']

    def validate(self, data):
        delivery_type = data.get('delivery_type')
        delivery_zone = data.get('delivery_zone')
        pickup_location = data.get('pickup_location')
        delivery_address = data.get('delivery_address')

        if delivery_type == 'DELIVERY':
            if not delivery_zone:
                raise serializers.ValidationError(
                    {'delivery_zone_id': 'Delivery zone is required for delivery orders.'}
                )
            if not delivery_address:
                raise serializers.ValidationError(
                    {'delivery_address': 'Delivery address is required for delivery orders.'}
                )
        elif delivery_type == 'PICKUP':
            if not pickup_location:
                raise serializers.ValidationError(
                    {'pickup_location_id': 'Pickup location is required for pickup orders.'}
                )

        return data 