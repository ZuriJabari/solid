import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Category, Product, ProductImage, ProductReview, Inventory
from analytics.models import ProductPerformance
from django.core.files import File
from django.conf import settings

User = get_user_model()

def create_sample_users():
    # Create sample users
    users = []
    for i in range(5):
        user = User.objects.create_user(
            email=f'user{i+1}@example.com',
            password='password123',
            first_name=f'User{i+1}',
            last_name='Test',
            is_active=True,
            email_verified=True
        )
        users.append(user)
    return users

def create_categories():
    categories = [
        {
            'name': 'CBD Oils',
            'description': 'High-quality CBD oils for various wellness needs'
        },
        {
            'name': 'CBD Edibles',
            'description': 'Delicious CBD-infused treats and supplements'
        },
        {
            'name': 'Topicals',
            'description': 'CBD-infused creams, balms, and lotions for skin care and pain relief'
        },
        {
            'name': 'CBD Capsules',
            'description': 'Easy-to-take CBD capsules and softgels'
        },
        {
            'name': 'Pet CBD',
            'description': 'CBD products specially formulated for pets'
        }
    ]
    
    created_categories = []
    for cat in categories:
        category = Category.objects.create(
            name=cat['name'],
            description=cat['description']
        )
        created_categories.append(category)
    return created_categories

def create_products(categories):
    products_data = [
        # CBD Oils
        {
            'category': 'CBD Oils',
            'products': [
                {
                    'name': 'Full Spectrum CBD Oil 1000mg',
                    'description': 'High-potency full spectrum CBD oil with natural terpenes. Perfect for experienced users.',
                    'price': Decimal('89.99'),
                    'stock': 50
                },
                {
                    'name': 'Broad Spectrum CBD Oil 500mg',
                    'description': 'THC-free broad spectrum CBD oil ideal for daily use.',
                    'price': Decimal('59.99'),
                    'stock': 75
                },
                {
                    'name': 'CBD Isolate Oil 250mg',
                    'description': 'Pure CBD isolate oil perfect for beginners.',
                    'price': Decimal('39.99'),
                    'stock': 100
                }
            ]
        },
        # CBD Edibles
        {
            'category': 'CBD Edibles',
            'products': [
                {
                    'name': 'CBD Gummies 300mg',
                    'description': 'Delicious fruit-flavored CBD gummies. 10mg per gummy.',
                    'price': Decimal('29.99'),
                    'stock': 150
                },
                {
                    'name': 'CBD Chocolate Bar 100mg',
                    'description': 'Premium dark chocolate infused with CBD.',
                    'price': Decimal('19.99'),
                    'stock': 100
                }
            ]
        },
        # Topicals
        {
            'category': 'Topicals',
            'products': [
                {
                    'name': 'CBD Pain Relief Cream 750mg',
                    'description': 'Powerful CBD cream for targeted pain relief.',
                    'price': Decimal('64.99'),
                    'stock': 80
                },
                {
                    'name': 'CBD Skin Care Balm 250mg',
                    'description': 'Nourishing CBD balm for healthy skin.',
                    'price': Decimal('45.99'),
                    'stock': 90
                }
            ]
        },
        # CBD Capsules
        {
            'category': 'CBD Capsules',
            'products': [
                {
                    'name': 'CBD Softgels 750mg',
                    'description': 'Easy-to-swallow CBD softgels with 25mg per capsule.',
                    'price': Decimal('69.99'),
                    'stock': 60
                },
                {
                    'name': 'CBD Sleep Capsules 450mg',
                    'description': 'CBD capsules with melatonin for better sleep.',
                    'price': Decimal('54.99'),
                    'stock': 70
                }
            ]
        },
        # Pet CBD
        {
            'category': 'Pet CBD',
            'products': [
                {
                    'name': 'Pet CBD Oil 250mg',
                    'description': 'Specially formulated CBD oil for pets.',
                    'price': Decimal('44.99'),
                    'stock': 85
                },
                {
                    'name': 'Pet CBD Treats 150mg',
                    'description': 'CBD-infused treats your pets will love.',
                    'price': Decimal('34.99'),
                    'stock': 120
                }
            ]
        }
    ]

    created_products = []
    for category_data in products_data:
        category = Category.objects.get(name=category_data['category'])
        for product_data in category_data['products']:
            product = Product.objects.create(
                category=category,
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock'],
                is_active=True
            )
            
            # Create inventory
            Inventory.objects.create(
                product=product,
                quantity=product_data['stock'],
                low_stock_threshold=20
            )
            
            created_products.append(product)
    return created_products

def create_reviews(products, users):
    reviews_data = [
        "Great product! Really helped with my anxiety.",
        "Excellent quality and fast shipping.",
        "This product works exactly as described.",
        "Very effective for pain relief.",
        "Good value for money.",
        "Will definitely buy again!",
        "Noticed improvement in sleep quality.",
        "Pleasant taste and easy to use.",
        "High-quality product, recommended!",
        "Fast acting and effective."
    ]
    
    for product in products:
        # Create 3-5 reviews per product
        for _ in range(random.randint(3, 5)):
            ProductReview.objects.create(
                product=product,
                user=random.choice(users),
                rating=random.randint(4, 5),  # Mostly positive reviews
                comment=random.choice(reviews_data),
                is_verified_purchase=True,
                is_approved=True
            )

def create_product_performance(products):
    # Create performance metrics for the last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    for product in products:
        for day in range(30):
            date = start_date + timedelta(days=day)
            ProductPerformance.objects.create(
                product=product,
                date=date,
                views=random.randint(50, 200),
                add_to_cart_count=random.randint(5, 20),
                purchase_count=random.randint(1, 10),
                revenue=Decimal(random.randint(100, 1000)),
                conversion_rate=Decimal(random.randint(1, 5))
            )

def clear_existing_data():
    """Clear all existing data from the database"""
    print("Clearing existing data...")
    User.objects.filter(is_superuser=False).delete()
    Category.objects.all().delete()
    Product.objects.all().delete()
    ProductReview.objects.all().delete()
    ProductPerformance.objects.all().delete()
    Inventory.objects.all().delete()

def main():
    print("Creating sample data...")
    
    # Clear existing data
    clear_existing_data()
    
    # Create sample users
    print("Creating users...")
    users = create_sample_users()
    
    # Create categories
    print("Creating categories...")
    categories = create_categories()
    
    # Create products
    print("Creating products...")
    products = create_products(categories)
    
    # Create reviews
    print("Creating product reviews...")
    create_reviews(products, users)
    
    # Create product performance data
    print("Creating product performance data...")
    create_product_performance(products)
    
    print("Sample data creation completed!")

if __name__ == "__main__":
    main() 