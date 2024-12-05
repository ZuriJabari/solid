from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

# Create a router for viewsets
router = DefaultRouter()
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
router.register(r'batches', views.InventoryBatchViewSet, basename='batch')
router.register(r'adjustments', views.StockAdjustmentViewSet, basename='adjustment')

urlpatterns = [
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/tree/', views.CategoryTreeView.as_view(), name='category-tree'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Review URLs
    path('products/<slug:slug>/reviews/', views.ProductReviewCreateView.as_view(), name='product-review-create'),
    path('reviews/<int:id>/', views.ProductReviewUpdateView.as_view(), name='product-review-update'),
    path('reviews/<int:id>/delete/', views.ProductReviewDeleteView.as_view(), name='product-review-delete'),
    path('reviews/<int:review_id>/vote/', views.ReviewVoteView.as_view(), name='review-vote'),
    path('reviews/moderate/<int:pk>/', views.ReviewModerationView.as_view(), name='review-moderate'),

    # Include router URLs for inventory management
    path('', include(router.urls)),
] 