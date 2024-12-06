from rest_framework import serializers
from .models import SalesMetric, InventoryMetric, CustomerMetric, ProductPerformance
from products.serializers import ProductSerializer

class SalesMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesMetric
        fields = [
            'id', 'date', 'total_sales', 'order_count',
            'average_order_value', 'refund_amount', 'refund_count',
            'formatted_total_sales', 'formatted_average_order_value'
        ]
        read_only_fields = fields

class InventoryMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMetric
        fields = [
            'id', 'date', 'metrics_data'
        ]
        read_only_fields = fields

class CustomerMetricSerializer(serializers.ModelSerializer):
    customer_retention_rate = serializers.SerializerMethodField()

    class Meta:
        model = CustomerMetric
        fields = [
            'id', 'date', 'total_customers', 'new_customers',
            'returning_customers', 'average_session_duration',
            'cart_abandonment_rate', 'customer_retention_rate'
        ]
        read_only_fields = fields

    def get_customer_retention_rate(self, obj):
        if obj.total_customers == 0:
            return 0
        return round((obj.returning_customers / obj.total_customers) * 100, 2)

class ProductPerformanceSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductPerformance
        fields = [
            'id', 'date', 'product', 'views',
            'add_to_cart_count', 'purchase_count',
            'revenue', 'conversion_rate',
            'formatted_revenue'
        ]
        read_only_fields = fields

class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data

class AnalyticsSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_customers = serializers.IntegerField()
    best_selling_products = ProductPerformanceSerializer(many=True)
    customer_retention_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    inventory_turnover_rate = serializers.DecimalField(max_digits=5, decimal_places=2) 