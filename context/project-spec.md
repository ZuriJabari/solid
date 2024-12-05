# CBD E-commerce Platform Technical Specification

## Project Overview
Cross-platform e-commerce application for CBD products with delivery/pickup capabilities in Kampala, Entebbe, and Mukono regions.

## Technology Stack

### Backend (Python/Django)
- Python 3.11+
- Django 5.0+
- Django REST Framework 3.14+
- PostgreSQL 15+
- Redis (for caching and task queue)
- Celery (for async tasks)

#### Backend Dependencies
```
django-cors-headers
django-filter
django-storages
djangorestframework-simplejwt
Pillow
psycopg2-binary
python-dotenv
django-phonenumber-field
geopy (for distance calculations)
stripe (payment processing)
```

### Frontend (React/React Native)
- React 18+
- React Native 0.72+ with Expo
- TypeScript 5+
- Node.js 18+ LTS

#### Frontend Dependencies
```
@react-navigation/native
@react-navigation/stack
@reduxjs/toolkit
react-redux
axios
formik
yup
tailwindcss
react-native-maps
react-native-paper
expo-location
expo-image-picker
```

## System Architecture

### Backend Components

#### Django Apps Structure
```
backend/
├── config/                 # Project settings
├── accounts/              # User management
├── products/             # Product catalog
├── orders/              # Order processing
├── payments/           # Payment integration
├── locations/         # Delivery/Pickup
├── analytics/        # Business intelligence
└── utils/           # Shared utilities
```

#### Key Models
```python
# accounts/models.py
class User(AbstractUser):
    phone = PhoneNumberField(unique=True)
    date_of_birth = models.DateField()
    verified = models.BooleanField(default=False)

# products/models.py
class Product:
    name = models.CharField()
    description = models.TextField()
    price = models.DecimalField()
    category = models.ForeignKey()
    stock = models.IntegerField()

# orders/models.py
class Order:
    user = models.ForeignKey()
    items = models.ManyToManyField()
    delivery_type = models.CharField(choices=['DELIVERY', 'PICKUP'])
    status = models.CharField()
    total = models.DecimalField()

# locations/models.py
class DeliveryZone:
    name = models.CharField()
    polygon = models.PolygonField()
    base_fee = models.DecimalField()
```

### Frontend Architecture

#### Web Application Structure
```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/           # Route components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API integration
│   ├── store/           # Redux store
│   ├── utils/           # Helper functions
│   └── types/           # TypeScript definitions
```

#### Mobile Application Structure (React Native)
```
mobile/
├── src/
│   ├── components/      # Shared components
│   ├── screens/         # Screen components
│   ├── navigation/      # Navigation config
│   ├── services/        # API integration
│   ├── store/          # Redux store
│   ├── hooks/          # Custom hooks
│   └── utils/          # Helper functions
```

## API Endpoints

### Authentication
```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/verify-age/
POST /api/auth/refresh-token/
```

### Products
```
GET /api/products/
GET /api/products/{id}/
GET /api/products/categories/
GET /api/products/search/
```

### Orders
```
POST /api/orders/create/
GET /api/orders/
GET /api/orders/{id}/
PATCH /api/orders/{id}/status/
```

### Delivery
```
GET /api/delivery/zones/
POST /api/delivery/calculate-fee/
GET /api/delivery/pickup-locations/
```

## Development Setup

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Frontend Setup
```bash
# Web application
cd frontend
npm install
npm run dev

# Mobile application
cd mobile
npm install
npx expo start
```

## Development Workflow

1. Initial Setup
- Set up version control (Git)
- Configure development environment
- Set up CI/CD pipeline (GitHub Actions)

2. Backend Development
- Implement models and migrations
- Create API endpoints
- Add authentication and authorization
- Implement business logic
- Add tests

3. Frontend Development
- Set up project structure
- Implement UI components
- Add state management
- Integrate with backend API
- Add responsive design

4. Mobile Development
- Configure Expo
- Implement native features
- Add push notifications
- Handle offline mode
- Platform-specific optimizations

## Security Considerations

1. Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Age verification
- Session management

2. Data Protection
- Input validation
- XSS prevention
- CSRF protection
- SQL injection prevention

3. API Security
- Rate limiting
- Request validation
- Error handling
- Logging and monitoring

## Testing Strategy

1. Backend Testing
- Unit tests for models and services
- Integration tests for API endpoints
- Performance testing

2. Frontend Testing
- Component testing with React Testing Library
- E2E testing with Cypress
- Mobile testing with Detox

## Deployment

### Backend Deployment
- Use Docker containers
- Deploy to DigitalOcean or AWS
- Configure NGINX
- Set up SSL certificates

### Frontend Deployment
- Deploy web app to Vercel
- Configure CDN
- Submit mobile apps to stores

## Monitoring and Analytics

1. System Monitoring
- Server metrics
- Error tracking
- Performance monitoring
- User analytics

2. Business Analytics
- Sales metrics
- User behavior
- Inventory tracking
- Delivery analytics
