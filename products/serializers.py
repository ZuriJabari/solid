from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview, ReviewVote, InventoryBatch, StockAdjustment, ProductInventory

class RecursiveCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'description', 'children', 'product_count', 'level')
    
    def get_children(self, obj):
        if not obj.get_children():
            return []
        return RecursiveCategorySerializer(obj.get_children(), many=True).data

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    path = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'description', 'parent', 'parent_name', 'product_count', 'level', 'path')
    
    def get_path(self, obj):
        return [{'id': ancestor.id, 'name': ancestor.name, 'slug': ancestor.slug} 
                for ancestor in obj.get_ancestors(include_self=True)]

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'order')

class ReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ('id', 'vote', 'created_at')
        read_only_fields = ('created_at',)

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    helpful_percentage = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = (
            'id', 'rating', 'title', 'comment', 'created_at',
            'user_name', 'user_avatar', 'helpful_votes',
            'unhelpful_votes', 'helpful_percentage', 'user_vote',
            'is_verified_purchase', 'status', 'can_edit'
        )
        read_only_fields = (
            'helpful_votes', 'unhelpful_votes', 'status',
            'is_verified_purchase', 'created_at'
        )

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
        return None

    def get_helpful_percentage(self, obj):
        total_votes = obj.helpful_votes + obj.unhelpful_votes
        if total_votes > 0:
            return round((obj.helpful_votes / total_votes) * 100)
        return None

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            return vote.vote if vote else None
        return None

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def validate(self, data):
        if self.instance:  # Update
            if self.instance.status != 'pending':
                raise serializers.ValidationError(
                    "Cannot edit a review that has been moderated"
                )
        return data

class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name')
    category_slug = serializers.CharField(source='category.slug')
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'short_description', 'price',
            'sale_price', 'primary_image', 'category_name', 'category_slug',
            'potency', 'average_rating', 'review_count', 'is_featured',
            'stock', 'in_stock'
        )

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            if self.context.get('request'):
                return self.context['request'].build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None

    def get_in_stock(self, obj):
        return obj.stock > 0

class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = [
            'id', 'batch_number', 'quantity',
            'manufacturing_date', 'expiry_date',
            'supplier', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']

class StockAdjustmentSerializer(serializers.ModelSerializer):
    adjusted_by_name = serializers.CharField(source='adjusted_by.get_full_name', read_only=True)

    class Meta:
        model = StockAdjustment
        fields = [
            'id', 'adjustment_type', 'quantity',
            'reason', 'reference_number', 'batch',
            'adjusted_by_name', 'created_at'
        ]
        read_only_fields = ['adjusted_by_name', 'created_at']

class ProductInventorySerializer(serializers.ModelSerializer):
    batches = InventoryBatchSerializer(many=True, read_only=True)
    recent_adjustments = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    expiring_batches = serializers.SerializerMethodField()

    class Meta:
        model = ProductInventory
        fields = [
            'id', 'current_stock', 'reorder_point',
            'reorder_quantity', 'last_restock_date',
            'last_restock_quantity', 'batches',
            'recent_adjustments', 'stock_status',
            'expiring_batches'
        ]
        read_only_fields = [
            'current_stock', 'last_restock_date',
            'last_restock_quantity'
        ]

    def get_recent_adjustments(self, obj):
        adjustments = obj.adjustments.all()[:5]
        return StockAdjustmentSerializer(adjustments, many=True).data

    def get_stock_status(self, obj):
        if obj.current_stock <= 0:
            return 'out_of_stock'
        elif obj.current_stock <= obj.reorder_point:
            return 'low_stock'
        return 'in_stock'

    def get_expiring_batches(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_later = timezone.now().date() + timedelta(days=30)
        batches = obj.batches.filter(
            expiry_date__lte=thirty_days_later,
            quantity__gt=0
        )
        return InventoryBatchSerializer(batches, many=True).data

class ProductDetailSerializer(ProductListSerializer):
    inventory = ProductInventorySerializer(read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    rating_distribution = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            'description', 'ingredients', 'usage_instructions',
            'warnings', 'reviews', 'rating_distribution',
            'inventory'
        )

    def get_rating_distribution(self, obj):
        distribution = {i: 0 for i in range(1, 6)}
        reviews = obj.reviews.filter(status='approved')
        total_reviews = reviews.count()
        
        if total_reviews > 0:
            for rating in range(1, 6):
                count = reviews.filter(rating=rating).count()
                distribution[rating] = {
                    'count': count,
                    'percentage': round((count / total_reviews) * 100)
                }
        
        return distribution