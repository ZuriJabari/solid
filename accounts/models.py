from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    # Keep both id fields during transition
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    
    # Email verification
    email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    
    # Newsletter and marketing preferences
    newsletter_subscribed = models.BooleanField(_('newsletter subscribed'), default=False)
    marketing_preferences = models.JSONField(_('marketing preferences'), default=dict, blank=True)
    
    # Account status
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('date joined'), auto_now_add=True)
    updated_at = models.DateTimeField(_('last updated'), auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Address(models.Model):
    TYPE_CHOICES = [
        ('SHIPPING', 'Shipping'),
        ('BILLING', 'Billing'),
        ('BOTH', 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', to_field='id')
    address_type = models.CharField(_('address type'), max_length=20, choices=TYPE_CHOICES)
    is_default = models.BooleanField(_('default address'), default=False)
    
    # Address fields
    full_name = models.CharField(_('full name'), max_length=255)
    street_address1 = models.CharField(_('address line 1'), max_length=255)
    street_address2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100)
    phone = models.CharField(_('phone number'), max_length=20)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)

class UserPreference(models.Model):
    THEME_CHOICES = [
        ('LIGHT', 'Light'),
        ('DARK', 'Dark'),
        ('SYSTEM', 'System'),
    ]

    NOTIFICATION_CHOICES = [
        ('all', 'All Notifications'),
        ('important', 'Important Only'),
        ('none', 'None')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences', to_field='id')
    
    # UI preferences
    theme = models.CharField(_('theme preference'), max_length=20, choices=THEME_CHOICES, default='SYSTEM')
    
    # Notification preferences
    email_notifications = models.CharField(
        _('email notifications'),
        max_length=10,
        choices=NOTIFICATION_CHOICES,
        default='all'
    )
    push_notifications = models.CharField(
        _('push notifications'),
        max_length=10,
        choices=NOTIFICATION_CHOICES,
        default='all'
    )
    
    # Shopping preferences
    default_shipping_address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shipping_preference'
    )
    default_billing_address = models.ForeignKey(
        Address,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='billing_preference'
    )
    
    # Product preferences
    wishlist_items = models.ManyToManyField(
        'products.Product',
        related_name='in_wishlists',
        blank=True
    )
    saved_items = models.ManyToManyField(
        'products.Product',
        related_name='saved_by_users',
        blank=True
    )
    preferred_categories = models.ManyToManyField(
        'products.Category',
        related_name='preferred_by_users',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create UserPreference instance when a new user is created"""
    if created:
        UserPreference.objects.create(user=instance)
