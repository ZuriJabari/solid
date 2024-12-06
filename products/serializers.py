from rest_framework import serializers
from .models import (
    Product, ProductImage, Category,
    ProductRecommendation
)
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary']

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'category', 'stock', 'is_active', 'images',
            'created_at'
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'category', 'stock', 'is_active', 'images',
            'created_at', 'updated_at'
        ]

@extend_schema_serializer(
    component_name='ProductRecommendation',
    exclude_fields=[],
)
class ProductRecommendationSerializer(serializers.ModelSerializer):
    recommended_product = ProductListSerializer(read_only=True)
    source_product_id = serializers.PrimaryKeyRelatedField(
        source='source_product',
        queryset=Product.objects.all(),
        write_only=True
    )
    recommended_product_id = serializers.PrimaryKeyRelatedField(
        source='recommended_product',
        queryset=Product.objects.all(),
        write_only=True
    )
    recommendation_type = serializers.ChoiceField(
        choices=ProductRecommendation.RECOMMENDATION_TYPES,
        help_text='Type of recommendation (similar, frequently_bought, personalized)'
    )
    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text='Recommendation score (0-100)'
    )
    
    class Meta:
        model = ProductRecommendation
        fields = [
            'id',
            'source_product_id',
            'recommended_product_id',
            'recommended_product',
            'recommendation_type',
            'score'
        ]
        read_only_fields = ['id', 'score']
