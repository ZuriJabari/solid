# Reporting and Inventory Management Implementation

## Backend Implementation

### 1. Reporting Models (reporting/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class Report(models.Model):
    REPORT_TYPES = [
        ('SALES', 'Sales Report'),
        ('INVENTORY', 'Inventory Report'),
        ('DELIVERY', 'Delivery Performance'),
        ('CUSTOMER', 'Customer Analysis'),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    filters = JSONField(default=dict)
    data = JSONField()
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]

    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    recipients = models.ManyToManyField('accounts.User')
    last_sent = models.DateTimeField(null=True)
    next_scheduled = models.DateTimeField()
    is_active = models.BooleanField(default=True)

### 2. Enhanced Inventory Models (inventory/models.py)
```python
from django.db import models
from django.core.validators import MinValueValidator

class Batch(models.Model):
    batch_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True)
    lab_report = models.FileField(upload_to='lab_reports/', null=True, blank=True)
    cbd_content = models.DecimalField(max_digits=5, decimal_places=2)
    thc_content = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.batch_number:
            prefix = self.product.sku[:3]
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            self.batch_number = f"{prefix}-{timestamp}"
        super().save(*args, **kwargs)

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    license_number = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ('RESTOCK', 'Restock'),
        ('DAMAGE', 'Damage'),
        ('EXPIRED', 'Expired'),
        ('RETURN', 'Return'),
        ('CORRECTION', 'Correction'),
    ]

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField()
    adjusted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    adjusted_at = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=50, blank=True)

class InventoryCount(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    counted_quantity = models.IntegerField()
    system_quantity = models.IntegerField()
    difference = models.IntegerField()
    counted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    counted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

class ReorderPoint(models.Model):
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE)
    minimum_quantity = models.IntegerField()
    reorder_quantity = models.IntegerField()
    last_reorder_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### 3. Report Generation Service (reporting/services.py)
```python
from datetime import datetime, timedelta
from typing import Dict, Any
from django.db.models import Sum, Avg, Count, F
from django.db.models.functions import TruncDate

class ReportingService:
    @staticmethod
    def generate_sales_report(start_date: datetime, end_date: datetime, filters: Dict = None) -> Dict[str, Any]:
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status='COMPLETED'
        )

        if filters:
            if 'category' in filters:
                orders = orders.filter(items__product__category_id=filters['category'])
            if 'delivery_type' in filters:
                orders = orders.filter(delivery_type=filters['delivery_type'])

        # Daily sales breakdown
        daily_sales = orders.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_sales=Sum('total'),
            order_count=Count('id'),
            average_order_value=Avg('total')
        ).order_by('date')

        # Product performance
        product_performance = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__name',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total'),
            average_rating=Avg('product__reviews__rating')
        ).order_by('-total_sales')

        # Customer demographics
        customer_data = orders.values(
            'user__age_group',
            'user__city'
        ).annotate(
            customer_count=Count('user', distinct=True),
            total_spent=Sum('total')
        )

        return {
            'summary': {
                'total_sales': orders.aggregate(Sum('total'))['total__sum'],
                'total_orders': orders.count(),
                'average_order_value': orders.aggregate(Avg('total'))['total__avg'],
                'unique_customers': orders.values('user').distinct().count()
            },
            'daily_sales': list(daily_sales),
            'product_performance': list(product_performance),
            'customer_data': list(customer_data)
        }

    @staticmethod
    def generate_inventory_report() -> Dict[str, Any]:
        products = Product.objects.all()
        
        inventory_data = products.annotate(
            total_stock=Sum('batches__quantity'),
            stock_value=F('total_stock') * F('price'),
            pending_orders=Count('orderitems', filter=Q(orderitems__order__status='PENDING')),
            reorder_needed=Case(
                When(total_stock__lte=F('reorderpoint__minimum_quantity'), then=True),
                default=False
            )
        )

        expiring_soon = Batch.objects.filter(
            expiry_date__lte=timezone.now() + timedelta(days=90)
        ).select_related('product')

        return {
            'summary': {
                'total_products': products.count(),
                'total_stock_value': inventory_data.aggregate(Sum('stock_value'))['stock_value__sum'],
                'low_stock_items': inventory_data.filter(reorder_needed=True).count(),
                'expiring_items': expiring_soon.count()
            },
            'inventory_data': list(inventory_data.values(
                'id', 'name', 'category__name', 'total_stock', 
                'stock_value', 'pending_orders', 'reorder_needed'
            )),
            'expiring_batches': list(expiring_soon.values(
                'product__name', 'batch_number', 'quantity',
                'expiry_date'
            ))
        }
```

## Frontend Implementation

### 1. Report Generation Interface (src/pages/admin/ReportsPage.tsx)
```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import DatePicker from 'react-datepicker';
import {
  Bar,
  Line,
  Pie
} from 'react-chartjs-2';

const ReportsPage = () => {
  const [reportType, setReportType] = useState('SALES');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    end: new Date()
  });
  const [filters, setFilters] = useState({});

  const { data: report, isLoading } = useQuery(
    ['report', reportType, dateRange, filters],
    () => generateReport(reportType, dateRange, filters)
  );

  const renderSalesReport = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(report.summary).map(([key, value]) => (
          <div key={key} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <dt className="text-sm font-medium text-gray-500 truncate">
                {key.replace('_', ' ').toUpperCase()}
              </dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </dd>
            </div>
          </div>
        ))}
      </div>

      {/* Sales Trend Chart */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Sales Trend</h3>
        <div className="h-96">
          <Line
            data={{
              labels: report.daily_sales.map(d => d.date),
              datasets: [{
                label: 'Daily Sales',
                data: report.daily_sales.map(d => d.total_sales),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
              }]
            }}
            options={{ maintainAspectRatio: false }}
          />
        </div>
      </div>

      {/* Product Performance */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Products</h3>
        <div className="h-96">
          <Bar
            data={{
              labels: report.product_performance.map(p => p.product__name),
              datasets: [{
                label: 'Sales',
                data: report.product_performance.map(p => p.total_sales),
                backgroundColor: 'rgba(75, 192, 192, 0.2)'
              }]
            }}
            options={{ maintainAspectRatio: false }}
          />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Report Controls */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="SALES">Sales Report</option>
              <option value="INVENTORY">Inventory Report</option>
              <option value="DELIVERY">Delivery Performance</option>
              <option value="CUSTOMER">Customer Analysis</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Date Range
            </label>
            <DatePicker
              selectsRange
              startDate={dateRange.start}
              endDate={dateRange.end}
              onChange={(update) => {
                setDateRange({
                  start: update[0],
                  end: update[1] || update[0]
                });
              }}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Report Content */}
      {isLoading ? (
        <div className="flex justify-center">
          <div className="loader">Loading...</div>
        </div>
      ) : (
        reportType === 'SALES' ? renderSalesReport() : null
        // Add other report type renderers here
      )}
    </div>
  );
};

export default ReportsPage;
```

### 2. Inventory Management Interface (src/pages/admin/InventoryPage.tsx)
```typescript
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

const InventoryPage = () => {
  const [selectedProduct, setSelectedProduct] = useState(null);
  const queryClient = useQueryClient();

  const { data: inventory, isLoading } = useQuery(
    ['inventory'],
    fetchInventory
  );

  const adjustStockMutation = useMutation(adjustStock, {
    onSuccess: () => {
      queryClient.invalidateQueries(['inventory']);
    }
  });

  return (
    <div className="space-y-6">
      {/* Inventory Alerts */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex