from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mobile_payments.models import MobilePayment
from mobile_payments.services import MobilePaymentService

class Command(BaseCommand):
    help = 'Cancel stale mobile money payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Cancel payments pending for more than X hours'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be done without making actual changes'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Get stale payments
        cutoff_time = timezone.now() - timedelta(hours=hours)
        stale_payments = MobilePayment.objects.filter(
            status__in=['PENDING', 'PROCESSING'],
            created_at__lt=cutoff_time
        ).select_related('provider', 'user', 'order')
        
        self.stdout.write(f"Found {stale_payments.count()} stale payments...")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
        
        for payment in stale_payments:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would cancel payment {payment.id} "
                        f"(Order #{payment.order.id}, User: {payment.user.email})"
                    )
                else:
                    # Update payment status
                    payment.status = 'CANCELLED'
                    payment.save()
                    
                    # Send notification
                    service = MobilePaymentService(payment.provider)
                    service.send_payment_status_notification(payment)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Cancelled payment {payment.id} "
                            f"(Order #{payment.order.id}, User: {payment.user.email})"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to cancel payment {payment.id}: {str(e)}"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS("Payment cancellation complete")) 