from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg
from .models import Category, Product, ProductReview, Inventory
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductReviewSerializer,
    InventorySerializer
)
from .filters import ProductFilter

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def review(self, request, pk=None):
        product = self.get_object()
        user = request.user
        
        # Check if user has already reviewed this product
        if ProductReview.objects.filter(product=product, user=user).exists():
            return Response(
                {'detail': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        product = self.get_object()
        try:
            inventory = product.inventory
            serializer = InventorySerializer(inventory)
            return Response(serializer.data)
        except Inventory.DoesNotExist:
            return Response(
                {'detail': 'Inventory not found for this product.'},
                status=status.HTTP_404_NOT_FOUND
            )
