from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import (
    Product, Category, ProductRecommendation
)
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    CategorySerializer, ProductRecommendationSerializer
)
from .filters import ProductFilter

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

@extend_schema_view(
    list=extend_schema(
        description='List product recommendations',
        responses={200: ProductRecommendationSerializer(many=True)},
        parameters=[
            {
                'name': 'source_product_id',
                'in': 'query',
                'description': 'Filter recommendations by source product ID',
                'required': False,
                'type': 'integer'
            },
            {
                'name': 'recommendation_type',
                'in': 'query',
                'description': 'Filter by recommendation type (similar, frequently_bought, personalized)',
                'required': False,
                'type': 'string'
            }
        ]
    ),
    create=extend_schema(
        description='Create a product recommendation',
        request=ProductRecommendationSerializer,
        responses={201: ProductRecommendationSerializer}
    ),
    retrieve=extend_schema(
        description='Get a specific product recommendation',
        responses={200: ProductRecommendationSerializer}
    ),
    update=extend_schema(
        description='Update a product recommendation',
        request=ProductRecommendationSerializer,
        responses={200: ProductRecommendationSerializer}
    ),
    partial_update=extend_schema(
        description='Partially update a product recommendation',
        request=ProductRecommendationSerializer,
        responses={200: ProductRecommendationSerializer}
    ),
    destroy=extend_schema(
        description='Delete a product recommendation',
        responses={204: None}
    )
)
class RecommendationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing product recommendations.
    
    Recommendation types:
    - similar: Similar Products
    - frequently_bought: Frequently Bought Together
    - personalized: Personalized Recommendation
    """
    queryset = ProductRecommendation.objects.all()
    serializer_class = ProductRecommendationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['recommendation_type']
    ordering_fields = ['score', 'created_at']
    ordering = ['-score']

    def get_queryset(self):
        queryset = super().get_queryset()
        source_product_id = self.request.query_params.get('source_product_id')
        if source_product_id:
            queryset = queryset.filter(source_product_id=source_product_id)
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('category').all()
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
