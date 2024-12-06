"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls', namespace='accounts')),
    path('api/products/', include('products.urls', namespace='products')),
    path('api/cart/', include('cart.urls', namespace='cart')),
    path('api/orders/', include('orders.urls', namespace='orders')),
    path('api/payments/', include('mobile_payments.urls', namespace='mobile_payments')),
    path('api/checkout/', include('checkout.urls', namespace='checkout')),
    path('api/analytics/', include('analytics.urls', namespace='analytics')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
