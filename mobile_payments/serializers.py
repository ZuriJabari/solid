from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import MobilePayment, MobilePaymentProvider, PaymentNotification

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
            'id', 'user', 'order', 'provider', 'provider_name',
            'amount', 'phone_number', 'status', 'transaction_id',
            'provider_reference', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.PrimaryKeyRelatedField(queryset=MobilePaymentProvider.objects.filter(is_active=True))
    phone_number = serializers.CharField(max_length=15)

class PaymentStatusSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()

class PaymentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentNotification
        fields = [
            'id', 'payment', 'provider', 'notification_type',
            'payload', 'processed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class WebhookSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    provider_reference = serializers.CharField()

class AirtelWebhookSerializer(WebhookSerializer):
    pass

class MTNWebhookSerializer(WebhookSerializer):
    pass 