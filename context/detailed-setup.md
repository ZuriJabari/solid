# Detailed Development Setup Guide

## Initial Development Environment Setup

### Prerequisites Installation
```bash
# 1. Install Python 3.11+
# Windows: Download from python.org
# macOS:
brew install python@3.11

# 2. Install Node.js 18+ LTS
# Windows: Download from nodejs.org
# macOS:
brew install node@18

# 3. Install PostgreSQL 15+
# Windows: Download from postgresql.org
# macOS:
brew install postgresql@15

# 4. Install Redis
# Windows: Download from redis.io
# macOS:
brew install redis
```

### Backend Project Setup

1. Create Project Structure
```bash
mkdir cbd-platform
cd cbd-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows

# Create project structure
mkdir backend
cd backend
```

2. Initialize Django Project
```bash
# Install initial dependencies
pip install django djangorestframework python-dotenv

# Start Django project
django-admin startproject config .

# Create essential apps
python manage.py startapp accounts
python manage.py startapp products
python manage.py startapp orders
python manage.py startapp locations
python manage.py startapp payments
```

3. Initial Backend Configuration (config/settings.py)
```python
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'phonenumber_field',
    
    # Local apps
    'accounts',
    'products',
    'orders',
    'locations',
    'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... other middleware
]

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
```

4. Create .env file
```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006

# Database
DB_NAME=cbd_platform
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment (Flutterwave)
FW_PUBLIC_KEY=your-public-key
FW_SECRET_KEY=your-secret-key
```

### Frontend Project Setup

1. Web Application Setup
```bash
cd ../
npx create-react-app frontend --template typescript
cd frontend

# Install essential dependencies
npm install @reduxjs/toolkit react-redux axios formik yup
npm install -D tailwindcss postcss autoprefixer
npm install @headlessui/react @heroicons/react

# Initialize Tailwind CSS
npx tailwindcss init -p
```

2. Configure Tailwind (tailwind.config.js)
```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f8f9fa',
          // ... other shades
          900: '#1a202c',
        },
      },
    },
  },
  plugins: [],
}
```

3. Mobile Application Setup
```bash
cd ../
npx create-expo-app mobile --template
cd mobile

# Install essential dependencies
npm install @react-navigation/native @react-navigation/stack
npm install @reduxjs/toolkit react-redux axios formik yup
npm install react-native-paper react-native-maps
```

## Database Schema

### Core Models

1. User Model (accounts/models.py)
```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    phone = PhoneNumberField(unique=True)
    date_of_birth = models.DateField()
    verified = models.BooleanField(default=False)
    address = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_joined']

class UserVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
```

2. Product Model (products/models.py)
```python
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    images = models.ManyToManyField('ProductImage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class ProductImage(models.Model):
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200)
```

3. Order Model (orders/models.py)
```python
from django.db import models
from django.conf import settings

class Order(models.Model):
    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    DELIVERY_TYPE = [
        ('DELIVERY', 'Home Delivery'),
        ('PICKUP', 'Store Pickup'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE)
    delivery_address = models.TextField(blank=True)
    pickup_location = models.ForeignKey('locations.PickupLocation', 
                                      on_delete=models.SET_NULL, 
                                      null=True, 
                                      blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

4. Location Model (locations/models.py)
```python
from django.contrib.gis.db import models

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    polygon = models.PolygonField()
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

class PickupLocation(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    point = models.PointField()
    contact_phone = PhoneNumberField()
    operating_hours = models.TextField()
    active = models.BooleanField(default=True)
```

## API Endpoints Specification

1. Authentication Endpoints
```python
# accounts/urls.py
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify/', VerifyAccountView.as_view()),
    path('profile/', ProfileView.as_view()),
]
```

2. Product Endpoints
```python
# products/urls.py
urlpatterns = [
    path('categories/', CategoryListView.as_view()),
    path('products/', ProductListView.as_view()),
    path('products/<slug:slug>/', ProductDetailView.as_view()),
    path('products/search/', ProductSearchView.as_view()),
]
```

3. Order Endpoints
```python
# orders/urls.py
urlpatterns = [
    path('orders/', OrderListCreateView.as_view()),
    path('orders/<str:order_number>/', OrderDetailView.as_view()),
    path('orders/<str:order_number>/track/', OrderTrackingView.as_view()),
]
```

4. Location Endpoints
```python
# locations/urls.py
urlpatterns = [
    path('zones/', DeliveryZoneListView.as_view()),
    path('pickup-locations/', PickupLocationListView.as_view()),
    path('calculate-delivery-fee/', DeliveryFeeCalculationView.as_view()),
]
```

## Mobile App Navigation Structure

```typescript
// mobile/src/navigation/types.ts
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  ProductDetails: { slug: string };
  Cart: undefined;
  Checkout: undefined;
  OrderTracking: { orderNumber: string };
};

// mobile/src/navigation/RootNavigator.tsx
const Stack = createStackNavigator<RootStackParamList>();

function RootNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Auth" component={AuthNavigator} />
      <Stack.Screen name="Main" component={MainTabNavigator} />
      <Stack.Screen name="ProductDetails" component={ProductDetailsScreen} />
      <Stack.Screen name="Cart" component={CartScreen} />
      <Stack.Screen name="Checkout" component={CheckoutScreen} />
      <Stack.Screen name="OrderTracking" component={OrderTrackingScreen} />
    </Stack.Navigator>
  );
}

// mobile/src/navigation/MainTabNavigator.tsx
const Tab = createBottomTabNavigator();

function MainTabNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Categories" component={CategoriesScreen} />
      <Tab.Screen name="Orders" component={OrdersScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
```

This setup provides a solid foundation for your CBD e-commerce platform. Would you like me to provide more details about any specific aspect or move on to implementing specific features?