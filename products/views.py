from rest_framework import generics, filters, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import Category, Product, ProductReview, ReviewVote, ProductInventory, InventoryBatch, StockAdjustment
from .filters import ProductFilter
from .serializers import (
    CategorySerializer, RecursiveCategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductReviewSerializer, ReviewVoteSerializer,
    ProductInventorySerializer, InventoryBatchSerializer, StockAdjustmentSerializer
)

class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 48

class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        )
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            if parent_id == 'root':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        return queryset

class CategoryTreeView(generics.ListAPIView):
    serializer_class = RecursiveCategorySerializer
    permission_classes = []

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        )

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = []

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        )

class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = []
    pagination_class = ProductPagination
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'name', 'average_rating']
    ordering = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True
        ).annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).select_related('category').prefetch_related('images')

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = []

    def get_queryset(self):
        return Product.objects.annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__status='approved')),
            review_count=Count('reviews', filter=Q(reviews__status='approved'))
        ).select_related('category').prefetch_related(
            'images',
            'reviews__user',
            'reviews__votes'
        )

class ProductReviewCreateView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs['slug'])
        
        # Check if user has purchased the product
        has_purchased = product.orders.filter(
            user=self.request.user,
            status='completed'
        ).exists()
        
        review = serializer.save(
            user=self.request.user,
            product=product,
            is_verified_purchase=has_purchased
        )

class ProductReviewUpdateView(generics.UpdateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return ProductReview.objects.filter(
            user=self.request.user,
            status='pending'
        )

class ProductReviewDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return ProductReview.objects.filter(
            user=self.request.user,
            status='pending'
        )

class ReviewVoteView(generics.CreateAPIView):
    serializer_class = ReviewVoteSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        review_id = kwargs.get('review_id')
        vote_type = request.data.get('vote')
        
        if vote_type not in ['helpful', 'unhelpful']:
            return Response(
                {'error': 'Invalid vote type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            review = ProductReview.objects.get(id=review_id, status='approved')
        except ProductReview.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if review.user == request.user:
            return Response(
                {'error': 'Cannot vote on your own review'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update or create vote
        vote, created = ReviewVote.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={'vote': vote_type}
        )

        return Response(
            ReviewVoteSerializer(vote).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

class ReviewModerationView(generics.UpdateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff members can moderate reviews")
        return ProductReview.objects.filter(status='pending')

    def perform_update(self, serializer):
        status = self.request.data.get('status')
        if status not in ['approved', 'rejected']:
            raise serializers.ValidationError("Invalid status")
        
        serializer.save(
            status=status,
            moderated_by=self.request.user,
            moderated_at=timezone.now()
        )

class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductInventorySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['product__name']
    filterset_fields = ['product']

    def get_queryset(self):
        return ProductInventory.objects.all().select_related(
            'product'
        ).prefetch_related('batches', 'adjustments')

    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        inventory = self.get_object()
        batch_data = request.data.get('batch', {})
        quantity = batch_data.get('quantity', 0)

        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new batch
        batch_serializer = InventoryBatchSerializer(data=batch_data)
        if batch_serializer.is_valid():
            batch = batch_serializer.save(inventory=inventory)

            # Create stock adjustment
            adjustment = StockAdjustment.objects.create(
                inventory=inventory,
                batch=batch,
                adjustment_type='restock',
                quantity=quantity,
                reason=f"Restock - Batch {batch.batch_number}",
                adjusted_by=request.user
            )

            # Update inventory
            inventory.last_restock_date = timezone.now()
            inventory.last_restock_quantity = quantity
            inventory.save()

            return Response(
                StockAdjustmentSerializer(adjustment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            batch_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        inventory = self.get_object()
        adjustment_data = request.data

        # Validate adjustment
        serializer = StockAdjustmentSerializer(data=adjustment_data)
        if serializer.is_valid():
            adjustment = serializer.save(
                inventory=inventory,
                adjusted_by=request.user
            )
            return Response(
                StockAdjustmentSerializer(adjustment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True)
    def expiring_batches(self, request, pk=None):
        inventory = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        expiry_date = timezone.now().date() + timezone.timedelta(days=days)
        batches = inventory.batches.filter(
            expiry_date__lte=expiry_date,
            quantity__gt=0
        )
        
        return Response(
            InventoryBatchSerializer(batches, many=True).data
        )

    @action(detail=True)
    def low_stock_products(self, request):
        queryset = self.get_queryset().filter(
            current_stock__lte=F('reorder_point')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class InventoryBatchViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryBatchSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['inventory', 'supplier']
    search_fields = ['batch_number', 'supplier', 'notes']

    def get_queryset(self):
        return InventoryBatch.objects.all().select_related(
            'inventory__product'
        )

class StockAdjustmentViewSet(viewsets.ModelViewSet):
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['inventory', 'adjustment_type']
    search_fields = ['reason', 'reference_number']

    def get_queryset(self):
        return StockAdjustment.objects.all().select_related(
            'inventory__product', 'batch', 'adjusted_by'
        )

    def perform_create(self, serializer):
        serializer.save(adjusted_by=self.request.user)
