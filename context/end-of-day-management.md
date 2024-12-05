# End-of-day Reporting and Cash Management Implementation

## Backend Implementation

### 1. End-of-day Models (reports/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class DailyReport(models.Model):
    date = models.DateField(unique=True)
    store = models.ForeignKey('stores.Store', on_delete=models.CASCADE)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    gross_profit = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = models.IntegerField()
    payment_breakdown = JSONField()  # Stores payment method totals
    hourly_sales = JSONField()       # Stores sales by hour
    product_sales = JSONField()      # Stores sales by product
    category_sales = JSONField()     # Stores sales by category
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)

    class Meta:
        indexes = [
            models.Index(fields=['date', 'store']),
        ]

class CashDrawer(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('SUSPENDED', 'Suspended')
    ]

    store = models.ForeignKey('stores.Store', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    actual_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cash_difference = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True)
    notes = models.TextField(blank=True)

class CashMovement(models.Model):
    MOVEMENT_TYPES = [
        ('SALE', 'Sale'),
        ('REFUND', 'Refund'),
        ('PAYOUT', 'Payout'),
        ('DROP', 'Cash Drop'),
        ('ADD', 'Cash Added')
    ]

    cash_drawer = models.ForeignKey(CashDrawer, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=50)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

### 2. Report Generation Service (reports/services.py)
```python
from datetime import datetime, time
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour

class EndOfDayReportService:
    @staticmethod
    def generate_daily_report(store_id, date, user_id):
        """Generate end of day report for a specific store"""
        # Get all transactions for the day
        start_datetime = datetime.combine(date, time.min)
        end_datetime = datetime.combine(date, time.max)
        
        sales = Sale.objects.filter(
            store_id=store_id,
            created_at__range=(start_datetime, end_datetime)
        )

        # Calculate totals
        sales_data = sales.aggregate(
            total_sales=Sum('total'),
            total_tax=Sum('tax'),
            total_cost=Sum('items__product__cost_price'),
            transaction_count=Count('id')
        )

        # Payment method breakdown
        payment_breakdown = sales.values('payment_method').annotate(
            total=Sum('total'),
            count=Count('id')
        )

        # Hourly sales
        hourly_sales = sales.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('hour')

        # Product sales
        product_sales = sales.values(
            'items__product__id',
            'items__product__name'
        ).annotate(
            quantity=Sum('items__quantity'),
            total=Sum('items__total_price')
        )

        # Category sales
        category_sales = sales.values(
            'items__product__category__name'
        ).annotate(
            total=Sum('items__total_price')
        )

        # Create daily report
        return DailyReport.objects.create(
            date=date,
            store_id=store_id,
            total_sales=sales_data['total_sales'] or 0,
            total_tax=sales_data['total_tax'] or 0,
            total_cost=sales_data['total_cost'] or 0,
            gross_profit=(sales_data['total_sales'] or 0) - (sales_data['total_cost'] or 0),
            transaction_count=sales_data['transaction_count'] or 0,
            payment_breakdown=list(payment_breakdown),
            hourly_sales=list(hourly_sales),
            product_sales=list(product_sales),
            category_sales=list(category_sales),
            generated_by_id=user_id
        )

class CashManagementService:
    @staticmethod
    def open_cash_drawer(store_id, user_id, opening_balance):
        """Open a new cash drawer session"""
        # Ensure no other drawer is open for this user
        active_drawer = CashDrawer.objects.filter(
            assigned_to_id=user_id,
            status='OPEN'
        ).first()
        
        if active_drawer:
            raise ValidationError('User already has an active cash drawer')

        return CashDrawer.objects.create(
            store_id=store_id,
            assigned_to_id=user_id,
            status='OPEN',
            opening_balance=opening_balance
        )

    @staticmethod
    def record_cash_movement(drawer_id, movement_type, amount, reference, user_id, notes=''):
        """Record a cash movement in the drawer"""
        drawer = CashDrawer.objects.get(id=drawer_id)
        if drawer.status != 'OPEN':
            raise ValidationError('Cash drawer is not open')

        return CashMovement.objects.create(
            cash_drawer_id=drawer_id,
            movement_type=movement_type,
            amount=amount,
            reference=reference,
            performed_by_id=user_id,
            notes=notes
        )

    @staticmethod
    def close_cash_drawer(drawer_id, actual_cash, notes=''):
        """Close a cash drawer and reconcile the cash"""
        drawer = CashDrawer.objects.get(id=drawer_id)
        
        # Calculate expected cash
        movements = CashMovement.objects.filter(cash_drawer_id=drawer_id)
        expected_cash = drawer.opening_balance

        for movement in movements:
            if movement.movement_type in ['SALE', 'ADD']:
                expected_cash += movement.amount
            elif movement.movement_type in ['REFUND', 'PAYOUT', 'DROP']:
                expected_cash -= movement.amount

        # Update drawer
        drawer.closing_balance = expected_cash
        drawer.actual_cash = actual_cash
        drawer.cash_difference = actual_cash - expected_cash
        drawer.status = 'CLOSED'
        drawer.closed_at = timezone.now()
        drawer.notes = notes
        drawer.save()

        return {
            'expected_cash': expected_cash,
            'actual_cash': actual_cash,
            'difference': drawer.cash_difference,
            'total_sales': movements.filter(movement_type='SALE').aggregate(
                total=Sum('amount')
            )['total'] or 0
        }
```

## Frontend Implementation

### 1. End-of-day Report Page (src/pages/reports/EndOfDayReport.tsx)
```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  BarChart,
  PieChart
} from 'react-chartjs-2';
import { formatCurrency } from '../../utils/format';

const EndOfDayReport = () => {
  const [date, setDate] = useState(new Date());

  const { data: report, isLoading } = useQuery(
    ['dailyReport', date],
    () => fetchDailyReport(date.toISOString().split('T')[0])
  );

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Date Selection */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">End of Day Report</h1>
        <input
          type="date"
          value={date.toISOString().split('T')[0]}
          onChange={(e) => setDate(new Date(e.target.value))}
          className="border rounded px-3 py-2"
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-gray-500">Total Sales</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(report.total_sales)}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-gray-500">Transactions</h3>
          <p className="text-2xl font-bold">{report.transaction_count}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-gray-500">Gross Profit</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(report.gross_profit)}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-gray-500">Total Tax</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(report.total_tax)}
          </p>
        </div>
      </div>

      {/* Payment Methods */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Payment Methods</h2>
        <div className="h-64">
          <PieChart
            data={{
              labels: report.payment_breakdown.map(p => p.payment_method),
              datasets: [{
                data: report.payment_breakdown.map(p => p.total),
                backgroundColor: [
                  '#10B981',
                  '#3B82F6',
                  '#6366F1',
                  '#8B5CF6'
                ]
              }]
            }}
          />
        </div>
      </div>

      {/* Hourly Sales */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Hourly Sales</h2>
        <div className="h-64">
          <LineChart
            data={{
              labels: report.hourly_sales.map(h => `${h.hour}:00`),
              datasets: [{
                label: 'Sales',
                data: report.hourly_sales.map(h => h.total),
                borderColor: '#3B82F6',
                tension: 0.1
              }]
            }}
          />
        </div>
      </div>

      {/* Top Products */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Top Products</h2>
        <div className="h-64">
          <BarChart
            data={{
              labels: report.product_sales.slice(0, 10).map(p => p.name),
              datasets: [{
                label: 'Sales',
                data: report.product_sales.slice(0, 10).map(p => p.total),
                backgroundColor: '#3B82F6'
              }]
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default EndOfDayReport;
```

### 2. Cash Drawer Management Interface (src/pages/pos/CashDrawerPage.tsx)
```typescript
import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { formatCurrency } from '../../utils/format';

const CashDrawerPage = () => {
  const [showOpenDrawer, setShowOpenDrawer] = useState(false);
  const [showCashMovement, setShowCashMovement] = useState(false);
  const [showCloseDrawer, setShowCloseDrawer] = useState(false);

  const { data: activeDrawer, isLoading } = useQuery(
    ['activeDrawer'],
    fetchActiveDrawer
  );

  const openDrawerMutation = useMutation(openCashDrawer);
  const cashMovementMutation = useMutation(recordCashMovement);
  const closeDrawerMutation = useMutation(closeCashDrawer);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Active Drawer Summary */}
      {activeDrawer ? (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold">Active Cash Drawer</h2>
            <button
              onClick={() => setShowCloseDrawer(true)}
              className="bg-red-600 text-white px-4 py-2 rounded"
            >
              Close Drawer
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-gray-500">Opening Balance</h3>
              <p className="text-2xl font-bold">
                {formatCurrency(activeDrawer.opening_balance)}
              </p>
            </div>
            <div>
              <h3 className="text-gray-500">Current Balance</h3>
              <p className="text-2xl font-bold">
                {formatCurrency(activeDrawer.current_balance)}
              </p>
            </div>
          </div>

          {/* Cash Movement Buttons */}
          <div className="mt-6 flex space-x-4">
            <button
              onClick={() => setShowCashMovement(true)}