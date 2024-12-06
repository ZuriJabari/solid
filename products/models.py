from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from config.currency import MIN_AMOUNT, MAX_AMOUNT, CURRENCY_DECIMAL_PLACES

class Category(MPTTModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at', 'id']

class ProductOption(models.Model):
    """Model for product options like Size, Color, Weight, etc."""
    name = models.CharField(max_length=100)  # e.g., "Size", "Color"
    display_name = models.CharField(max_length=100)  # e.g., "Select Size", "Choose Color"
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order', 'name']

class ProductOptionValue(models.Model):
    """Model for values of product options like S, M, L or Red, Blue, etc."""
    option = models.ForeignKey(ProductOption, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)  # e.g., "S", "Red"
    display_value = models.CharField(max_length=100)  # e.g., "Small", "Red"
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.option.name}: {self.value}"

    class Meta:
        ordering = ['sort_order', 'value']
        unique_together = ['option', 'value']

class ProductVariant(models.Model):
    """Model for product variants (combinations of option values)"""
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    option_values = models.ManyToManyField(ProductOptionValue, related_name='variants')
    price_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        default=Decimal('0'),
        validators=[
            MinValueValidator(Decimal('-999999999')),
            MaxValueValidator(Decimal('999999999'))
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    @property
    def final_price(self):
        return self.product.price + self.price_adjustment

class BulkPricing(models.Model):
    """Model for bulk pricing rules"""
    product = models.ForeignKey(Product, related_name='bulk_prices', on_delete=models.CASCADE)
    min_quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[MinValueValidator(MIN_AMOUNT)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.min_quantity}+ units at {self.price}"

    class Meta:
        ordering = ['min_quantity']
        unique_together = ['product', 'min_quantity']

class ProductBundle(models.Model):
    """Model for product bundles"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    products = models.ManyToManyField(Product, through='BundleItem')
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.bundle_items.all())

    @property
    def discounted_price(self):
        return self.total_price * (Decimal('1.00') - self.discount_percentage / Decimal('100.00'))

class BundleItem(models.Model):
    """Model for items in a product bundle"""
    bundle = models.ForeignKey(ProductBundle, related_name='bundle_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.bundle.name} - {self.product.name} x{self.quantity}"

    class Meta:
        unique_together = ['bundle', 'product']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.alt_text}"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} in stock"

    class Meta:
        verbose_name_plural = 'inventories'

class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
    )

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.inventory.product.name} - {self.get_movement_type_display()} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.movement_type == 'IN':
            self.inventory.quantity += self.quantity
        elif self.movement_type == 'OUT':
            self.inventory.quantity -= self.quantity
        elif self.movement_type == 'ADJ':
            self.inventory.quantity = self.quantity
        
        self.inventory.save()
        super().save(*args, **kwargs)

class ProductRecommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('similar', 'Similar Products'),
        ('frequently_bought', 'Frequently Bought Together'),
        ('personalized', 'Personalized Recommendation')
    ]

    source_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='source_recommendations'
    )
    recommended_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='target_recommendations'
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPES
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_product', 'recommended_product', 'recommendation_type')
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"{self.source_product.name} -> {self.recommended_product.name} ({self.recommendation_type})"
