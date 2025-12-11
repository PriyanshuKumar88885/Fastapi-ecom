"""
Unit tests for User Management
"""
import pytest


class TestUserManagement:
    """Test user creation and management"""
    
    def test_platform_admin_create_tenant_admin(self, client):
        """Platform admin can create tenant admin user"""
        # Create tenant first
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create tenant admin
        response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={
                "username": "nike_manager",
                "role": "tenant_admin",
                "password": "secure123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "nike_manager"
        assert data["role"] == "tenant_admin"
        assert data["tenant_id"] is not None
    
    def test_platform_admin_create_regular_user(self, client):
        """Platform admin can create regular user"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create user
        response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={
                "username": "customer1",
                "role": "user",
                "password": "pass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "customer1"
        assert data["role"] == "user"
    
    def test_list_tenant_users(self, client):
        """Platform admin can list users in a tenant"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create users
        client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "user1", "role": "user", "password": "pass1"}
        )
        client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "user2", "role": "user", "password": "pass2"}
        )
        
        # List users
        response = client.get(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_update_user_role(self, client):
        """Platform admin can update user role"""
        # Create tenant and user
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        create_response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "user1", "role": "user", "password": "pass1"}
        )
        user_id = create_response.json()["id"]
        
        # Update role
        response = client.put(
            f'/tenants/Nike/users/{user_id}',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "user1", "role": "tenant_admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "tenant_admin"
    
    def test_delete_user(self, client):
        """Platform admin can delete user"""
        # Create tenant and user
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        create_response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "user1", "role": "user", "password": "pass1"}
        )
        user_id = create_response.json()["id"]
        
        # Delete user
        response = client.delete(
            f'/tenants/Nike/users/{user_id}',
            headers={"Authorization": "Bearer platform-admin-token"}
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "deleted"
    
    def test_tenant_admin_cannot_create_users(self, client):
        """Tenant admin cannot create users (only platform admin can)"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to create user as tenant admin
        response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"username": "unauthorized", "role": "user", "password": "pass"}
        )
        assert response.status_code == 403
    
    def test_regular_user_cannot_manage_users(self, client):
        """Regular user cannot manage users"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to list users as regular user
        response = client.get(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 403
    
    def test_create_duplicate_username_fails(self, client):
        """Cannot create user with duplicate username"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create first user
        client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "duplicate", "role": "user", "password": "pass1"}
        )
        
        # Try to create duplicate
        response = client.post(
            '/tenants/Nike/users/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"username": "duplicate", "role": "user", "password": "pass2"}
        )
        assert response.status_code == 400


class TestUserSignup:
    """Test public user signup"""
    
    def test_user_signup(self, client):
        """User can signup without authentication"""
        response = client.post(
            '/users/signup',
            json={
                "username": "new_user",
                "password": "secure_password"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "new_user"
        assert data["role"] == "user"
    
    def test_signup_duplicate_username_fails(self, client):
        """Cannot signup with duplicate username"""
        # First signup
        client.post(
            '/users/signup',
            json={"username": "john", "password": "pass1"}
        )
        
        # Try duplicate
        response = client.post(
            '/users/signup',
            json={"username": "john", "password": "pass2"}
        )
        assert response.status_code == 400
