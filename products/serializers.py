from rest_framework import serializers
from django.db import models
from decimal import Decimal
from typing import Optional, Union
from drf_spectacular.utils import extend_schema_field
from .models import (
    Category, Product, ProductImage, ProductReview, 
    Inventory, StockMovement, ProductOption, ProductOptionValue,
    ProductVariant, BulkPricing, ProductBundle, BundleItem
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'description', 'image', 'is_active']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_feature']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']

class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'movement_type', 'quantity', 'reference', 'notes', 'created_at']
        read_only_fields = ['created_at']

class InventorySerializer(serializers.ModelSerializer):
    movements = StockMovementSerializer(many=True, read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'product', 'quantity', 'low_stock_threshold', 'movements']
        read_only_fields = ['quantity']

class ProductOptionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOptionValue
        fields = ['id', 'option', 'value', 'display_value', 'sort_order']

class ProductOptionSerializer(serializers.ModelSerializer):
    values = ProductOptionValueSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'display_name', 'sort_order', 'values']

class ProductVariantSerializer(serializers.ModelSerializer):
    option_values = ProductOptionValueSerializer(many=True, read_only=True)
    final_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True,
        min_value=Decimal('0.00'),
        max_value=Decimal('999999.99')
    )
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'option_values', 'price_adjustment',
            'final_price', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']

class BulkPricingSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('999999.99')
    )

    class Meta:
        model = BulkPricing
        fields = ['id', 'min_quantity', 'price', 'is_active']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    bulk_prices = BulkPricingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    inventory_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_id', 'name', 'slug',
            'description', 'price', 'image', 'is_active',
            'images', 'reviews', 'variants', 'bulk_prices',
            'average_rating', 'inventory_status', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']

    @extend_schema_field(Optional[float])
    def get_average_rating(self, obj: Product) -> Optional[float]:
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return None

    @extend_schema_field(str)
    def get_inventory_status(self, obj: Product) -> str:
        try:
            inventory = obj.inventory
            if inventory.quantity <= 0:
                return 'Out of Stock'
            elif inventory.quantity <= inventory.low_stock_threshold:
                return 'Low Stock'
            return 'In Stock'
        except Inventory.DoesNotExist:
            return 'No Inventory'

class BundleItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )
    
    class Meta:
        model = BundleItem
        fields = ['id', 'product', 'product_id', 'quantity']

class ProductBundleSerializer(serializers.ModelSerializer):
    bundle_items = BundleItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        min_value=Decimal('0.00')
    )
    discounted_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        min_value=Decimal('0.00')
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00')
    )
    
    class Meta:
        model = ProductBundle
        fields = [
            'id', 'name', 'slug', 'description', 'bundle_items',
            'discount_percentage', 'total_price', 'discounted_price',
            'is_active', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']

# Action Serializers
class ProductReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating product reviews"""
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False)

class ProductInventoryUpdateSerializer(serializers.Serializer):
    """Serializer for updating product inventory"""
    quantity = serializers.IntegerField(min_value=0)
    low_stock_threshold = serializers.IntegerField(min_value=0, required=False)

class ProductBundleProductSerializer(serializers.Serializer):
    """Serializer for adding/removing products from bundles"""
    product_id = serializers.IntegerField()

class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search parameters"""
    query = serializers.CharField(required=False)
    category = serializers.IntegerField(required=False)
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    max_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    sort_by = serializers.ChoiceField(
        choices=['price', '-price', 'name', '-name'],
        required=False
    )