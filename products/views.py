from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Avg, Q
from .models import Category, Product, ProductReview, ProductBundle
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductReviewSerializer, ProductBundleSerializer,
    ProductReviewCreateSerializer, ProductInventoryUpdateSerializer,
    ProductBundleProductSerializer, ProductSearchSerializer
)
from core.serializers import ErrorSerializer, SuccessSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing product categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.annotate(
            average_rating=Avg('reviews__rating')
        ).order_by('-created_at', 'id')
        return queryset

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Add a review to a product"""
        product = self.get_object()
        serializer = ProductReviewCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            review = ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=serializer.validated_data['rating'],
                comment=serializer.validated_data.get('comment', '')
            )
            return Response(
                ProductReviewSerializer(review).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get product inventory"""
        product = self.get_object()
        return Response({
            'quantity': product.inventory_count,
            'low_stock_threshold': product.low_stock_threshold
        })

    @action(detail=True, methods=['post'])
    def update_inventory(self, request, pk=None):
        """Update product inventory"""
        product = self.get_object()
        serializer = ProductInventoryUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            product.inventory_count = serializer.validated_data['quantity']
            if 'low_stock_threshold' in serializer.validated_data:
                product.low_stock_threshold = serializer.validated_data['low_stock_threshold']
            product.save()
            return Response({
                'quantity': product.inventory_count,
                'low_stock_threshold': product.low_stock_threshold
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search products with filters"""
        serializer = ProductSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        data = serializer.validated_data

        if 'query' in data:
            queryset = queryset.filter(
                Q(name__icontains=data['query']) |
                Q(description__icontains=data['query'])
            )

        if 'category' in data:
            queryset = queryset.filter(category_id=data['category'])

        if 'min_price' in data:
            queryset = queryset.filter(price__gte=data['min_price'])

        if 'max_price' in data:
            queryset = queryset.filter(price__lte=data['max_price'])

        if 'sort_by' in data:
            queryset = queryset.order_by(data['sort_by'])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProductBundleViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing product bundles.
    """
    queryset = ProductBundle.objects.all()
    serializer_class = ProductBundleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Add a product to the bundle"""
        bundle = self.get_object()
        serializer = ProductBundleProductSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                product = Product.objects.get(
                    id=serializer.validated_data['product_id']
                )
                bundle.products.add(product)
                return Response(self.get_serializer(bundle).data)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        """Remove a product from the bundle"""
        bundle = self.get_object()
        serializer = ProductBundleProductSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                product = Product.objects.get(
                    id=serializer.validated_data['product_id']
                )
                bundle.products.remove(product)
                return Response(self.get_serializer(bundle).data)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
