from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MobilePaymentViewSet, PaymentWebhookView

app_name = 'mobile_payments'

router = DefaultRouter()
router.register(r'payments', MobilePaymentViewSet, basename='payment')

# Get the initiate and check_status views
payment_initiate = MobilePaymentViewSet.as_view({
    'post': 'initiate'
})

payment_check_status = MobilePaymentViewSet.as_view({
    'post': 'check_status'
})

urlpatterns = [
    path('', include(router.urls)),
    path('initiate/', payment_initiate, name='initiate'),
    path('check-status/', payment_check_status, name='check-status'),
    path('webhook/<str:provider_code>/', PaymentWebhookView.as_view(), name='webhook'),
] 