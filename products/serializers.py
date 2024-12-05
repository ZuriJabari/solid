from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview, Inventory, StockMovement

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

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    inventory_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_id', 'name', 'slug',
            'description', 'price', 'image', 'is_active',
            'images', 'reviews', 'average_rating',
            'inventory_status', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']

    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return None

    def get_inventory_status(self, obj):
        try:
            inventory = obj.inventory
            if inventory.quantity <= 0:
                return 'Out of Stock'
            elif inventory.quantity <= inventory.low_stock_threshold:
                return 'Low Stock'
            return 'In Stock'
        except Inventory.DoesNotExist:
            return 'No Inventory'