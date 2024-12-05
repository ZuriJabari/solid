from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    POTENCY_CHOICES = [
        ('LOW', 'Low (< 10mg)'),
        ('MEDIUM', 'Medium (10-20mg)'),
        ('HIGH', 'High (> 20mg)'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField()
    potency = models.CharField(max_length=10, choices=POTENCY_CHOICES)
    ingredients = models.TextField()
    usage_instructions = models.TextField()
    warnings = models.TextField()
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text='Weight in grams')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

class ProductReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=255)
    comment = models.TextField()
    helpful_votes = models.PositiveIntegerField(default=0)
    unhelpful_votes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    moderation_notes = models.TextField(blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.product.name} ({self.rating}★)"

class ReviewVote(models.Model):
    VOTE_CHOICES = [
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful')
    ]

    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')
        indexes = [
            models.Index(fields=['review', 'vote']),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on create
            if self.vote == 'helpful':
                self.review.helpful_votes = models.F('helpful_votes') + 1
            else:
                self.review.unhelpful_votes = models.F('unhelpful_votes') + 1
            self.review.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.vote == 'helpful':
            self.review.helpful_votes = models.F('helpful_votes') - 1
        else:
            self.review.unhelpful_votes = models.F('unhelpful_votes') - 1
        self.review.save()
        super().delete(*args, **kwargs)

class ProductInventory(models.Model):
    ADJUSTMENT_TYPES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
        ('correction', 'Inventory Correction'),
        ('expired', 'Expired'),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    current_stock = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(
        help_text="Stock level that triggers reorder alert"
    )
    reorder_quantity = models.PositiveIntegerField(
        help_text="Suggested quantity to reorder"
    )
    last_restock_date = models.DateTimeField(null=True, blank=True)
    last_restock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inventory for {self.product.name}"

    def save(self, *args, **kwargs):
        if self.current_stock <= self.reorder_point:
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"Low Stock Alert: {self.product.name}"
            message = (
                f"Product: {self.product.name}\n"
                f"Current Stock: {self.current_stock}\n"
                f"Reorder Point: {self.reorder_point}\n"
                f"Suggested Reorder Quantity: {self.reorder_quantity}"
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.INVENTORY_ALERT_EMAIL],
                    fail_silently=True,
                )
            except:
                pass  # Don't let email failures stop the save
        super().save(*args, **kwargs)

class InventoryBatch(models.Model):
    inventory = models.ForeignKey(
        ProductInventory,
        on_delete=models.CASCADE,
        related_name='batches'
    )
    batch_number = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField()
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost price per unit for this batch"
    )
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    supplier = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f"Batch {self.batch_number} - {self.inventory.product.name}"

class StockAdjustment(models.Model):
    inventory = models.ForeignKey(
        ProductInventory,
        on_delete=models.CASCADE,
        related_name='adjustments'
    )
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments'
    )
    adjustment_type = models.CharField(
        max_length=20,
        choices=ProductInventory.ADJUSTMENT_TYPES
    )
    quantity = models.IntegerField(
        help_text="Use positive for additions, negative for reductions"
    )
    reason = models.TextField()
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Order number, return reference, etc."
    )
    adjusted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory', 'adjustment_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.adjustment_type} - {self.quantity} units"

    def save(self, *args, **kwargs):
        # Update inventory current_stock
        self.inventory.current_stock += self.quantity
        self.inventory.save()
        
        # Update batch quantity if applicable
        if self.batch:
            self.batch.quantity += self.quantity
            self.batch.save()
            
        super().save(*args, **kwargs)

    @property
    def stock(self):
        try:
            return self.inventory.current_stock
        except ProductInventory.DoesNotExist:
            return 0

    @property
    def needs_reorder(self):
        try:
            return self.inventory.current_stock <= self.inventory.reorder_point
        except ProductInventory.DoesNotExist:
            return False

    @property
    def has_expiring_batches(self):
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            thirty_days_later = timezone.now().date() + timedelta(days=30)
            return self.inventory.batches.filter(
                expiry_date__lte=thirty_days_later,
                quantity__gt=0
            ).exists()
        except ProductInventory.DoesNotExist:
            return False
