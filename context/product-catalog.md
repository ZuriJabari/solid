# Product Catalog Implementation

## Backend Implementation

### 1. Enhanced Product Models (products/models.py)
```python
from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    POTENCY_CHOICES = [
        ('LOW', 'Low (< 10mg)'),
        ('MEDIUM', 'Medium (10-20mg)'),
        ('HIGH', 'High (> 20mg)'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField()
    potency = models.CharField(max_length=10, choices=POTENCY_CHOICES)
    ingredients = models.TextField()
    usage_instructions = models.TextField()
    warnings = models.TextField()
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text='Weight in grams')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'category', 'is_active']),
            models.Index(fields=['price', 'sale_price']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
```

### 2. Serializers (products/serializers.py)
```python
from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'description', 'parent')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'order')

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ('id', 'rating', 'comment', 'created_at', 'user_name')

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name')
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'short_description', 'price',
            'sale_price', 'primary_image', 'category_name',
            'potency', 'average_rating', 'is_featured'
        )

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    category = CategorySerializer()
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
```

### 3. Views (products/views.py)
```python
from rest_framework import generics, filters
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductReview
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductReviewSerializer
)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = []

class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = []
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'potency', 'is_featured']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']

    def get_queryset(self):
        return Product.objects.filter(is_active=True).annotate(
            average_rating=Avg('reviews__rating')
        ).select_related('category')

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = []

    def get_queryset(self):
        return Product.objects.annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).select_related('category').prefetch_related('images', 'reviews')

class ProductReviewCreateView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs['slug'])
        serializer.save(user=self.request.user, product=product)
```

## Frontend Implementation (Web)

### 1. Product Components (src/components/products)

```typescript
// ProductCard.tsx
import React from 'react';
import { Link } from 'react-router-dom';

interface ProductCardProps {
  product: {
    slug: string;
    name: string;
    primary_image: string;
    price: number;
    sale_price: number | null;
    short_description: string;
    potency: string;
    average_rating: number;
  };
}

const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  return (
    <div className="group relative">
      <Link to={`/products/${product.slug}`} className="block">
        <div className="aspect-w-1 aspect-h-1 rounded-lg overflow-hidden">
          <img
            src={product.primary_image}
            alt={product.name}
            className="w-full h-full object-cover object-center group-hover:opacity-75"
          />
          {product.sale_price && (
            <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded">
              Sale
            </div>
          )}
        </div>
        <div className="mt-4 space-y-2">
          <h3 className="text-sm font-medium text-gray-900">{product.name}</h3>
          <p className="text-sm text-gray-500">{product.short_description}</p>
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              {product.sale_price ? (
                <>
                  <span className="text-lg font-medium text-red-600">
                    ${product.sale_price}
                  </span>
                  <span className="text-sm text-gray-500 line-through">
                    ${product.price}
                  </span>
                </>
              ) : (
                <span className="text-lg font-medium text-gray-900">
                  ${product.price}
                </span>
              )}
            </div>
            <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              {product.potency}
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <StarIcon
                  key={i}
                  className={`h-4 w-4 ${
                    i < Math.round(product.average_rating)
                      ? 'text-yellow-400'
                      : 'text-gray-200'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
};

// ProductGrid.tsx
const ProductGrid: React.FC<{ products: Product[] }> = ({ products }) => {
  return (
    <div className="grid grid-cols-1 gap-y-10 sm:grid-cols-2 gap-x-6 lg:grid-cols-3 xl:grid-cols-4 xl:gap-x-8">
      {products.map((product) => (
        <ProductCard key={product.slug} product={product} />
      ))}
    </div>
  );
};

// ProductFilters.tsx
const ProductFilters: React.FC<{
  categories: Category[];
  selectedCategory: string | null;
  onCategoryChange: (category: string | null) => void;
  potency: string | null;
  onPotencyChange: (potency: string | null) => void;
}> = ({
  categories,
  selectedCategory,
  onCategoryChange,
  potency,
  onPotencyChange,
}) => {
  return (
    <div className="hidden lg:block">
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-medium text-gray-900">Categories</h3>
        <ul className="mt-4 space-y-4">
          {categories.map((category) => (
            <li key={category.slug}>
              <button
                onClick={() => onCategoryChange(category.slug)}
                className={`text-sm ${
                  selectedCategory === category.slug
                    ? 'text-indigo-600 font-medium'
                    : 'text-gray-600'
                }`}
              >
                {category.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="border-b border-gray-200 py-6">
        <h3 className="text-lg font-medium text-gray-900">Potency</h3>
        <ul className="mt-4 space-y-4">
          {['LOW', 'MEDIUM', 'HIGH'].map((level) => (
            <li key={level}>
              <button
                onClick={() => onPotencyChange(level)}
                className={`text-sm ${
                  potency === level
                    ? 'text-indigo-600 font-medium'
                    : 'text-gray-600'
                }`}
              >
                {level.charAt(0) + level.slice(1).toLowerCase()}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

### 2. Product Pages (src/pages)

```typescript
// ProductListPage.tsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ProductGrid, ProductFilters, ProductSearch } from '../components/products';
import { fetchProducts, fetchCategories } from '../services/api';

const ProductListPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const category = searchParams.get('category');
  const potency = searchParams.get('potency');
  const search = searchParams.get('search');

  const { data: products, isLoading: productsLoading } = useQuery(
    ['products', { category, potency, search }],
    () => fetchProducts({ category, potency, search })
  );

  const { data: categories } = useQuery(['categories'], fetchCategories);

  const handleSearch = (value: string) => {
    setSearchParams({ ...Object.fromEntries(searchParams), search: value });
  };

  if (productsLoading) return <LoadingSpinner />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="pt-24 pb-10">
        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
          CBD Products
        </h1>
      </div>

      <div className="flex gap-8">
        <ProductFilters
          categories={categories || []}
          selectedCategory={category}
          onCategoryChange={(value) =>
            setSearchParams({ ...Object.fromEntries(searchParams), category: value })
          }
          potency={potency}
          onPotencyChange={(value) =>
            set