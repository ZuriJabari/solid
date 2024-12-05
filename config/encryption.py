from cryptography.fernet import Fernet
from django.conf import settings
from base64 import b64encode, b64decode
import os

class EncryptionManager:
    def __init__(self):
        # Get or generate encryption key
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)

    def _get_or_create_key(self):
        """Get existing key or create a new one"""
        key_file = os.path.join(settings.BASE_DIR, '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt(self, data):
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        encrypted_data = self.cipher_suite.encrypt(data)
        return b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_data):
        """Decrypt data"""
        try:
            encrypted_data = b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

# Create a singleton instance
encryption_manager = EncryptionManager()

class EncryptedTextField:
    """
    Custom field type for encrypted text data
    Usage:
    class SensitiveData(models.Model):
        encrypted_data = EncryptedTextField()
    """
    def __init__(self, *args, **kwargs):
        self.encryption_manager = encryption_manager

    def __get__(self, instance, owner):
        if instance is None:
            return self
        encrypted_value = instance.__dict__.get(self.field_name)
        if encrypted_value:
            return self.encryption_manager.decrypt(encrypted_value)
        return None

    def __set__(self, instance, value):
        if value is not None:
            encrypted_value = self.encryption_manager.encrypt(value)
            instance.__dict__[self.field_name] = encrypted_value
        else:
            instance.__dict__[self.field_name] = None

    def contribute_to_class(self, cls, name):
        self.field_name = name
        setattr(cls, name, self) 