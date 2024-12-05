from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'description', 'parent')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'order')

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ('id', 'rating', 'comment', 'created_at', 'user_name')

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name')
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'short_description', 'price',
            'sale_price', 'primary_image', 'category_name',
            'potency', 'average_rating', 'is_featured'
        )

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            if self.context.get('request'):
                return self.context['request'].build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None