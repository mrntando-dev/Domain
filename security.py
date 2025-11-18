import hashlib
import hmac
import secrets
import re
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta

class SecurityManager:
    """Advanced security manager"""
    
    @staticmethod
    def generate_token(data, expiry_hours=24):
        """Generate JWT token"""
        payload = {
            'data': data,
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload['data']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def sanitize_subdomain(subdomain):
        """Sanitize subdomain input"""
        # Remove any dangerous characters
        subdomain = re.sub(r'[^a-z0-9\-]', '', subdomain.lower())
        # Ensure it doesn't start or end with hyphen
        subdomain = subdomain.strip('-')
        # Limit length
        subdomain = subdomain[:63]
        return subdomain
    
    @staticmethod
    def validate_subdomain(subdomain):
        """Validate subdomain format"""
        if not subdomain or len(subdomain) < 1 or len(subdomain) > 63:
            return False
        # RFC 1123 compliant
        pattern = r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$'
        return bool(re.match(pattern, subdomain))
    
    @staticmethod
    def generate_api_key():
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    @staticmethod
    def verify_signature(data, signature, secret):
        """Verify HMAC signature"""
        expected_signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        # Verify API key (implement your logic)
        return f(*args, **kwargs)
    return decorated_function

def validate_request(f):
    """Decorator to validate request data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check content type
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function
