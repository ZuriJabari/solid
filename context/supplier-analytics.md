# Supplier Analytics and Inventory Forecasting Implementation

## Backend Implementation

### 1. Supplier Analytics Models (analytics/models.py)
```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class SupplierPerformance(models.Model):
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Delivery Metrics
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2)
    average_delay_days = models.DecimalField(max_digits=5, decimal_places=2)
    delivery_rejection_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Quality Metrics
    quality_rating = models.DecimalField(max_digits=5, decimal_places=2)
    defect_rate = models.DecimalField(max_digits=5, decimal_places=2)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Order Fulfillment
    fill_rate = models.DecimalField(max_digits=5, decimal_places=2)
    order_accuracy = models.DecimalField(max_digits=5, decimal_places=2)
    cancellation_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Price Performance
    price_competitiveness = models.DecimalField(max_digits=5, decimal_places=2)
    price_stability = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Additional Metrics
    response_time_avg = models.DurationField()
    communication_rating = models.DecimalField(max_digits=5, decimal_places=2)
    
    raw_metrics = JSONField()  # Stores detailed metrics data
    created_at = models.DateTimeField(auto_now_add=True)

class PriceTrend(models.Model):
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    price_date = models.DateField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume_discount_tiers = JSONField(null=True)
    notes = models.TextField(blank=True)

class ForecastModel(models.Model):
    MODEL_TYPES = [
        ('ARIMA', 'ARIMA'),
        ('PROPHET', 'Prophet'),
        ('LSTM', 'LSTM'),
        ('HYBRID', 'Hybrid')
    ]
    
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    model_type = models.CharField(max_length=10, choices=MODEL_TYPES)
    parameters = JSONField()
    accuracy_metrics = JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

class DemandForecast(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    location = models.ForeignKey('locations.Location', on_delete=models.CASCADE)
    forecast_date = models.DateField()
    predicted_demand = models.IntegerField()
    confidence_interval_lower = models.IntegerField()
    confidence_interval_upper = models.IntegerField()
    features = JSONField()  # Stores relevant features used in prediction
    model = models.ForeignKey(ForecastModel, on_delete=models.PROTECT)
```

### 2. Supplier Analytics Service (services/supplier_analytics.py)
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error
from django.db.models import Avg, Count, F, Sum

class SupplierAnalyticsService:
    @staticmethod
    def calculate_supplier_performance(supplier_id, start_date, end_date):
        """Calculate comprehensive supplier performance metrics"""
        orders = PurchaseOrder.objects.filter(
            supplier_id=supplier_id,
            created_at__range=(start_date, end_date)
        )
        
        deliveries = orders.filter(status='DELIVERED')
        
        # Calculate delivery metrics
        on_time_deliveries = deliveries.filter(
            actual_delivery_date__lte=F('expected_delivery_date')
        ).count()
        
        delivery_metrics = {
            'on_time_delivery_rate': on_time_deliveries / deliveries.count() if deliveries.count() > 0 else 0,
            'average_delay_days': deliveries.aggregate(
                avg_delay=Avg(F('actual_delivery_date') - F('expected_delivery_date'))
            )['avg_delay'].days if deliveries.exists() else 0,
            'rejection_rate': deliveries.filter(quality_check_passed=False).count() / deliveries.count() 
                if deliveries.count() > 0 else 0
        }
        
        # Calculate quality metrics
        quality_metrics = {
            'defect_rate': ProductQualityCheck.objects.filter(
                supplier_id=supplier_id,
                date__range=(start_date, end_date)
            ).aggregate(
                avg_defect_rate=Avg('defect_rate')
            )['avg_defect_rate'] or 0,
            
            'return_rate': ReturnOrder.objects.filter(
                supplier_id=supplier_id,
                created_at__range=(start_date, end_date)
            ).count() / deliveries.count() if deliveries.count() > 0 else 0
        }
        
        # Calculate price competitiveness
        price_metrics = SupplierAnalyticsService._calculate_price_metrics(
            supplier_id, start_date, end_date
        )
        
        return SupplierPerformance.objects.create(
            supplier_id=supplier_id,
            period_start=start_date,
            period_end=end_date,
            on_time_delivery_rate=delivery_metrics['on_time_delivery_rate'],
            average_delay_days=delivery_metrics['average_delay_days'],
            delivery_rejection_rate=delivery_metrics['rejection_rate'],
            defect_rate=quality_metrics['defect_rate'],
            return_rate=quality_metrics['return_rate'],
            price_competitiveness=price_metrics['competitiveness'],
            price_stability=price_metrics['stability'],
            raw_metrics={
                'delivery': delivery_metrics,
                'quality': quality_metrics,
                'price': price_metrics
            }
        )

    @staticmethod
    def _calculate_price_metrics(supplier_id, start_date, end_date):
        """Calculate price-related metrics for supplier"""
        price_trends = PriceTrend.objects.filter(
            supplier_id=supplier_id,
            price_date__range=(start_date, end_date)
        ).order_by('product_id', 'price_date')
        
        df = pd.DataFrame(price_trends.values())
        
        # Calculate price stability
        price_stability = 1 - df.groupby('product_id')['unit_price'].std().mean()
        
        # Calculate price competitiveness
        market_prices = PriceTrend.objects.filter(
            price_date__range=(start_date, end_date)
        ).values('product_id', 'price_date').annotate(
            avg_market_price=Avg('unit_price')
        )
        
        market_df = pd.DataFrame(market_prices)
        merged_df = pd.merge(df, market_df, on=['product_id', 'price_date'])
        price_competitiveness = (
            merged_df['avg_market_price'] - merged_df['unit_price']
        ).mean() / merged_df['avg_market_price'].mean()
        
        return {
            'stability': price_stability,
            'competitiveness': price_competitiveness
        }

class InventoryForecastingService:
    @staticmethod
    def train_forecast_model(product_id, location_id=None):
        """Train and save forecasting model for a product"""
        # Gather historical data
        sales_data = OrderItem.objects.filter(
            product_id=product_id,
            order__location_id=location_id if location_id else F('order__location_id')
        ).values(
            'order__created_at__date'
        ).annotate(
            quantity=Sum('quantity')
        ).order_by('order__created_at__date')
        
        df = pd.DataFrame(sales_data)
        df = df.rename(columns={
            'order__created_at__date': 'date',
            'quantity': 'demand'
        })
        
        # Add features
        df = InventoryForecastingService._add_features(df)
        
        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        
        model.fit(df)
        
        # Save model
        forecast_model = ForecastModel.objects.create(
            product_id=product_id,
            model_type='PROPHET',
            parameters=model.params,
            accuracy_metrics=InventoryForecastingService._calculate_accuracy(
                model, df
            )
        )
        
        return forecast_model

    @staticmethod
    def generate_forecast(product_id, location_id, days=30):
        """Generate demand forecast for a product"""
        model = ForecastModel.objects.get(
            product_id=product_id,
            active=True
        )
        
        # Create future dataframe
        future_dates = pd.date_range(
            start=datetime.now(),
            periods=days,
            freq='D'
        )
        
        future_df = pd.DataFrame({'ds': future_dates})
        future_df = InventoryForecastingService._add_features(future_df)
        
        # Generate forecast
        forecast = model.predict(future_df)
        
        # Save forecasts
        forecasts = []
        for _, row in forecast.iterrows():
            forecasts.append(
                DemandForecast(
                    product_id=product_id,
                    location_id=location_id,
                    forecast_date=row['ds'].date(),
                    predicted_demand=int(row['yhat']),
                    confidence_interval_lower=int(row['yhat_lower']),
                    confidence_interval_upper=int(row['yhat_upper']),
                    features={
                        'trend': row['trend'],
                        'yearly': row['yearly'],
                        'weekly': row['weekly']
                    },
                    model=model
                )
            )
        
        DemandForecast.objects.bulk_create(forecasts)
        
        return forecasts

    @staticmethod
    def optimize_stock_levels(product_id, location_id):
        """Optimize stock levels based on forecasts and constraints"""
        forecasts = DemandForecast.objects.filter(
            product_id=product_id,
            location_id=location_id,
            forecast_date__gte=datetime.now().date()
        ).order_by('forecast_date')
        
        product = Product.objects.get(id=product_id)
        
        # Calculate optimal stock level
        safety_stock = InventoryForecastingService._calculate_safety_stock(
            forecasts,
            product.lead_time,
            product.service_level
        )
        
        reorder_point = InventoryForecastingService._calculate_reorder_point(
            forecasts,
            safety_stock,
            product.lead_time
        )
        
        return {
            'safety_stock': safety_stock,
            'reorder_point': reorder_point,
            'max_stock': reorder_point * 2,  # Simple max stock calculation
            'forecasted_demand': sum(f.predicted_demand for f in forecasts),
            'confidence_interval': (
                sum(f.confidence_interval_lower for f in forecasts),
                sum(f.confidence_interval_upper for f in forecasts)
            )
        }

    @staticmethod
    def _add_features(df):
        """Add relevant features for forecasting"""
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Add holiday features
        holidays = Holiday.objects.filter(
            date__range=(df['date'].min(), df['date'].max())
        ).values_list('date', flat=True)
        
        df['is_holiday'] = df['date'].isin(holidays).astype(int)
        
        return df

    @staticmethod
    def _calculate_safety_stock(forecasts, lead_time, service_level):
        """Calculate safety stock level"""
        z_score = norm.ppf(service_level)
        
        std_dev = np.std([f.predicted_demand for f in forecasts])
        
        return int(z_score * std_dev * np.sqrt(lead_time))

    @staticmethod
    def _calculate_reorder_point(forecasts, safety_stock, lead_time):
        """Calculate reorder point"""
        avg_daily_demand = np.mean([f.predicted_demand for f in forecasts])
        
        return int(safety_stock + (avg_daily_demand * lead_time))
```

This implementation provides:

1. Supplier Analytics:
- Comprehensive performance metrics
- Quality tracking
- Price trend analysis
- Delivery performance monitoring
- Order fulfillment tracking

2. Inventory Forecasting:
- Advanced demand prediction
- Seasonal analysis
- Safety stock optimization
- Reorder point calculation
- Confidence intervals

3. Key Features:
- Machine learning-based forecasting
- Multi-location support
- Price competitiveness analysis
- Quality metrics tracking
- Automated optimization

Would you like me to implement additional features such as:
1. AI-powered supplier recommendations
2. Advanced price optimization
3. Multi-product forecasting
4. Supply chain risk analysis

Let me know which aspects you'd like to explore next!