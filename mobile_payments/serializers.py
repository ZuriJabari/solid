from rest_framework import serializers
from .models import MobilePayment
import uuid

class MobilePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePayment
        fields = [
            'id', 'order', 'provider', 'phone_number',
            'amount', 'status', 'transaction_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'transaction_id',
            'created_at', 'updated_at'
        ]

class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating a mobile payment"""
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=MobilePayment.PROVIDER_CHOICES)
    phone_number = serializers.CharField()

class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for checking payment status"""
    transaction_id = serializers.CharField()

class WebhookSerializer(serializers.Serializer):
    """Base serializer for payment webhooks"""
    transaction_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    provider_reference = serializers.CharField(required=False)

class AirtelWebhookSerializer(WebhookSerializer):
    """Serializer for Airtel Money webhooks"""
    msisdn = serializers.CharField()
    payment_status = serializers.CharField()
    transaction_time = serializers.DateTimeField(required=False)

class MTNWebhookSerializer(WebhookSerializer):
    """Serializer for MTN Mobile Money webhooks"""
    phone_number = serializers.CharField()
    payment_result = serializers.CharField()
    transaction_timestamp = serializers.DateTimeField(required=False) 