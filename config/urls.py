"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

schema_view = get_schema_view(
    openapi.Info(
        title="Urban Herb API",
        default_version='v1',
        description="API documentation for Urban Herb",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@urbanherb.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Custom logout view that accepts both GET and POST
class CustomLogoutView(auth_views.LogoutView):
    http_method_names = ['get', 'post']

urlpatterns = [
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('redoc', cache_timeout=0), name='api-docs'),

    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('auth/login/', auth_views.LoginView.as_view(template_name='rest_framework/login.html'), name='login'),
    path('auth/logout/', CustomLogoutView.as_view(
        next_page='schema-swagger-ui',
        template_name='rest_framework/logout.html'
    ), name='logout'),
    path('auth/', include('rest_framework.urls')),

    # Products
    path('api/', include('products.urls')),

    # Cart
    path('api/cart/', include('cart.urls')),

    # Orders
    path('api/orders/', include('orders.urls')),

    # User Management
    path('api/accounts/', include('accounts.urls')),

    # Mobile Payments
    path('api/mobile-payments/', include('mobile_payments.urls')),

    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
