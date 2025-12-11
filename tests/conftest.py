import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.database import engine, Base, SessionLocal


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    """Create fresh test database for the session"""
    # Create fresh DB for tests
    if os.path.exists('test_ecommerce.db'):
        os.remove('test_ecommerce.db')
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Teardown
    if os.path.exists('test_ecommerce.db'):
        os.remove('test_ecommerce.db')


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database tables between each test"""
    yield
    # Clear all tables after each test
    db = SessionLocal()
    try:
        # Delete in reverse order to respect foreign keys
        from app.models import user_favourites
        db.execute(user_favourites.delete())
        db.execute(Base.metadata.tables['order_items'].delete())
        db.execute(Base.metadata.tables['orders'].delete())
        db.execute(Base.metadata.tables['products'].delete())
        db.execute(Base.metadata.tables['users'].delete())
        db.execute(Base.metadata.tables['tenants'].delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client():
    """FastAPI test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """Database session for tests"""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def mock_jwt_auth():
    """
    Mock JWT verification for all tests.
    Maps token strings to user claims.
    """
    def mock_verify(token):
        # Platform admin token
        if token == "platform-admin-token":
            return {
                "preferred_username": "platform_admin",
                "realm_access": {"roles": ["platform_admin"]},
                "tenant": None
            }
        
        # Nike tenant admin token
        elif token == "nike-admin-token":
            return {
                "preferred_username": "nike_admin",
                "realm_access": {"roles": ["tenant_admin"]},
                "tenant": "Nike"
            }
        
        # Adidas tenant admin token
        elif token == "adidas-admin-token":
            return {
                "preferred_username": "adidas_admin",
                "realm_access": {"roles": ["tenant_admin"]},
                "tenant": "Adidas"
            }
        
        # Regular user token
        elif token == "user-token":
            return {
                "preferred_username": "john_doe",
                "realm_access": {"roles": ["user"]},
                "tenant": None
            }
        
        # Another regular user token
        elif token == "user2-token":
            return {
                "preferred_username": "jane_smith",
                "realm_access": {"roles": ["user"]},
                "tenant": None
            }
        
        # Invalid token
        return None
    
    # Patch in dependencies module where it's used
    with patch("app.dependencies.verify_jwt_token", side_effect=mock_verify):
        yield
