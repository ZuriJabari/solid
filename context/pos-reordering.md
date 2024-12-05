# POS Integration and Automated Reordering System

## Backend Implementation

### 1. Purchase Order Models (purchasing/models.py)
```python
from django.db import models
from django.core.validators import MinValueValidator

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    order_date = models.DateTimeField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            next_number = '1' if not last_po else str(int(last_po.po_number[2:]) + 1)
            self.po_number = f'PO{next_number.zfill(6)}'
        super().save(*args, **kwargs)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

### 2. POS Models (pos/models.py)
```python
from django.db import models

class POSSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]

    cashier = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    opening_time = models.DateTimeField(auto_now_add=True)
    closing_time = models.DateTimeField(null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mobile_money_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

class POSOrder(models.Model):
    session = models.ForeignKey(POSSession, on_delete=models.PROTECT)
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = POSOrder.objects.order_by('-id').first()
            next_number = '1' if not last_order else str(int(last_order.order_number[3:]) + 1)
            self.order_number = f'POS{next_number.zfill(6)}'
        super().save(*args, **kwargs)

class POSOrderItem(models.Model):
    order = models.ForeignKey(POSOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
```

### 3. Automated Reordering Service (purchasing/services.py)
```python
from datetime import datetime, timedelta
from django.db.models import Sum, F, ExpressionWrapper, fields
from django.db.models.functions import Coalesce

class AutoReorderService:
    @staticmethod
    def check_reorder_points():
        """Check all products against their reorder points and create purchase orders if needed."""
        products_to_reorder = Product.objects.annotate(
            total_stock=Coalesce(Sum('batches__quantity'), 0),
            pending_po_quantity=Coalesce(
                Sum('purchaseorderitem__quantity', 
                    filter=models.Q(purchaseorderitem__purchase_order__status__in=['PENDING', 'APPROVED', 'ORDERED'])),
                0
            ),
            effective_stock=F('total_stock') + F('pending_po_quantity')
        ).filter(
            effective_stock__lte=F('reorderpoint__minimum_quantity'),
            is_active=True
        )

        suppliers_pos = {}
        for product in products_to_reorder:
            if not product.default_supplier_id:
                continue

            if product.default_supplier_id not in suppliers_pos:
                suppliers_pos[product.default_supplier_id] = {
                    'items': [],
                    'total': 0
                }

            reorder_quantity = product.reorderpoint.reorder_quantity
            unit_price = product.supplier_products.get(
                supplier_id=product.default_supplier_id
            ).unit_price

            suppliers_pos[product.default_supplier_id]['items'].append({
                'product': product,
                'quantity': reorder_quantity,
                'unit_price': unit_price,
                'total_price': reorder_quantity * unit_price
            })
            suppliers_pos[product.default_supplier_id]['total'] += reorder_quantity * unit_price

        # Create purchase orders
        for supplier_id, po_data in suppliers_pos.items():
            purchase_order = PurchaseOrder.objects.create(
                supplier_id=supplier_id,
                status='PENDING',
                total_amount=po_data['total'],
                created_by=User.objects.get(username='system')
            )

            for item in po_data['items']:
                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    product=item['product'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )

    @staticmethod
    def get_demand_forecast(product, days=30):
        """Calculate demand forecast based on historical sales."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        daily_sales = OrderItem.objects.filter(
            product=product,
            order__created_at__range=[start_date, end_date]
        ).values('order__created_at__date').annotate(
            total_quantity=Sum('quantity')
        ).order_by('order__created_at__date')

        # Calculate average daily demand
        total_quantity = sum(day['total_quantity'] for day in daily_sales)
        avg_daily_demand = total_quantity / days

        return {
            'avg_daily_demand': avg_daily_demand,
            'recommended_stock': avg_daily_demand * product.reorder_lead_time,
            'daily_sales': list(daily_sales)
        }
```

### 4. POS Service (pos/services.py)
```python
class POSService:
    @staticmethod
    def create_order(session_id, items, payment_method, customer_id=None):
        """Create a new POS order and update inventory."""
        session = POSSession.objects.get(id=session_id)
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        tax = subtotal * Decimal('0.18')  # 18% tax
        total = subtotal + tax

        # Create order
        order = POSOrder.objects.create(
            session=session,
            customer_id=customer_id,
            subtotal=subtotal,
            tax=tax,
            total=total,
            payment_method=payment_method
        )

        # Add items and update inventory
        for item in items:
            POSOrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['quantity'] * item['unit_price']
            )

            # Update inventory
            product = Product.objects.get(id=item['product_id'])
            product.update_stock(-item['quantity'])

        # Update session totals
        if payment_method == 'CASH':
            session.cash_sales += total
        elif payment_method == 'CARD':
            session.card_sales += total
        else:
            session.mobile_money_sales += total
        
        session.total_sales += total
        session.save()

        return order

    @staticmethod
    def close_session(session_id, closing_balance, notes=''):
        """Close a POS session and reconcile cash."""
        session = POSSession.objects.get(id=session_id)
        
        if session.status == 'CLOSED':
            raise ValueError('Session is already closed')

        session.closing_balance = closing_balance
        session.closing_time = timezone.now()
        session.status = 'CLOSED'
        session.notes = notes
        session.save()

        return {
            'cash_difference': closing_balance - (session.opening_balance + session.cash_sales),
            'total_sales': session.total_sales,
            'transaction_count': POSOrder.objects.filter(session=session).count()
        }
```

## Frontend Implementation

### 1. POS Interface (src/pages/pos/POSPage.tsx)
```typescript
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { PlusIcon, MinusIcon, ReceiptIcon } from '@heroicons/react/24/outline';

const POSPage = () => {
  const [cart, setCart] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: products } = useQuery(['products'], fetchProducts);
  const { data: session } = useQuery(['posSession'], getCurrentSession);

  const createOrderMutation = useMutation(createPOSOrder, {
    onSuccess: () => {
      setCart([]);
      // Show success message
    }
  });

  const addToCart = (product) => {
    setCart(current => {
      const existing = current.find(item => item.product.id === product.id);
      if (existing) {
        return current.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...current, { product, quantity: 1 }];
    });
  };

  const calculateTotals = () => {
    const subtotal = cart.reduce((sum, item) => 
      sum + (item.product.price * item.quantity), 0
    );
    const tax = subtotal * 0.18;
    return {
      subtotal,
      tax,
      total: subtotal + tax
    };
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Product Selection */}
      <div className="flex-1 overflow-auto p-4">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search products..."
            className="w-full p-2 border rounded"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex space-x-2 mb-4">
          {categories.map(category => (
            <button
              key={category.id}
              className={`px-4 py-2 rounded ${
                selectedCategory === category.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white'
              }`}
              onClick={() => setSelectedCategory(category.id)}
            >
              {category.name}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4">
          {filteredProducts.map(product => (
            <button
              key={product.id}
              className="p-4 bg-white rounded-lg shadow hover:shadow-md"
              onClick={() => addToCart(product)}
            >
              <img
                src={product.image}
                alt={product.name}
                className="w-full h-32 object-cover rounded mb-2"
              />
              <div className="text-left">
                <h3 className="font-medium">{product.name}</h3>
                <p className="text-gray-600">${product.price}</p>
                <p className="text-sm text-gray-500">
                  Stock: {product.stock}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Cart */}
      <div className="w-96 bg-white border-l">
        <div className="h-full flex flex-col">
          <div className="p-4 border-b">
            <h2 className="text-lg font-medium">Current Order</h2>
          </div>

          <div className="flex-1 overflow-auto p-4">
            {cart.map(item => (
              <div key={item.product.id} className="flex items-center mb-4">
                <div className="flex-1">
                  <h3 className="font-