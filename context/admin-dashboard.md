# Admin Dashboard Implementation

## Backend Implementation

### 1. Analytics Models (analytics/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class SalesMetrics(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    order_count = models.IntegerField()
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_sales = models.DecimalField(max_digits=12, decimal_places=2)
    pickup_sales = models.DecimalField(max_digits=12, decimal_places=2)
    metrics_data = JSONField()  # Stores detailed metrics

class InventoryLog(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # STOCK_ADD, STOCK_REMOVE, SALE, etc.
    quantity = models.IntegerField()
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

class DeliveryMetrics(models.Model):
    date = models.DateField()
    driver = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    deliveries_completed = models.IntegerField()
    average_delivery_time = models.DurationField()
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2)
    customer_ratings = JSONField()
```

### 2. Analytics Service (analytics/services.py)
```python
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import SalesMetrics, InventoryLog, DeliveryMetrics
from orders.models import Order

class AnalyticsService:
    @staticmethod
    def generate_daily_metrics():
        today = timezone.now().date()
        daily_orders = Order.objects.filter(
            created_at__date=today,
            status__in=['COMPLETED', 'DELIVERED']
        )

        metrics = {
            'total_sales': daily_orders.aggregate(Sum('total'))['total__sum'] or 0,
            'order_count': daily_orders.count(),
            'average_order_value': daily_orders.aggregate(Avg('total'))['total__avg'] or 0,
            'delivery_sales': daily_orders.filter(delivery_type='DELIVERY')
                .aggregate(Sum('total'))['total__sum'] or 0,
            'pickup_sales': daily_orders.filter(delivery_type='PICKUP')
                .aggregate(Sum('total'))['total__sum'] or 0,
            'metrics_data': {
                'sales_by_category': list(daily_orders.values('items__product__category__name')
                    .annotate(total=Sum('items__total'))),
                'sales_by_hour': list(daily_orders.values('created_at__hour')
                    .annotate(count=Count('id'))),
                'popular_products': list(daily_orders.values('items__product__name')
                    .annotate(count=Count('id'))
                    .order_by('-count')[:10]),
            }
        }

        SalesMetrics.objects.create(date=today, **metrics)
        return metrics

    @staticmethod
    def get_inventory_alerts():
        from products.models import Product
        low_stock_threshold = 10  # Configure as needed

        return Product.objects.filter(
            stock__lte=low_stock_threshold,
            is_active=True
        ).values('id', 'name', 'stock')

    @staticmethod
    def get_delivery_performance(start_date, end_date):
        return DeliveryMetrics.objects.filter(
            date__range=[start_date, end_date]
        ).values('driver__first_name', 'driver__last_name')
        .annotate(
            total_deliveries=Sum('deliveries_completed'),
            avg_delivery_time=Avg('average_delivery_time'),
            avg_rating=Avg('customer_ratings__rating')
        )
```

### 3. Admin API Views (admin/views.py)
```python
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import (
    DashboardMetricsSerializer, 
    InventoryLogSerializer,
    DeliveryMetricsSerializer
)

class DashboardMetricsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        metrics = {
            'sales_metrics': SalesMetrics.objects.filter(
                date__range=[start_date, end_date]
            ),
            'inventory_alerts': AnalyticsService.get_inventory_alerts(),
            'delivery_performance': AnalyticsService.get_delivery_performance(
                start_date, end_date
            ),
            'recent_orders': Order.objects.order_by('-created_at')[:10],
        }

        serializer = DashboardMetricsSerializer(metrics)
        return Response(serializer.data)
```

## Frontend Implementation

### 1. Dashboard Layout (src/pages/admin/DashboardLayout.tsx)
```typescript
import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

const DashboardLayout = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Sidebar />
      <div className="lg:pl-64">
        <Header />
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
```

### 2. Dashboard Overview (src/pages/admin/DashboardOverview.tsx)
```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { fetchDashboardMetrics } from '../../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const DashboardOverview = () => {
  const { data: metrics, isLoading } = useQuery(
    ['dashboardMetrics'],
    () => fetchDashboardMetrics(),
    { refetchInterval: 300000 } // Refresh every 5 minutes
  );

  if (isLoading) return <div>Loading...</div>;

  const salesData = {
    labels: metrics.sales_metrics.map(m => m.date),
    datasets: [
      {
        label: 'Total Sales',
        data: metrics.sales_metrics.map(m => m.total_sales),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CurrencyDollarIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Today's Sales
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ${metrics.today_sales.toLocaleString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShoppingBagIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Orders Today
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {metrics.today_orders}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TruckIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Deliveries
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {metrics.active_deliveries}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sales Chart */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Sales Overview</h3>
        <div className="h-72">
          <Line data={salesData} options={{ maintainAspectRatio: false }} />
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg font-medium text-gray-900">Recent Orders</h3>
        </div>
        <div className="border-t border-gray-200">
          <ul className="divide-y divide-gray-200">
            {metrics.recent_orders.map((order) => (
              <li key={order.id} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        Order #{order.order_number}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(order.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className={`inline-flex rounded-full px-2 text-xs font-semibold ${
                      order.status === 'COMPLETED' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Inventory Alerts */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg font-medium text-gray-900">Low Stock Alerts</h3>
        </div>
        <div className="border-t border-gray-200">
          <ul className="divide-y divide-gray-200">
            {metrics.inventory_alerts.map((alert) => (
              <li key={alert.id} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {alert.name}
                    </p>
                    <p className="text-sm text-red-500">
                      Only {alert.stock} units remaining
                    </p>
                  </div>
                  <button className="text-indigo-600 hover:text-indigo-900">
                    Restock
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
```

This implementation provides:

1. Dashboard Overview:
- Real-time sales metrics
- Order statistics
- Inventory alerts
- Delivery performance tracking

2. Analytics Features:
- Sales trends visualization
- Product performance tracking
- Delivery efficiency metrics
- Inventory movement logs

3. Management Tools:
- Order management
- Stock control
- Delivery staff monitoring
- Customer data analysis

Next, we can implement:
1. Detailed reporting system
2. Inventory management interface
3. Staff management tools
4. Customer relationship management features

Would you like me to continue with any of these features?