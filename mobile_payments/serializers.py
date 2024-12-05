from rest_framework import serializers
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification

class MobilePaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePaymentProvider
        fields = ['id', 'name', 'code', 'is_active']
        read_only_fields = ['id']

class MobilePaymentSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    
    class Meta:
        model = MobilePayment
        fields = [
            'id', 'provider', 'provider_name', 'amount',
            'currency', 'phone_number', 'status',
            'provider_tx_id', 'provider_tx_ref',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'provider_tx_id', 'provider_tx_ref',
            'status', 'created_at', 'completed_at'
        ]

class PaymentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentNotification
        fields = [
            'id', 'payment', 'provider',
            'notification_type', 'status',
            'is_processed', 'received_at'
        ]
        read_only_fields = [
            'id', 'is_processed', 'received_at'
        ]

class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider_code = serializers.CharField()
    phone_number = serializers.CharField()
    
    def validate_provider_code(self, value):
        try:
            provider = MobilePaymentProvider.objects.get(
                code=value,
                is_active=True
            )
            return value
        except MobilePaymentProvider.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or inactive payment provider"
            )

class CheckPaymentStatusSerializer(serializers.Serializer):
    provider_tx_ref = serializers.CharField()
    
    def validate_provider_tx_ref(self, value):
        try:
            payment = MobilePayment.objects.get(provider_tx_ref=value)
            return value
        except MobilePayment.DoesNotExist:
            raise serializers.ValidationError(
                "Payment not found"
            ) 