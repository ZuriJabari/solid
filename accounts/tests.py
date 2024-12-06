from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from products.models import Category, Product
from .models import UserPreference

User = get_user_model()

class UserTests(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """Test creating a new user"""
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

class AuthAPITests(APITestCase):
    def setUp(self):
        self.login_url = reverse('accounts:api-login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_login(self):
        """Test user login endpoint"""
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

class UserPreferenceTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            description='Test Description 1',
            price=99.99,
            category=self.category
        )
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test Description 2',
            price=149.99,
            category=self.category
        )

        # Get user preferences
        self.preferences = UserPreference.objects.get(user=self.user)
        self.preferences_url = reverse('accounts:preference-detail', args=[self.preferences.id])

    def test_add_to_wishlist(self):
        """Test adding a product to wishlist"""
        url = reverse('accounts:preference-add-to-wishlist', args=[self.preferences.id])
        response = self.client.post(url, {'product_id': self.product1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.product1, self.preferences.wishlist_items.all())

    def test_remove_from_wishlist(self):
        """Test removing a product from wishlist"""
        self.preferences.wishlist_items.add(self.product1)
        url = reverse('accounts:preference-remove-from-wishlist', args=[self.preferences.id])
        response = self.client.post(url, {'product_id': self.product1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.product1, self.preferences.wishlist_items.all())

    def test_add_to_saved_items(self):
        """Test adding a product to saved items"""
        url = reverse('accounts:preference-add-to-saved', args=[self.preferences.id])
        response = self.client.post(url, {'product_id': self.product1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.product1, self.preferences.saved_items.all())

    def test_remove_from_saved_items(self):
        """Test removing a product from saved items"""
        self.preferences.saved_items.add(self.product1)
        url = reverse('accounts:preference-remove-from-saved', args=[self.preferences.id])
        response = self.client.post(url, {'product_id': self.product1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.product1, self.preferences.saved_items.all())

    def test_update_notification_preferences(self):
        """Test updating notification preferences"""
        data = {
            'email_notifications': 'important',
            'push_notifications': 'none'
        }
        response = self.client.patch(self.preferences_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.preferences.refresh_from_db()
        self.assertEqual(self.preferences.email_notifications, 'important')
        self.assertEqual(self.preferences.push_notifications, 'none')

    def test_update_preferred_categories(self):
        """Test updating preferred categories"""
        data = {
            'preferred_categories': [self.category.id]
        }
        response = self.client.patch(self.preferences_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.preferences.refresh_from_db()
        self.assertIn(self.category, self.preferences.preferred_categories.all())
