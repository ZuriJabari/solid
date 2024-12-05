"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.views.generic import RedirectView

schema_view = get_schema_view(
   openapi.Info(
      title="Urban Herb API",
      default_version='v1',
      description="API documentation for Urban Herb CBD E-commerce",
      terms_of_service="https://www.urbanherb.com/terms/",
      contact=openapi.Contact(email="contact@urbanherb.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# API Documentation patterns
docs_patterns = [
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns = [
    # API Documentation (before other patterns)
    *docs_patterns,
    
    # Root URL redirects to ReDoc
    path('', schema_view.with_ui('redoc', cache_timeout=0), name='api-docs'),
    
    # Admin and API URLs
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
    
    # Authentication URLs
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
