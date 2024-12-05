# Automated Reordering and POS Integration

## 1. Automated Reordering System

### Reorder Service (services/reorder_service.py)
```python
from django.db.models import F, Sum, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from decimal import Decimal

class ReorderService:
    @staticmethod
    def check_stock_levels():
        """Monitor stock levels and generate purchase orders"""
        products_to_reorder = Product.objects.annotate(
            current_stock=Coalesce(Sum('batches__quantity'), 0),
            pending_orders=Coalesce(
                Sum('purchaseorderitems__quantity', 
                    filter=Q(purchaseorderitems__order__status__in=['PENDING', 'ORDERED'])),
                0
            ),
            effective_stock=F('current_stock') + F('pending_orders')
        ).filter(
            effective_stock__lte=F('reorder_point'),
            auto_reorder=True,
            is_active=True
        )

        for product in products_to_reorder:
            ReorderService._generate_purchase_order(product)

    @staticmethod
    def _generate_purchase_order(product):
        """Generate purchase order for a product"""
        supplier = product.preferred_supplier
        if not supplier:
            return None

        # Calculate optimal order quantity
        reorder_quantity = ReorderService._calculate_reorder_quantity(product)
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            supplier=supplier,
            status='DRAFT',
            created_by_system=True
        )

        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity=reorder_quantity,
            unit_price=product.supplier_price
        )

        # Send notifications
        NotificationService.send_reorder_notification(purchase_order)
        return purchase_order

    @staticmethod
    def _calculate_reorder_quantity(product):
        """Calculate optimal reorder quantity using EOQ formula"""
        annual_demand = OrderItem.objects.filter(
            product=product,
            order__created_at__gte=timezone.now() - timedelta(days=365)
        ).aggregate(
            total_demand=Coalesce(Sum('quantity'), 0)
        )['total_demand']

        holding_cost = Decimal('0.2')  # 20% of product cost
        ordering_cost = Decimal('50.00')  # Fixed cost per order

        eoq = sqrt(
            (2 * annual_demand * ordering_cost) /
            (product.supplier_price * holding_cost)
        )
        
        return ceil(eoq)

class SupplierIntegrationService:
    @staticmethod
    def send_purchase_order(purchase_order):
        """Send purchase order to supplier's system"""
        supplier = purchase_order.supplier
        
        if supplier.api_integration_type == 'API':
            return SupplierIntegrationService._send_api_order(purchase_order)
        elif supplier.api_integration_type == 'EMAIL':
            return SupplierIntegrationService._send_email_order(purchase_order)
        
        return False

    @staticmethod
    def check_order_status(purchase_order):
        """Check status of purchase order with supplier"""
        if purchase_order.supplier.api_integration_type != 'API':
            return None

        try:
            response = requests.get(
                f"{purchase_order.supplier.api_url}/orders/{purchase_order.supplier_reference}",
                headers={"Authorization": f"Bearer {purchase_order.supplier.api_key}"}
            )
            return response.json()['status']
        except Exception as e:
            logger.error(f"Error checking order status: {str(e)}")
            return None
```

### Stock Monitoring Task (tasks.py)
```python
from celery import shared_task
from .services import ReorderService

@shared_task
def monitor_stock_levels():
    """Periodic task to check stock levels and generate purchase orders"""
    ReorderService.check_stock_levels()

@shared_task
def update_purchase_order_status():
    """Update status of pending purchase orders"""
    pending_orders = PurchaseOrder.objects.filter(
        status__in=['ORDERED', 'PENDING']
    )
    
    for order in pending_orders:
        status = SupplierIntegrationService.check_order_status(order)
        if status:
            order.status = status
            order.save()
```

## 2. POS Integration

### POS Service (services/pos_service.py)
```python
class POSService:
    @staticmethod
    def process_sale(session_id, items, payment_method, customer=None):
        """Process a sale and update inventory"""
        with transaction.atomic():
            # Create sale record
            sale = Sale.objects.create(
                session_id=session_id,
                customer=customer,
                payment_method=payment_method
            )

            total_amount = Decimal('0.00')
            
            # Process items and update inventory
            for item in items:
                product = Product.objects.select_for_update().get(
                    id=item['product_id']
                )
                
                # Validate stock
                if product.current_stock < item['quantity']:
                    raise InsufficientStockError(
                        f"Insufficient stock for {product.name}"
                    )

                # Create sale item
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item['quantity'],
                    unit_price=product.current_price,
                    total_price=product.current_price * item['quantity']
                )

                # Update inventory
                product.update_stock(-item['quantity'])
                total_amount += product.current_price * item['quantity']

            # Update sale totals
            sale.subtotal = total_amount
            sale.tax = total_amount * Decimal('0.18')  # 18% tax
            sale.total = sale.subtotal + sale.tax
            sale.save()

            # Update session totals
            session = POSSession.objects.get(id=session_id)
            session.update_totals(sale)

            return sale

    @staticmethod
    def generate_receipt(sale_id):
        """Generate receipt for a sale"""
        sale = Sale.objects.get(id=sale_id)
        
        receipt_data = {
            'company_name': 'CBD Store',
            'sale_number': sale.number,
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{
                'name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.total_price)
            } for item in sale.items.all()],
            'subtotal': float(sale.subtotal),
            'tax': float(sale.tax),
            'total': float(sale.total),
            'payment_method': sale.payment_method,
            'cashier': sale.session.cashier.get_full_name()
        }

        return receipt_data
```

### Real-time Inventory Updates (models.py)
```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    current_stock = models.IntegerField(default=0)
    reorder_point = models.IntegerField()
    auto_reorder = models.BooleanField(default=True)
    preferred_supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.SET_NULL, 
        null=True
    )

    def update_stock(self, quantity_change):
        """Update stock with real-time validation"""
        if self.current_stock + quantity_change < 0:
            raise InsufficientStockError(
                f"Insufficient stock for {self.name}"
            )

        self.current_stock += quantity_change
        self.save()

        if self.current_stock <= self.reorder_point:
            transaction.on_commit(
                lambda: monitor_stock_levels.delay()
            )

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
        ('ADJUSTMENT', 'Adjustment'),
        ('RETURN', 'Return')
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=50)
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new records
            self.previous_stock = self.product.current_stock
            self.new_stock = self.previous_stock + self.quantity
        super().save(*args, **kwargs)
```

### Till Management (models.py)
```python
class POSSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed')
    ]

    cashier = models.ForeignKey('User', on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True
    )
    cash_sales = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    card_sales = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    mobile_money_sales = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='OPEN'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)

    def update_totals(self, sale):
        """Update session totals after a sale"""
        if sale.payment_method == 'CASH':
            self.cash_sales += sale.total
        elif sale.payment_method == 'CARD':
            self.card_sales += sale.total
        elif sale.payment_method == 'MOBILE_MONEY':
            self.mobile_money_sales += sale.total
        self.save()

    def close_session(self, closing_balance):
        """Close the session and calculate differences"""
        self.closing_balance = closing_balance
        self.ended_at = timezone.now()
        self.status = 'CLOSED'
        self.save()

        expected_cash = self.opening_balance + self.cash_sales
        cash_difference = closing_balance - expected_cash

        return {
            'expected_cash': expected_cash,
            'actual_cash': closing_balance,
            'difference': cash_difference,
            'total_sales': self.cash_sales + self.card_sales + self.mobile_money_sales
        }
```

This implementation provides:

1. Automated Reordering:
- Smart stock level monitoring
- Economic Order Quantity calculation
- Supplier integration
- Automated purchase order generation

2. POS Integration:
- Real-time inventory updates
- Accurate stock tracking
- Multi-payment support
- Till management
- Detailed receipt generation

3. Key Features:
- Transaction atomicity
- Stock movement tracking
- Automated reorder triggers
- Session management
- Cash reconciliation

Would you like me to implement additional features such as:
1. Supplier portal integration
2. Advanced inventory analytics
3. Multi-location support
4. Batch tracking system

Let me know which aspects you'd like to explore next!