from rest_framework import serializers
from typing import List, Dict, Any
from drf_spectacular.utils import extend_schema_field
from .models import Order, OrderItem, OrderStatusHistory, OrderNote, DeliveryZone, Product

class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = ['id', 'name', 'description', 'delivery_fee', 'estimated_days']

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price', 'subtotal']
        read_only_fields = ['price', 'subtotal']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'notes', 'created_by_name', 'created_at']
        read_only_fields = ['created_at', 'created_by_name']

class OrderNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = OrderNote
        fields = ['id', 'note', 'is_public', 'created_by_name', 'created_at']
        read_only_fields = ['created_at', 'created_by_name']

class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'total', 'created_at'
        ]
        read_only_fields = fields

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    notes = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    delivery_zone = DeliveryZoneSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'delivery_zone', 'shipping_address',
            'subtotal', 'delivery_fee', 'total',
            'created_at', 'updated_at',
            'tracking_number',
            'items', 'status_history', 'notes'
        ]
        read_only_fields = [
            'user', 'subtotal', 'total',
            'created_at', 'updated_at'
        ]

    @extend_schema_field(OrderNoteSerializer(many=True))
    def get_notes(self, obj: Order) -> List[Dict[str, Any]]:
        # Only return public notes and all notes for staff users
        request = self.context.get('request')
        if request and request.user.is_staff:
            notes = obj.notes.all()
        else:
            notes = obj.notes.filter(is_public=True)
        return OrderNoteSerializer(notes, many=True).data

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'delivery_zone', 'shipping_address', 'items'
        ]

    def create(self, validated_data: Dict[str, Any]) -> Order:
        items_data = validated_data.pop('items')
        order = Order.objects.create(
            user=self.context['request'].user,
            **validated_data
        )

        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Calculate totals
        order.subtotal = sum(item.subtotal for item in order.items.all())
        if order.delivery_zone:
            order.delivery_fee = order.delivery_zone.delivery_fee
        order.total = order.subtotal + order.delivery_fee
        order.save()

        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status=order.status,
            notes="Order created",
            created_by=self.context['request'].user
        )

        return order

# Action Serializers
class AddNoteSerializer(serializers.Serializer):
    """Serializer for adding a note to an order"""
    note = serializers.CharField()
    is_public = serializers.BooleanField(default=True)

class UpdateStatusSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    notes = serializers.CharField(required=False)

class TrackingNumberSerializer(serializers.Serializer):
    """Serializer for updating tracking number"""
    tracking_number = serializers.CharField()

class CancelOrderSerializer(serializers.Serializer):
    """Serializer for canceling an order"""
    reason = serializers.CharField(required=False) 