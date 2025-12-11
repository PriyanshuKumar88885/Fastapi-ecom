"""
Application configuration and settings.

Loads environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    # Environment
    ENV = os.getenv('ENV', 'production')  # production | testing
    DEBUG = ENV != 'production'

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./ecommerce.db')

    # Keycloak / OIDC
    KEYCLOAK_JWKS_URL = os.getenv('KEYCLOAK_JWKS_URL')
    KEYCLOAK_AUDIENCE = os.getenv('KEYCLOAK_AUDIENCE')
    KEYCLOAK_ISSUER = os.getenv('KEYCLOAK_ISSUER')
    
    # Keycloak Admin API
    KEYCLOAK_ADMIN_URL = os.getenv('KEYCLOAK_ADMIN_URL', 'http://localhost:8080')
    KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'ecom')
    KEYCLOAK_ADMIN_USERNAME = os.getenv('KEYCLOAK_ADMIN_USERNAME')
    KEYCLOAK_ADMIN_PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD')
    
    # Keycloak Client (for token exchange)
    KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'Confidential-Client')
    KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else ['*']
    CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'false').lower() == 'true'
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['*']

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # json | text

    # API
    API_TITLE = 'E-Commerce API'
    API_DESCRIPTION = 'Multi-tenant e-commerce with Keycloak authentication'
    API_VERSION = '1.0.0'
    API_PREFIX = ''  # Routes have their own prefixes (/tenants, /products, etc.)
    DOCS_URL = '/docs'
    REDOC_URL = '/redoc'
    OPENAPI_URL = '/openapi.json'

    # Pagination
    DEFAULT_SKIP = 0
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 100

    @classmethod
    def validate(cls):
        """Validate required settings based on environment."""
        if cls.ENV == 'production':
            required_settings = {
                'KEYCLOAK_JWKS_URL': cls.KEYCLOAK_JWKS_URL,
                'KEYCLOAK_ISSUER': cls.KEYCLOAK_ISSUER,
                'KEYCLOAK_ADMIN_USERNAME': cls.KEYCLOAK_ADMIN_USERNAME,
                'KEYCLOAK_ADMIN_PASSWORD': cls.KEYCLOAK_ADMIN_PASSWORD,
                'KEYCLOAK_CLIENT_SECRET': cls.KEYCLOAK_CLIENT_SECRET,
            }
            missing = [key for key, value in required_settings.items() if not value]
            if missing:
                raise ValueError(f"Required settings missing in production: {', '.join(missing)}")


# Load settings and validate
settings = Settings()
settings.validate()
