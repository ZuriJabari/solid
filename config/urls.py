"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny

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
    path('api/schema/', 
        SpectacularAPIView.as_view(
            permission_classes=[AllowAny],
            authentication_classes=[],
            serve_public=True,
            api_version='1.0.0'
        ), 
        name='schema'
    ),
    path('api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            template_name='swagger-ui.html',
            permission_classes=[AllowAny],
            authentication_classes=[],
        ),
        name='swagger-ui'
    ),
    path('api/schema/redoc/',
        SpectacularRedocView.as_view(
            url_name='schema',
            permission_classes=[AllowAny],
            authentication_classes=[],
        ),
        name='redoc'
    ),
    
    # Direct Swagger UI paths
    path('swagger-ui/', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),
    path('swagger-ui', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),
    
    # Additional API paths
    path('api/swagger-ui/', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),
    path('api/docs/', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),
    
    # Convenience redirects
    path('', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=False)),
    path('swagger/', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=False)),
    path('redoc/', RedirectView.as_view(url='/api/schema/redoc/', permanent=False)),
    path('docs/', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
