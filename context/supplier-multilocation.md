# Supplier Portal and Multi-location Support Implementation

## Backend Implementation

### 1. Supplier Portal Models (supplier/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class SupplierAccount(models.Model):
    supplier = models.OneToOneField('inventory.Supplier', on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    delivery_zones = models.ManyToManyField('locations.DeliveryZone')
    delivery_days = JSONField(default=dict)  # Store delivery schedule
    payment_terms = models.IntegerField(default=30)  # Net days
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class SupplierDeliverySchedule(models.Model):
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    location = models.ForeignKey('locations.Location', on_delete=models.CASCADE)
    day_of_week = models.IntegerField()  # 0-6 for Monday-Sunday
    delivery_window_start = models.TimeField()
    delivery_window_end = models.TimeField()
    notes = models.TextField(blank=True)

class SupplierInvoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('DISPUTED', 'Disputed')
    ]

    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50)
    purchase_order = models.ForeignKey('purchasing.PurchaseOrder', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='supplier_invoices/')

class SupplierMessage(models.Model):
    MESSAGE_TYPES = [
        ('ORDER', 'Order Related'),
        ('DELIVERY', 'Delivery Related'),
        ('INVOICE', 'Invoice Related'),
        ('GENERAL', 'General')
    ]

    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    reference = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True)

### 2. Multi-location Models (locations/models.py)
```python
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

class Location(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    address = models.TextField()
    point = models.PointField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    operating_hours = JSONField()
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class LocationInventory(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    reorder_point = models.IntegerField()
    reorder_quantity = models.IntegerField()
    last_restock_date = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ['location', 'product']

class LocationPricing(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    sale_start_date = models.DateTimeField(null=True)
    sale_end_date = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ['location', 'product']

class InventoryTransfer(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('IN_TRANSIT', 'In Transit'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    transfer_number = models.CharField(max_length=20, unique=True)
    source_location = models.ForeignKey(Location, related_name='transfers_out', on_delete=models.PROTECT)
    destination_location = models.ForeignKey(Location, related_name='transfers_in', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    requested_by = models.ForeignKey('accounts.User', related_name='requested_transfers', on_delete=models.PROTECT)
    approved_by = models.ForeignKey('accounts.User', related_name='approved_transfers', null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    notes = models.TextField(blank=True)

class TransferItem(models.Model):
    transfer = models.ForeignKey(InventoryTransfer, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    received_quantity = models.IntegerField(null=True)
    notes = models.TextField(blank=True)

class ProductReservation(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    reserved_for = models.CharField(max_length=100)
    reserved_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

### 3. Location Management Service (services/location_service.py)
```python
from django.db import transaction
from django.db.models import F, Sum
from datetime import datetime, timedelta

class LocationService:
    @staticmethod
    def update_inventory(location_id, product_id, quantity_change, reference):
        """Update inventory levels for a specific location"""
        with transaction.atomic():
            inventory = LocationInventory.objects.select_for_update().get(
                location_id=location_id,
                product_id=product_id
            )
            
            if inventory.quantity + quantity_change < 0:
                raise ValueError("Insufficient stock")

            inventory.quantity = F('quantity') + quantity_change
            inventory.save()

            InventoryMovement.objects.create(
                location_id=location_id,
                product_id=product_id,
                quantity_change=quantity_change,
                reference=reference
            )

    @staticmethod
    def check_reorder_points(location_id):
        """Check reorder points for all products in a location"""
        products_to_reorder = LocationInventory.objects.filter(
            location_id=location_id,
            quantity__lte=F('reorder_point')
        ).select_related('product')

        for inventory in products_to_reorder:
            PurchaseOrderService.create_order(
                location_id=location_id,
                product_id=inventory.product_id,
                quantity=inventory.reorder_quantity
            )

    @staticmethod
    def create_transfer(source_location_id, destination_location_id, items, requested_by):
        """Create an inventory transfer between locations"""
        with transaction.atomic():
            transfer = InventoryTransfer.objects.create(
                source_location_id=source_location_id,
                destination_location_id=destination_location_id,
                requested_by=requested_by,
                status='PENDING'
            )

            for item in items:
                # Validate stock availability
                inventory = LocationInventory.objects.get(
                    location_id=source_location_id,
                    product_id=item['product_id']
                )
                if inventory.quantity < item['quantity']:
                    raise ValueError(f"Insufficient stock for product {item['product_id']}")

                TransferItem.objects.create(
                    transfer=transfer,
                    product_id=item['product_id'],
                    quantity=item['quantity']
                )

            return transfer

    @staticmethod
    def complete_transfer(transfer_id, received_items):
        """Complete an inventory transfer"""
        with transaction.atomic():
            transfer = InventoryTransfer.objects.select_related(
                'source_location', 'destination_location'
            ).get(id=transfer_id)

            if transfer.status != 'IN_TRANSIT':
                raise ValueError("Transfer must be in transit")

            for received_item in received_items:
                transfer_item = transfer.items.get(
                    product_id=received_item['product_id']
                )
                transfer_item.received_quantity = received_item['quantity']
                transfer_item.save()

                # Update inventory at both locations
                LocationService.update_inventory(
                    transfer.source_location_id,
                    received_item['product_id'],
                    -received_item['quantity'],
                    f"Transfer #{transfer.transfer_number}"
                )

                LocationService.update_inventory(
                    transfer.destination_location_id,
                    received_item['product_id'],
                    received_item['quantity'],
                    f"Transfer #{transfer.transfer_number}"
                )

            transfer.status = 'COMPLETED'
            transfer.completed_at = timezone.now()
            transfer.save()
```

### 4. Supplier Portal Service (services/supplier_service.py)
```python
class SupplierPortalService:
    @staticmethod
    def process_supplier_order_response(order_id, response):
        """Handle supplier's response to purchase order"""
        with transaction.atomic():
            order = PurchaseOrder.objects.get(id=order_id)
            
            if response['status'] == 'ACCEPTED':
                order.status = 'CONFIRMED'
                order.expected_delivery_date = response['delivery_date']
                
                # Create delivery schedule
                SupplierDeliverySchedule.objects.create(
                    supplier=order.supplier,
                    location=order.location,
                    delivery_date=response['delivery_date'],
                    delivery_window_start=response['delivery_window_start'],
                    delivery_window_end=response['delivery_window_end']
                )
            
            elif response['status'] == 'MODIFIED':
                # Handle modifications to order
                for item_modification in response['modifications']:
                    order_item = order.items.get(
                        product_id=item_modification['product_id']
                    )
                    order_item.quantity = item_modification['new_quantity']
                    order_item.unit_price = item_modification['new_price']
                    order_item.save()
                
                order.status = 'PENDING_APPROVAL'
            
            else:  # REJECTED
                order.status = 'REJECTED'
                order.notes = f"Rejected by supplier: {response['reason']}"
            
            order.save()

    @staticmethod
    def process_supplier_invoice(invoice_data):
        """Process invoice received from supplier"""
        with transaction.atomic():
            # Validate invoice against purchase order
            purchase_order = PurchaseOrder.objects.get(
                id=invoice_data['purchase_order_id']
            )
            
            if purchase_order.status != 'RECEIVED':
                raise ValueError("Cannot process invoice for incomplete order")

            # Create invoice record
            invoice = SupplierInvoice.objects.create(
                supplier=purchase_order.supplier,
                invoice_number=invoice_data['invoice_number'],
                purchase_order=purchase_order,
                amount=invoice_data['amount'],
                tax_amount=invoice_data['tax_amount'],
                total_amount=invoice_data['total_amount'],
                due_date=invoice_data['due_date'],
                status='PENDING'
            )

            # Process payment if auto-pay is enabled
            if purchase_order.supplier.auto_pay:
                PaymentService.schedule_payment(invoice)

            return invoice

    @staticmethod
    def send_supplier_message(supplier_id, message_data):
        """Send message to supplier"""
        message = SupplierMessage.objects.create(
            supplier_id=supplier_id,
            message_type=message_data['type'],
            subject=message_data['subject'],
            content=message_data['content'],
            reference=message_data.get('reference', ''),
            created_by=message_data['user']
        )

        # Send email notification
        NotificationService.send_supplier_message_notification(message)
        
        return message
```

This implementation provides:

1. Supplier Portal Features:
- Order management and response system
- Delivery scheduling
- Invoice processing
- Communication system
- Payment terms management

2. Multi-location Support:
- Location-specific inventory tracking
- Inter-store transfers
- Location-based pricing
- Stock reservations
- Reorder point management

3. Key Features:
- Transaction management
- Stock validation
- Audit trails
- Automated notifications
- Payment processing

Would you like me to implement:
1. Supplier performance analytics
2. Advanced inventory forecasting
3. Route optimization for transfers
4. Integrated payment processing

Let me know which aspects you'd like to explore next!