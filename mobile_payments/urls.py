from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MobilePaymentViewSet, PaymentWebhookView

app_name = 'mobile_payments'

router = DefaultRouter()
router.register(r'payments', MobilePaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:provider_code>/', PaymentWebhookView.as_view(), name='webhook'),
] 