from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mobile_payments.models import MobilePayment
from mobile_payments.services import MobilePaymentService

class Command(BaseCommand):
    help = 'Check status of pending mobile money payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Check payments initiated in the last X minutes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be done without making actual API calls'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        dry_run = options['dry_run']
        
        # Get payments initiated in the last X minutes
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        pending_payments = MobilePayment.objects.filter(
            status__in=['PENDING', 'PROCESSING'],
            created_at__gt=cutoff_time
        ).select_related('provider', 'user', 'order')
        
        self.stdout.write(f"Found {pending_payments.count()} payments to check...")
        
        if dry_run:
            self.stdout.write("DRY RUN - No API calls will be made")
        
        for payment in pending_payments:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would check status for payment {payment.id} "
                        f"(Order #{payment.order.id}, User: {payment.user.email})"
                    )
                else:
                    service = MobilePaymentService(payment.provider)
                    status_info = service.check_payment_status(payment)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Payment {payment.id} status: {status_info['status']} "
                            f"(Order #{payment.order.id}, User: {payment.user.email})"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to check status for payment {payment.id}: {str(e)}"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS("Status check complete")) 