from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class CustomAnonThrottle(AnonRateThrottle):
    rate = '100/day'

class CustomUserThrottle(UserRateThrottle):
    rate = '1000/day'

class AuthenticationThrottle(UserRateThrottle):
    rate = '50/hour'
    scope = 'auth' 