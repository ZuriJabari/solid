from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mobile_payments'

router = DefaultRouter()
router.register(r'providers', views.MobilePaymentProviderViewSet, basename='provider')
router.register(r'payments', views.MobilePaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/mtn/', views.PaymentWebhookView.as_view({'post': 'mtn'}), name='webhook-mtn'),
    path('webhooks/airtel/', views.PaymentWebhookView.as_view({'post': 'airtel'}), name='webhook-airtel'),
] 