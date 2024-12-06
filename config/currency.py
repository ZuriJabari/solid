"""
Currency settings for the application.
"""
from decimal import Decimal

# Currency settings
CURRENCY = 'UGX'
CURRENCY_SYMBOL = 'UGX'
CURRENCY_DECIMAL_PLACES = 2
CURRENCY_THOUSAND_SEPARATOR = ','
CURRENCY_USE_GROUPING = True

# Minimum and maximum amounts
MIN_AMOUNT = Decimal('100')  # 100 UGX minimum
MAX_AMOUNT = Decimal('100000000')  # 100M UGX maximum

# Format currency amount
def format_currency(amount):
    """Format amount in UGX currency format"""
    if amount is None:
        return f"{CURRENCY_SYMBOL} 0.00"
    
    # Format with decimals and thousand separator
    formatted = "{:,.2f}".format(Decimal(str(amount)))
    
    return f"{CURRENCY_SYMBOL} {formatted}" 