# CBD E-commerce Platform Project Context

## Project Overview
Building a comprehensive CBD e-commerce platform serving Kampala, Entebbe, and Mukono regions, with both web and mobile applications. The platform will handle product listings, user management, order processing, delivery tracking, and pickup management.

## Tech Stack

### Backend (Python/Django)
- Python 3.11+
- Django 5.0+
- Django REST Framework 3.14+
- PostgreSQL 15+
- Redis (for caching and async tasks)
- Celery (background tasks)

#### Key Backend Packages
```txt
django-cors-headers==4.3.1
django-redis==5.4.0
django-filter==23.5
dj-rest-auth==5.0.2
djangorestframework-simplejwt==5.3.1
Pillow==10.1.0
psycopg2-binary==2.9.9
celery==5.3.6
django-celery-beat==2.5.0
python-dotenv==1.0.0
stripe==7.11.0
flutterwave-python==1.0.8
```

### Frontend (React/React Native)
- React 18+
- React Native 0.73+ (for mobile apps)
- TypeScript 5+
- Redux Toolkit for state management
- React Query for API data fetching
- Tailwind CSS (web)
- Native Base (mobile)

#### Key Frontend Packages
```json
{
  "dependencies": {
    "@reduxjs/toolkit": "^2.0.1",
    "@tanstack/react-query": "^5.17.1",
    "axios": "^1.6.3",
    "formik": "^2.4.5",
    "react-router-dom": "^6.21.1",
    "tailwindcss": "^3.4.0",
    "yup": "^1.3.3",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "native-base": "^3.4.28"
  }
}
```

## Project Structure

### Backend Structure
```
backend/
├── config/                 # Project settings
├── apps/
│   ├── accounts/          # User management
│   ├── products/          # Product management
│   ├── orders/            # Order processing
│   ├── delivery/          # Delivery management
│   ├── locations/         # Pickup locations
│   └── analytics/         # Business analytics
├── utils/                 # Helper functions
├── tests/                 # Test suite
└── requirements/
    ├── base.txt
    ├── local.txt
    └── production.txt
```

### Frontend Structure
```
frontend/
├── src/
│   ├── api/              # API integration
│   ├── components/       # Reusable components
│   ├── features/         # Feature modules
│   ├── hooks/           # Custom hooks
│   ├── layouts/         # Page layouts
│   ├── pages/           # Route pages
│   ├── store/           # Redux store
│   ├── styles/          # Global styles
│   └── utils/           # Helper functions
└── mobile/              # React Native app
    ├── src/
    │   ├── navigation/  # Navigation setup
    │   ├── screens/     # Mobile screens
    │   └── components/  # Mobile components
    └── android/         # Android specific
    └── ios/            # iOS specific
```

## Key Features Implementation

### Authentication System
```python
# Backend: apps/accounts/models.py
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField()
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_joined']
```

### Product Management
```python
# Backend: apps/products/models.py
class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    thc_content = models.DecimalField(max_digits=5, decimal_places=2)
    cbd_content = models.DecimalField(max_digits=5, decimal_places=2)
```

### Order Processing
```python
# Backend: apps/orders/models.py
class Order(models.Model):
    ORDER_STATUSES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=ORDER_STATUSES)
    delivery_type = models.CharField(max_length=10, choices=[('delivery', 'Delivery'), ('pickup', 'Pickup')])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
```

## API Endpoints Structure

### Authentication Endpoints
```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/verify-age/
POST /api/auth/refresh-token/
```

### Product Endpoints
```
GET /api/products/
GET /api/products/{id}/
GET /api/products/categories/
POST /api/products/search/
```

### Order Endpoints
```
POST /api/orders/create/
GET /api/orders/user/{user_id}/
PATCH /api/orders/{id}/status/
GET /api/orders/{id}/tracking/
```

## Environment Setup

### Backend Environment Variables
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
GOOGLE_MAPS_API_KEY=your-maps-key
FLUTTERWAVE_PUBLIC_KEY=your-flutterwave-key
FLUTTERWAVE_SECRET_KEY=your-flutterwave-secret
```

### Frontend Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_GOOGLE_MAPS_KEY=your-maps-key
REACT_APP_FLUTTERWAVE_PUBLIC_KEY=your-flutterwave-key
```

## Development Setup Instructions

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements/local.txt

# Setup database
python manage.py migrate

# Run development server
python manage.py runserver
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# For mobile development
cd mobile
npm install
npx pod-install  # iOS only
```

## Mobile Development Approach
For mobile development, React Native is recommended over a pure native approach for several reasons:
1. Code sharing between web and mobile
2. Faster development cycle
3. Easier maintenance
4. Single team can handle both platforms

However, certain features will require native modules:
- Location services
- Push notifications
- Payment processing
- Camera access (for age verification)

## Deployment Considerations

### Backend Deployment
- Use Docker containers
- Configure NGINX as reverse proxy
- Set up SSL certificates
- Configure PostgreSQL with proper indexing
- Implement Redis caching
- Set up Celery workers

### Frontend Deployment
- Configure CI/CD pipelines
- Set up environment-specific builds
- Implement code splitting
- Configure CDN for static assets
- Set up error tracking (Sentry)

## Security Considerations

### Backend Security
- Implement rate limiting
- Set up CORS properly
- Use JWT with refresh tokens
- Implement request validation
- Set up API authentication
- Configure security headers

### Frontend Security
- Implement SSL pinning
- Secure local storage usage
- Input sanitization
- Implement proper error handling
- Secure API key storage

## Testing Strategy

### Backend Testing
- Unit tests for models
- Integration tests for APIs
- Performance testing
- Security testing

### Frontend Testing
- Component testing
- Integration testing
- E2E testing
- Mobile device testing

## Monitoring and Analytics

### Backend Monitoring
- Application performance monitoring
- Database monitoring
- Error tracking
- API usage metrics

### Frontend Monitoring
- User behavior analytics
- Performance metrics
- Error tracking
- Usage analytics

## Initial Setup Tasks

1. Backend Initial Setup
   - Set up Django project
   - Configure database
   - Create initial models
   - Set up API structure

2. Frontend Initial Setup
   - Create React project
   - Set up routing
   - Configure state management
   - Set up API integration

3. Mobile Setup
   - Initialize React Native project
   - Configure navigation
   - Set up native modules
   - Configure build settings

4. Development Environment
   - Configure linting
   - Set up pre-commit hooks
   - Configure testing environment
   - Set up documentation
