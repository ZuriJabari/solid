from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, OrderNote, DeliveryZone

class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = ['id', 'name', 'description', 'delivery_fee', 'estimated_days']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['subtotal']

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.images.filter(is_primary=True).exists():
            image = obj.product.images.filter(is_primary=True).first()
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None

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
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'delivery_method', 'delivery_method_display',
            'total', 'created_at'
        ]
        read_only_fields = fields

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    notes = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    delivery_zone = DeliveryZoneSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user',
            'status', 'status_display',
            'payment_status', 'payment_status_display',
            'delivery_method', 'delivery_method_display',
            'delivery_zone', 'delivery_address', 'delivery_instructions',
            'preferred_delivery_date', 'preferred_delivery_time',
            'pickup_location', 'pickup_date', 'pickup_time',
            'subtotal', 'delivery_fee', 'tax', 'total',
            'created_at', 'updated_at', 'paid_at',
            'processed_at', 'completed_at', 'cancelled_at',
            'tracking_number', 'estimated_delivery', 'actual_delivery',
            'items', 'status_history', 'notes'
        ]
        read_only_fields = [
            'order_number', 'user', 'subtotal', 'total',
            'created_at', 'updated_at', 'paid_at',
            'processed_at', 'completed_at', 'cancelled_at',
            'actual_delivery'
        ]

    def get_notes(self, obj):
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
            'delivery_method', 'delivery_zone', 'delivery_address',
            'delivery_instructions', 'preferred_delivery_date',
            'preferred_delivery_time', 'pickup_location',
            'pickup_date', 'pickup_time', 'items'
        ]

    def validate(self, data):
        # Validate delivery method specific fields
        if data['delivery_method'] == 'delivery':
            if not data.get('delivery_address'):
                raise serializers.ValidationError(
                    {"delivery_address": "Delivery address is required for delivery orders."}
                )
            if not data.get('delivery_zone'):
                raise serializers.ValidationError(
                    {"delivery_zone": "Delivery zone is required for delivery orders."}
                )
        else:  # pickup
            if not data.get('pickup_location'):
                raise serializers.ValidationError(
                    {"pickup_location": "Pickup location is required for pickup orders."}
                )
            if not data.get('pickup_date'):
                raise serializers.ValidationError(
                    {"pickup_date": "Pickup date is required for pickup orders."}
                )

        # Validate items
        if not data.get('items'):
            raise serializers.ValidationError(
                {"items": "At least one item is required."}
            )

        return data

    def create(self, validated_data):
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
        if order.delivery_method == 'delivery' and order.delivery_zone:
            order.delivery_fee = order.delivery_zone.delivery_fee
        order.tax = order.subtotal * 0.15  # 15% tax
        order.total = order.subtotal + order.delivery_fee + order.tax
        order.save()

        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status=order.status,
            notes="Order created",
            created_by=self.context['request'].user
        )

        return order 