from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AddressViewSet, UserPreferenceViewSet,
    RegisterView, LoginView, LogoutView
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'preferences', UserPreferenceViewSet, basename='preference')

# Custom preference actions
preference_detail = UserPreferenceViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'put': 'update'
})

preference_wishlist = UserPreferenceViewSet.as_view({
    'post': 'add_to_wishlist'
})

preference_remove_wishlist = UserPreferenceViewSet.as_view({
    'post': 'remove_from_wishlist'
})

preference_saved = UserPreferenceViewSet.as_view({
    'post': 'add_to_saved'
})

preference_remove_saved = UserPreferenceViewSet.as_view({
    'post': 'remove_from_saved'
})

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Custom preference endpoints
    path('preferences/<uuid:pk>/', preference_detail, name='preference-detail'),
    path('preferences/<uuid:pk>/add-to-wishlist/', preference_wishlist, name='preference-add-to-wishlist'),
    path('preferences/<uuid:pk>/remove-from-wishlist/', preference_remove_wishlist, name='preference-remove-from-wishlist'),
    path('preferences/<uuid:pk>/add-to-saved/', preference_saved, name='preference-add-to-saved'),
    path('preferences/<uuid:pk>/remove-from-saved/', preference_remove_saved, name='preference-remove-from-saved'),
] 