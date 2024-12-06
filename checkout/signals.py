from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import CheckoutSession
from orders.models import Order, OrderItem

@receiver(post_save, sender=CheckoutSession)
def handle_checkout_session_status(sender, instance, created, **kwargs):
    """Handle checkout session status changes"""
    if not created and instance.status == 'COMPLETED':
        # Create order from checkout session
        order = Order.objects.create(
            user=instance.user,
            order_number=f"ORD-{instance.id}",
            status='PENDING',
            delivery_type=instance.delivery_type,
            delivery_address=instance.delivery_address,
            delivery_instructions=instance.delivery_instructions,
            delivery_zone=instance.delivery_zone,
            pickup_location=instance.pickup_location,
            subtotal=instance.subtotal,
            delivery_fee=instance.delivery_fee,
            total=instance.total,
            payment_method=instance.payment_method.provider,
            payment_status='PENDING'
        )

        # Create order items from cart items
        for cart_item in instance.cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                total=cart_item.subtotal
            )

        # Clear the cart
        instance.cart.items.all().delete()

@receiver(pre_save, sender=CheckoutSession)
def handle_session_expiry(sender, instance, **kwargs):
    """Handle session expiry"""
    if instance.expires_at and instance.expires_at < timezone.now():
        instance.status = 'EXPIRED' 