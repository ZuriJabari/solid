# Shift Reports and Audit Trail Implementation

## Backend Implementation

### 1. Shift Management Models (shifts/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class Shift(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('SUSPENDED', 'Suspended')
    ]

    cashier = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    store = models.ForeignKey('stores.Store', on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    actual_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cash_discrepancy = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    performance_metrics = JSONField(default=dict)
    notes = models.TextField(blank=True)

class ShiftTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('REFUND', 'Refund'),
        ('VOID', 'Void'),
        ('PAYOUT', 'Payout'),
        ('CASHDROP', 'Cash Drop')
    ]

    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

class ShiftDiscrepancy(models.Model):
    DISCREPANCY_TYPES = [
        ('CASH_OVER', 'Cash Over'),
        ('CASH_SHORT', 'Cash Short'),
        ('VOID_ANOMALY', 'Void Anomaly'),
        ('REFUND_ANOMALY', 'Refund Anomaly')
    ]

    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    discrepancy_type = models.CharField(max_length=15, choices=DISCREPANCY_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)
    resolution_notes = models.TextField(blank=True)

### 2. Audit Trail Models (audit/models.py)
```python
class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('OTHER', 'Other')
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=50)  # e.g., 'Product', 'Order'
    entity_id = models.CharField(max_length=50)
    action_details = JSONField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    store = models.ForeignKey('stores.Store', on_delete=models.PROTECT)

class SystemAudit(models.Model):
    SEVERITY_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical')
    ]

    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    description = models.TextField()
    details = JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)

class ComplianceLog(models.Model):
    category = models.CharField(max_length=50)
    action = models.TextField()
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_data = JSONField()
    verification_status = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
```

### 3. Shift Report Service (services/shift_service.py)
```python
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncHour

class ShiftReportService:
    @staticmethod
    def generate_shift_report(shift_id):
        """Generate comprehensive shift report"""
        shift = Shift.objects.select_related('cashier', 'store').get(id=shift_id)
        transactions = ShiftTransaction.objects.filter(shift=shift)

        # Calculate performance metrics
        hourly_sales = transactions.filter(
            transaction_type='SALE'
        ).annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('hour')

        payment_breakdown = transactions.filter(
            transaction_type='SALE'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

        discrepancies = ShiftDiscrepancy.objects.filter(shift=shift)

        return {
            'shift_info': {
                'cashier': shift.cashier.get_full_name(),
                'store': shift.store.name,
                'start_time': shift.start_time,
                'end_time': shift.end_time,
                'duration': (shift.end_time - shift.start_time).total_seconds() / 3600
            },
            'financial_summary': {
                'total_sales': shift.total_sales,
                'transaction_count': shift.total_transactions,
                'average_transaction': shift.total_sales / shift.total_transactions if shift.total_transactions > 0 else 0,
                'cash_discrepancy': shift.cash_discrepancy
            },
            'hourly_breakdown': list(hourly_sales),
            'payment_methods': list(payment_breakdown),
            'discrepancies': [{
                'type': d.discrepancy_type,
                'amount': d.amount,
                'resolved': bool(d.resolved_at)
            } for d in discrepancies],
            'performance_metrics': {
                'sales_per_hour': shift.total_sales / shift.duration if shift.duration > 0 else 0,
                'transactions_per_hour': shift.total_transactions / shift.duration if shift.duration > 0 else 0,
                'average_speed': shift.performance_metrics.get('average_transaction_time', 0)
            }
        }

    @staticmethod
    def detect_anomalies(shift_id):
        """Detect anomalies in shift transactions"""
        shift = Shift.objects.get(id=shift_id)
        transactions = ShiftTransaction.objects.filter(shift=shift)

        anomalies = []

        # Check for unusual void patterns
        void_transactions = transactions.filter(transaction_type='VOID')
        if void_transactions.count() > 5:  # Threshold for voids
            anomalies.append({
                'type': 'HIGH_VOID_COUNT',
                'details': f"{void_transactions.count()} void transactions detected"
            })

        # Check for large transactions
        avg_transaction = transactions.filter(
            transaction_type='SALE'
        ).aggregate(avg=Avg('amount'))['avg'] or 0

        large_transactions = transactions.filter(
            transaction_type='SALE',
            amount__gt=avg_transaction * 3  # Threshold for large transactions
        )
        
        if large_transactions.exists():
            anomalies.append({
                'type': 'LARGE_TRANSACTIONS',
                'details': f"{large_transactions.count()} unusually large transactions"
            })

        return anomalies

class AuditService:
    @staticmethod
    def log_action(user, action_type, entity_type, entity_id, action_details, request):
        """Log user action for audit trail"""
        return AuditLog.objects.create(
            user=user,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_details=action_details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            store=user.active_store
        )

    @staticmethod
    def log_compliance_action(user, category, action, related_data):
        """Log compliance-related actions"""
        return ComplianceLog.objects.create(
            category=category,
            action=action,
            user=user,
            related_data=related_data
        )

    @staticmethod
    def analyze_user_activity(user_id, timeframe=30):
        """Analyze user activity for suspicious patterns"""
        start_date = timezone.now() - timedelta(days=timeframe)
        user_logs = AuditLog.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date
        )

        patterns = {
            'login_attempts': user_logs.filter(
                action_type='LOGIN'
            ).count(),
            'after_hours_activity': user_logs.filter(
                timestamp__hour__gte=20
            ).count(),
            'high_risk_actions': user_logs.filter(
                action_type__in=['DELETE', 'UPDATE']
            ).count(),
            'data_exports': user_logs.filter(
                action_type='EXPORT'
            ).count()
        }

        return patterns
```

### 4. Audit Report Service (services/audit_service.py)
```python
class AuditReportService:
    @staticmethod
    def generate_audit_report(start_date, end_date, store_id=None):
        """Generate comprehensive audit report"""
        audit_logs = AuditLog.objects.filter(
            timestamp__range=(start_date, end_date)
        )

        if store_id:
            audit_logs = audit_logs.filter(store_id=store_id)

        compliance_logs = ComplianceLog.objects.filter(
            timestamp__range=(start_date, end_date)
        )

        report = {
            'summary': {
                'total_actions': audit_logs.count(),
                'unique_users': audit_logs.values('user').distinct().count(),
                'high_risk_actions': audit_logs.filter(
                    action_type__in=['DELETE', 'UPDATE']
                ).count(),
                'compliance_actions': compliance_logs.count()
            },
            'user_activity': audit_logs.values(
                'user__username'
            ).annotate(
                action_count=Count('id'),
                last_action=Max('timestamp')
            ),
            'action_breakdown': audit_logs.values(
                'action_type'
            ).annotate(
                count=Count('id')
            ),
            'compliance_summary': compliance_logs.values(
                'category'
            ).annotate(
                action_count=Count('id'),
                verification_rate=Sum(
                    Case(
                        When(verification_status=True, then=1),
                        default=0,
                        output_field=FloatField(),
                    )
                ) * 100.0 / Count('id')
            ),
            'anomalies': SystemAudit.objects.filter(
                timestamp__range=(start_date, end_date),
                severity__in=['WARNING', 'ERROR', 'CRITICAL']
            ).values('event_type', 'severity', 'description')
        }

        return report
```

This implementation provides:

1. Shift Reports:
- Detailed transaction tracking
- Performance metrics
- Cash handling analysis
- Anomaly detection
- Payment method breakdown

2. Audit Trails:
- Comprehensive action logging
- User activity tracking
- Compliance monitoring
- Anomaly detection
- Security reporting

3. Key Features:
- Real-time anomaly detection
- Performance analytics
- Compliance tracking
- Security monitoring
- Cash discrepancy tracking

Would you like me to implement additional features such as:
1. Advanced anomaly detection algorithms
2. Real-time alert system
3. Automated compliance reporting
4. Advanced cashier performance analytics

Let me know which aspects you'd like to explore next!