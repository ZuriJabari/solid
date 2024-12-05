import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_password_strength(password):
    """
    Validate password strength
    - At least 8 characters
    - Contains uppercase and lowercase
    - Contains numbers
    - Contains special characters
    """
    if len(password) < 8:
        raise ValidationError(_('Password must be at least 8 characters long.'))
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    
    if not re.search(r'\d', password):
        raise ValidationError(_('Password must contain at least one number.'))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_('Password must contain at least one special character.'))

def validate_phone_number(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    if not re.match(pattern, phone):
        raise ValidationError(_('Enter a valid phone number.'))

def sanitize_input(value):
    """Basic input sanitization"""
    if isinstance(value, str):
        # Remove any HTML tags
        value = re.sub(r'<[^>]*?>', '', value)
        # Convert special characters to HTML entities
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')
        # Remove any potential script injections
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'data:', '', value, flags=re.IGNORECASE)
    return value

def validate_file_extension(value, allowed_extensions=None):
    """Validate file extension"""
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    
    ext = value.name.lower().split('.')[-1]
    if f'.{ext}' not in allowed_extensions:
        raise ValidationError(_('Unsupported file extension.'))

def validate_file_size(value, max_size=5242880):  # 5MB default
    """Validate file size"""
    if value.size > max_size:
        raise ValidationError(_('File size cannot exceed 5MB.')) 