from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mobile_payments.models import MobilePayment
from mobile_payments.services import MobilePaymentService

class Command(BaseCommand):
    help = 'Send reminders for pending mobile money payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Send reminders for payments pending for more than X hours'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be done without sending actual reminders'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Get pending payments older than specified hours
        cutoff_time = timezone.now() - timedelta(hours=hours)
        pending_payments = MobilePayment.objects.filter(
            status__in=['PENDING', 'PROCESSING'],
            created_at__lt=cutoff_time
        ).select_related('provider', 'user', 'order')
        
        self.stdout.write(f"Found {pending_payments.count()} pending payments...")
        
        if dry_run:
            self.stdout.write("DRY RUN - No reminders will be sent")
        
        for payment in pending_payments:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would send reminder for payment {payment.id} "
                        f"(Order #{payment.order.id}, User: {payment.user.email})"
                    )
                else:
                    service = MobilePaymentService(payment.provider)
                    service.send_payment_reminder(payment)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent reminder for payment {payment.id} "
                            f"(Order #{payment.order.id}, User: {payment.user.email})"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send reminder for payment {payment.id}: {str(e)}"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS("Reminder processing complete")) 