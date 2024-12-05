# Real-time Alert System and Anomaly Detection Implementation

## Backend Implementation

### 1. Alert System Models (alerts/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class AlertConfiguration(models.Model):
    ALERT_TYPES = [
        ('TRANSACTION', 'Transaction Alert'),
        ('INVENTORY', 'Inventory Alert'),
        ('SECURITY', 'Security Alert'),
        ('SYSTEM', 'System Alert'),
        ('COMPLIANCE', 'Compliance Alert')
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]

    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    conditions = JSONField()  # Stores alert trigger conditions
    notification_channels = JSONField()  # Stores notification preferences
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class Alert(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive')
    ]

    configuration = models.ForeignKey(AlertConfiguration, on_delete=models.PROTECT)
    message = models.TextField()
    details = JSONField()
    source_type = models.CharField(max_length=50)
    source_id = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(
        'accounts.User',
        null=True,
        related_name='acknowledged_alerts',
        on_delete=models.SET_NULL
    )
    acknowledged_at = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey(
        'accounts.User',
        null=True,
        related_name='resolved_alerts',
        on_delete=models.SET_NULL
    )
    resolved_at = models.DateTimeField(null=True)
    resolution_notes = models.TextField(blank=True)

class AlertResponse(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    action_taken = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    response_time = models.DurationField()  # Time taken to respond

### 2. Anomaly Detection Models (anomaly/models.py)
```python
class AnomalyModel(models.Model):
    MODEL_TYPES = [
        ('ISOLATION_FOREST', 'Isolation Forest'),
        ('LOCAL_OUTLIER', 'Local Outlier Factor'),
        ('AUTOENCODER', 'Autoencoder'),
        ('STATISTICAL', 'Statistical Analysis')
    ]

    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    parameters = JSONField()  # Stores model parameters
    feature_config = JSONField()  # Stores feature configuration
    performance_metrics = JSONField()
    last_trained = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20)

class AnomalyDetection(models.Model):
    model = models.ForeignKey(AnomalyModel, on_delete=models.PROTECT)
    source_type = models.CharField(max_length=50)
    source_id = models.CharField(max_length=50)
    features = JSONField()  # Input features
    anomaly_score = models.FloatField()
    is_anomaly = models.BooleanField()
    details = JSONField()  # Detailed analysis results
    created_at = models.DateTimeField(auto_now_add=True)

### 3. Alert Service (services/alert_service.py)
```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class AlertService:
    @staticmethod
    async def trigger_alert(alert_type, source_type, source_id, details):
        """Trigger a new alert based on configured conditions"""
        # Get relevant alert configurations
        configs = AlertConfiguration.objects.filter(
            alert_type=alert_type,
            enabled=True
        )

        for config in configs:
            if AlertService._check_conditions(config.conditions, details):
                # Create alert
                alert = Alert.objects.create(
                    configuration=config,
                    message=AlertService._generate_message(config, details),
                    details=details,
                    source_type=source_type,
                    source_id=source_id
                )

                # Send real-time notifications
                await AlertService._send_notifications(alert)

                # Trigger automated responses based on severity
                if config.severity in ['HIGH', 'CRITICAL']:
                    await AlertService._trigger_automated_response(alert)

    @staticmethod
    def _check_conditions(conditions, details):
        """Check if alert conditions are met"""
        for condition in conditions:
            operator = condition.get('operator')
            field = condition.get('field')
            value = condition.get('value')
            
            if field not in details:
                continue

            actual_value = details[field]
            
            if operator == 'gt' and not actual_value > value:
                return False
            elif operator == 'lt' and not actual_value < value:
                return False
            elif operator == 'eq' and not actual_value == value:
                return False
            elif operator == 'contains' and value not in actual_value:
                return False

        return True

    @staticmethod
    async def _send_notifications(alert):
        """Send notifications through configured channels"""
        channel_layer = get_channel_layer()
        
        # Send WebSocket notification
        await channel_layer.group_send(
            "alerts",
            {
                "type": "alert.notification",
                "alert": {
                    "id": alert.id,
                    "message": alert.message,
                    "severity": alert.configuration.severity,
                    "created_at": alert.created_at.isoformat()
                }
            }
        )

        # Send other notifications based on configuration
        for channel in alert.configuration.notification_channels:
            if channel == 'EMAIL':
                await AlertService._send_email_notification(alert)
            elif channel == 'SMS':
                await AlertService._send_sms_notification(alert)
            elif channel == 'SLACK':
                await AlertService._send_slack_notification(alert)

class AnomalyDetectionService:
    @staticmethod
    def train_models():
        """Train or update anomaly detection models"""
        for model_config in AnomalyModel.objects.filter(is_active=True):
            if model_config.model_type == 'ISOLATION_FOREST':
                AnomalyDetectionService._train_isolation_forest(model_config)
            elif model_config.model_type == 'LOCAL_OUTLIER':
                AnomalyDetectionService._train_lof(model_config)
            elif model_config.model_type == 'AUTOENCODER':
                AnomalyDetectionService._train_autoencoder(model_config)

    @staticmethod
    def detect_anomalies(source_type, source_id, data):
        """Detect anomalies in new data"""
        models = AnomalyModel.objects.filter(is_active=True)
        results = []

        for model in models:
            # Prepare features
            features = AnomalyDetectionService._prepare_features(
                data,
                model.feature_config
            )

            # Get predictions
            anomaly_score = AnomalyDetectionService._get_predictions(
                model,
                features
            )

            # Determine if anomaly based on threshold
            is_anomaly = anomaly_score > model.parameters.get('threshold', 0.8)

            # Save detection result
            detection = AnomalyDetection.objects.create(
                model=model,
                source_type=source_type,
                source_id=source_id,
                features=features,
                anomaly_score=anomaly_score,
                is_anomaly=is_anomaly,
                details={
                    'score': anomaly_score,
                    'threshold': model.parameters.get('threshold', 0.8),
                    'feature_importance': AnomalyDetectionService._get_feature_importance(
                        model,
                        features
                    )
                }
            )

            results.append(detection)

            # Trigger alert if anomaly detected
            if is_anomaly:
                AlertService.trigger_alert(
                    'SECURITY',
                    source_type,
                    source_id,
                    {
                        'anomaly_score': anomaly_score,
                        'model_name': model.name,
                        'features': features
                    }
                )

        return results

    @staticmethod
    def _train_isolation_forest(model_config):
        """Train Isolation Forest model"""
        from sklearn.ensemble import IsolationForest
        
        # Get historical data
        data = AnomalyDetectionService._get_training_data(
            model_config.feature_config
        )
        
        # Train model
        model = IsolationForest(
            **model_config.parameters.get('model_params', {})
        )
        
        model.fit(data)
        
        # Save model
        AnomalyDetectionService._save_model(model, model_config)

    @staticmethod
    def _get_predictions(model_config, features):
        """Get anomaly predictions from model"""
        # Load model
        model = AnomalyDetectionService._load_model(model_config)
        
        if model_config.model_type == 'ISOLATION_FOREST':
            # Convert prediction to score between 0 and 1
            score = -model.score_samples([features])[0]
            return (score - model_config.parameters['min_score']) / (
                model_config.parameters['max_score'] - model_config.parameters['min_score']
            )
        
        elif model_config.model_type == 'AUTOENCODER':
            reconstruction_error = model.predict([features])[0]
            return reconstruction_error

        return 0.0

    @staticmethod
    def _get_feature_importance(model_config, features):
        """Calculate feature importance for anomaly detection"""
        if model_config.model_type == 'ISOLATION_FOREST':
            base_score = AnomalyDetectionService._get_predictions(
                model_config,
                features
            )
            
            importance = {}
            for feature in features:
                # Modify each feature and get new prediction
                modified_features = features.copy()
                modified_features[feature] = 0  # Or use mean value
                
                new_score = AnomalyDetectionService._get_predictions(
                    model_config,
                    modified_features
                )
                
                importance[feature] = abs(new_score - base_score)
            
            return importance
        
        return {}

    @staticmethod
    def calculate_risk_score(anomalies):
        """Calculate overall risk score based on detected anomalies"""
        if not anomalies:
            return 0.0

        # Weight anomalies by model confidence and severity
        weighted_scores = []
        for anomaly in anomalies:
            model_weight = anomaly.model.parameters.get('model_weight', 1.0)
            severity_weight = {
                'LOW': 0.25,
                'MEDIUM': 0.5,
                'HIGH': 0.75,
                'CRITICAL': 1.0
            }.get(anomaly.model.parameters.get('severity', 'MEDIUM'), 0.5)

            weighted_scores.append(
                anomaly.anomaly_score * model_weight * severity_weight
            )

        return sum(weighted_scores) / len(weighted_scores)
```

This implementation provides:

1. Real-time Alert System:
- Configurable alert conditions
- Multi-channel notifications (WebSocket, Email, SMS, Slack)
- Alert prioritization based on severity
- Response tracking and metrics
- Automated responses for high-severity alerts

2. Anomaly Detection:
- Multiple detection algorithms
- Feature importance analysis
- Risk scoring
- Historical pattern analysis
- Model performance tracking

3. Key Features:
- Real-time WebSocket notifications
- Customizable thresholds
- Automated responses
- Response time tracking
- Detailed anomaly analysis

Would you like me to implement additional features such as:
1. Advanced visualization dashboards
2. Mobile push notifications
3. Machine learning model optimization
4. Integration with external security systems

Let me know which aspects you'd like to explore next!