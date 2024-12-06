from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import (
    SalesMetric, InventoryMetric,
    CustomerMetric, ProductPerformance
)
from .serializers import (
    SalesMetricSerializer, InventoryMetricSerializer,
    CustomerMetricSerializer, ProductPerformanceSerializer,
    DateRangeSerializer, AnalyticsSummarySerializer
)
from products.models import Product
from orders.models import Order

@extend_schema_view(
    list=extend_schema(description='List analytics metrics'),
    retrieve=extend_schema(description='Retrieve specific analytics metric'),
)
class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for analytics metrics.
    """
    permission_classes = [IsAuthenticated]
    queryset = SalesMetric.objects.none()  # Default queryset
    serializer_class = SalesMetricSerializer

    def get_queryset(self):
        """
        Return appropriate queryset based on the action
        """
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset
            
        model_map = {
            'sales': SalesMetric,
            'inventory': InventoryMetric,
            'customers': CustomerMetric,
            'products': ProductPerformance,
        }
        
        metric_type = self.request.query_params.get('type', 'sales')
        model = model_map.get(metric_type, SalesMetric)
        
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        return model.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')

    def get_serializer_class(self):
        """
        Return appropriate serializer class
        """
        serializer_map = {
            'sales': SalesMetricSerializer,
            'inventory': InventoryMetricSerializer,
            'customers': CustomerMetricSerializer,
            'products': ProductPerformanceSerializer,
        }
        
        metric_type = self.request.query_params.get('type', 'sales')
        return serializer_map.get(metric_type, SalesMetricSerializer)

    @extend_schema(
        request=DateRangeSerializer,
        responses={200: AnalyticsSummarySerializer}
    )
    @action(detail=False, methods=['post'])
    def summary(self, request):
        """Get analytics summary for a date range"""
        serializer = DateRangeSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            
            # Calculate summary metrics
            sales_metrics = SalesMetric.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(
                total_revenue=models.Sum('total_sales'),
                total_orders=models.Sum('order_count'),
                avg_order_value=models.Avg('average_order_value')
            )
            
            customer_metrics = CustomerMetric.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(
                total_customers=models.Max('total_customers'),
                retention_rate=models.Avg('returning_customers')
            )
            
            # Get best selling products
            best_sellers = ProductPerformance.objects.filter(
                date__range=[start_date, end_date]
            ).order_by('-revenue')[:5]
            
            summary_data = {
                'total_revenue': sales_metrics['total_revenue'] or 0,
                'total_orders': sales_metrics['total_orders'] or 0,
                'average_order_value': sales_metrics['avg_order_value'] or 0,
                'total_customers': customer_metrics['total_customers'] or 0,
                'best_selling_products': ProductPerformanceSerializer(best_sellers, many=True).data,
                'customer_retention_rate': customer_metrics['retention_rate'] or 0,
                'inventory_turnover_rate': 0  # Placeholder for now
            }
            
            serializer = AnalyticsSummarySerializer(data=summary_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
