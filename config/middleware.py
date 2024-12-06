from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    def process_response(self, request, response):
        # Content Security Policy
        if '/swagger/' in request.path or '/redoc/' in request.path:
            # More permissive CSP for Swagger UI
            response['Content-Security-Policy'] = (
                "default-src * 'unsafe-inline' 'unsafe-eval'; "
                "img-src * data: blob: 'unsafe-inline'; "
                "connect-src * 'unsafe-inline'; "
                "style-src * 'unsafe-inline'; "
                "script-src * 'unsafe-inline' 'unsafe-eval';"
            )
        else:
            # Strict CSP for other routes
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # HSTS (uncomment in production with proper cert)
        # response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'accelerometer=(), '
            'camera=(), '
            'geolocation=(), '
            'gyroscope=(), '
            'magnetometer=(), '
            'microphone=(), '
            'payment=(), '
            'usb=()'
        )
        
        return response 