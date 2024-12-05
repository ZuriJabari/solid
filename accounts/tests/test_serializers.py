from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Address, UserPreference
from accounts.serializers import (
    UserSerializer, UserRegistrationSerializer,
    AddressSerializer, UserPreferenceSerializer,
    PasswordChangeSerializer
)

User = get_user_model()

class UserSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.serializer = UserSerializer(instance=self.user)

    def test_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'email', 'first_name', 'last_name', 'phone',
             'date_of_birth', 'email_verified', 'newsletter_subscribed',
             'marketing_preferences', 'is_active', 'created_at',
             'updated_at', 'addresses', 'preferences']
        )

class UserRegistrationSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890'
        }

    def test_passwords_match(self):
        """Test that passwords match validation works"""
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_passwords_mismatch(self):
        """Test that password mismatch is caught"""
        self.user_data['confirm_password'] = 'wrongpass'
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_create_user(self):
        """Test that user is created correctly"""
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))

class AddressSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
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
        self.address = Address.objects.create(user=self.user, **self.address_data)
        self.serializer = AddressSerializer(instance=self.address)

    def test_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'address_type', 'is_default', 'full_name',
             'street_address1', 'street_address2', 'city', 'state',
             'postal_code', 'country', 'phone', 'created_at',
             'updated_at']
        )

class UserPreferenceSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.preference = UserPreference.objects.get(user=self.user)
        self.serializer = UserPreferenceSerializer(instance=self.preference)

    def test_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'theme', 'email_notifications', 'push_notifications',
             'default_shipping_address', 'default_billing_address',
             'created_at', 'updated_at']
        )

class PasswordChangeSerializerTests(TestCase):
    def setUp(self):
        self.password_data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }

    def test_passwords_match(self):
        """Test that new passwords match validation works"""
        serializer = PasswordChangeSerializer(data=self.password_data)
        self.assertTrue(serializer.is_valid())

    def test_passwords_mismatch(self):
        """Test that new password mismatch is caught"""
        self.password_data['confirm_new_password'] = 'wrongpass'
        serializer = PasswordChangeSerializer(data=self.password_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors) 