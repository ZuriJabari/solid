from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Address, UserPreference

User = get_user_model()

class UserViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890'
        }
        self.user = User.objects.create_user(
            email='existing@example.com',
            password='existing123',
            first_name='Existing',
            last_name='User'
        )

    def test_create_user(self):
        """Test creating a new user"""
        url = reverse('user-list')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_me_endpoint(self):
        """Test the me endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_change_password(self):
        """Test changing password"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-change-password')
        data = {
            'old_password': 'existing123',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

class AddressViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.address_data = {
            'address_type': 'SHIPPING',
            'full_name': 'Test User',
            'street_address1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': 'Test Country',
            'phone': '1234567890',
            'is_default': True
        }

    def test_create_address(self):
        """Test creating a new address"""
        url = reverse('address-list')
        response = self.client.post(url, self.address_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 1)
        address = Address.objects.first()
        self.assertEqual(address.user, self.user)
        self.assertTrue(address.is_default)

    def test_list_addresses(self):
        """Test listing user's addresses"""
        Address.objects.create(user=self.user, **self.address_data)
        url = reverse('address-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_set_default_address(self):
        """Test setting an address as default"""
        address = Address.objects.create(user=self.user, **self.address_data)
        url = reverse('address-set-default', kwargs={'pk': address.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        address.refresh_from_db()
        self.assertTrue(address.is_default)

class UserPreferenceViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.preference = UserPreference.objects.get(user=self.user)

    def test_get_preferences(self):
        """Test retrieving user preferences"""
        url = reverse('preference-detail', kwargs={'pk': self.preference.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['theme'], 'SYSTEM')

    def test_update_preferences(self):
        """Test updating user preferences"""
        url = reverse('preference-detail', kwargs={'pk': self.preference.id})
        data = {
            'theme': 'DARK',
            'email_notifications': {'order_updates': True}
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.preference.refresh_from_db()
        self.assertEqual(self.preference.theme, 'DARK')
        self.assertEqual(
            self.preference.email_notifications,
            {'order_updates': True}
        ) 