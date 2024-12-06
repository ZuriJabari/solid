from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from datetime import timedelta
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

class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing analytics data"""
    
    def get_serializer_class(self):
        if self.action == 'sales':
            return SalesMetricSerializer
        elif self.action == 'inventory':
            return InventoryMetricSerializer
        elif self.action == 'customers':
            return CustomerMetricSerializer
        elif self.action == 'products':
            return ProductPerformanceSerializer
        elif self.action == 'generate_report':
            return DateRangeSerializer
        return AnalyticsSummarySerializer

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """Get sales metrics for the last 30 days"""
        start_date = timezone.now().date() - timedelta(days=30)
        metrics = SalesMetric.objects.filter(
            date__gte=start_date
        ).order_by('-date')
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inventory(self, request):
        """Get inventory metrics for the last 30 days"""
        start_date = timezone.now().date() - timedelta(days=30)
        metrics = InventoryMetric.objects.filter(
            date__gte=start_date
        ).order_by('-date')
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def customers(self, request):
        """Get customer metrics for the last 30 days"""
        start_date = timezone.now().date() - timedelta(days=30)
        metrics = CustomerMetric.objects.filter(
            date__gte=start_date
        ).order_by('-date')
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def products(self, request):
        """Get product performance metrics for the last 30 days"""
        start_date = timezone.now().date() - timedelta(days=30)
        metrics = ProductPerformance.objects.filter(
            date__gte=start_date
        ).order_by('-date')
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all analytics metrics"""
        # Get the latest metrics
        latest_customer_metrics = CustomerMetric.objects.latest('date')
        latest_sales = SalesMetric.objects.latest('date')
        
        # Get best selling products
        best_selling = ProductPerformance.objects.order_by('-revenue')[:5]
        
        data = {
            'total_revenue': latest_sales.total_sales,
            'total_orders': latest_sales.order_count,
            'average_order_value': latest_sales.average_order_value,
            'total_customers': latest_customer_metrics.total_customers,
            'best_selling_products': ProductPerformanceSerializer(
                best_selling, many=True
            ).data,
            'customer_retention_rate': (
                latest_customer_metrics.returning_customers /
                latest_customer_metrics.total_customers * 100
                if latest_customer_metrics.total_customers > 0 else 0
            ),
            'inventory_turnover_rate': self._calculate_inventory_turnover()
        }
        
        serializer = self.get_serializer(data)
        return Response(serializer.data)

    def _calculate_inventory_turnover(self):
        """Calculate the inventory turnover rate"""
        latest_metrics = InventoryMetric.objects.order_by('-date')
        if not latest_metrics.exists():
            return 0
        
        total_sold = latest_metrics.aggregate(
            sold=Sum('units_sold')
        )['sold'] or 0
        total_stock = latest_metrics.aggregate(
            stock=Sum('closing_stock')
        )['stock'] or 1  # Avoid division by zero
        
        return (total_sold / total_stock) * 100

    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate a detailed analytics report for a date range"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        
        # Get metrics for the date range
        sales_metrics = SalesMetric.objects.filter(
            date__range=(start_date, end_date)
        )
        inventory_metrics = InventoryMetric.objects.filter(
            date__range=(start_date, end_date)
        )
        customer_metrics = CustomerMetric.objects.filter(
            date__range=(start_date, end_date)
        )
        product_metrics = ProductPerformance.objects.filter(
            date__range=(start_date, end_date)
        )
        
        # Compile report data
        report = {
            'sales': SalesMetricSerializer(
                sales_metrics, many=True
            ).data,
            'inventory': InventoryMetricSerializer(
                inventory_metrics, many=True
            ).data,
            'customers': CustomerMetricSerializer(
                customer_metrics, many=True
            ).data,
            'products': ProductPerformanceSerializer(
                product_metrics, many=True
            ).data
        }
        
        return Response(report)
