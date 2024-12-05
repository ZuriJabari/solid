from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Address, UserPreference

User = get_user_model()

class UserModelTests(TestCase):
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
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        """Test creating a new superuser"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_str(self):
        """Test the user string representation"""
        self.assertEqual(str(self.user), self.user.email)

    def test_user_full_name(self):
        """Test user full name"""
        self.assertEqual(
            self.user.get_full_name(),
            f"{self.user.first_name} {self.user.last_name}"
        )

class AddressModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.address_data = {
            'user': self.user,
            'address_type': 'SHIPPING',
            'full_name': 'Test User',
            'street_address1': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': 'Test Country',
            'phone': '1234567890'
        }
        self.address = Address.objects.create(**self.address_data)

    def test_create_address(self):
        """Test creating a new address"""
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.address_type, 'SHIPPING')
        self.assertEqual(self.address.full_name, 'Test User')

    def test_address_str(self):
        """Test the address string representation"""
        expected_str = f"{self.address.full_name} - {self.address.city}, {self.address.state}"
        self.assertEqual(str(self.address), expected_str)

    def test_default_address(self):
        """Test setting an address as default"""
        # Create another address
        second_address = Address.objects.create(
            user=self.user,
            address_type='SHIPPING',
            full_name='Test User 2',
            street_address1='456 Test St',
            city='Test City 2',
            state='Test State 2',
            postal_code='67890',
            country='Test Country',
            phone='0987654321',
            is_default=True
        )
        
        # First address should not be default
        self.address.refresh_from_db()
        self.assertFalse(self.address.is_default)
        
        # Second address should be default
        self.assertTrue(second_address.is_default)

class UserPreferenceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.preference = UserPreference.objects.get(user=self.user)

    def test_preference_creation(self):
        """Test that UserPreference is created automatically"""
        self.assertIsNotNone(self.preference)
        self.assertEqual(self.preference.user, self.user)
        self.assertEqual(self.preference.theme, 'SYSTEM')

    def test_preference_str(self):
        """Test the preference string representation"""
        expected_str = f"Preferences for {self.user.email}"
        self.assertEqual(str(self.preference), expected_str)

    def test_default_values(self):
        """Test default values for preferences"""
        self.assertEqual(self.preference.theme, 'SYSTEM')
        self.assertEqual(self.preference.email_notifications, {})
        self.assertEqual(self.preference.push_notifications, {})
        self.assertIsNone(self.preference.default_shipping_address)
        self.assertIsNone(self.preference.default_billing_address) 