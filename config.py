import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ntando-store-super-secret-key-change-in-production'
    
    # Domain configuration
    SUPPORTED_TLDS = ['.net', '.com', '.zw', '.dev', '.id']
    BASE_DOMAINS = {
        'net': os.environ.get('BASE_DOMAIN_NET', 'ntandostore.net'),
        'com': os.environ.get('BASE_DOMAIN_COM', 'ntandostore.com'),
        'zw': os.environ.get('BASE_DOMAIN_ZW', 'ntandostore.co.zw'),
        'dev': os.environ.get('BASE_DOMAIN_DEV', 'ntandostore.dev'),
        'id': os.environ.get('BASE_DOMAIN_ID', 'ntandostore.id')
    }
    
    # Security
    RATE_LIMIT = "100 per minute"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Caching
    CACHE_TYPE = "SimpleCache"  # Use Redis in production
    CACHE_DEFAULT_TIMEOUT = 300
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # DNS Configuration
    DNS_PROVIDERS = {
        'cloudflare': {
            'api_token': os.environ.get('CLOUDFLARE_API_TOKEN'),
            'zone_ids': {
                'net': os.environ.get('CLOUDFLARE_ZONE_NET'),
                'com': os.environ.get('CLOUDFLARE_ZONE_COM'),
                'zw': os.environ.get('CLOUDFLARE_ZONE_ZW'),
                'dev': os.environ.get('CLOUDFLARE_ZONE_DEV'),
                'id': os.environ.get('CLOUDFLARE_ZONE_ID')
            }
        }
    }
    
    # Server Configuration
    PORT = int(os.environ.get('PORT', 10000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
