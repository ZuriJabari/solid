from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeliveryZoneViewSet, PickupLocationViewSet,
    PaymentMethodViewSet, CheckoutSessionViewSet
)

app_name = 'checkout'

router = DefaultRouter()
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'pickup-locations', PickupLocationViewSet, basename='pickup-location')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'sessions', CheckoutSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
] 