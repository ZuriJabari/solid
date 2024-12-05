from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

router = DefaultRouter()
router.register(r'delivery-zones', views.DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'notes', views.OrderNoteViewSet, basename='order-note')

urlpatterns = [
    path('', include(router.urls)),
] 