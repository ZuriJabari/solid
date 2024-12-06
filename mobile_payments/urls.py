from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MobilePaymentViewSet

app_name = 'mobile_payments'

router = DefaultRouter()
router.register(r'', MobilePaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
] 