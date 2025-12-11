"""
Unit tests for Tenant Management
"""
import pytest


class TestTenantManagement:
    """Test tenant CRUD operations"""
    
    def test_create_tenant_as_platform_admin(self, client):
        """Platform admin can create a tenant"""
        response = client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nike"
        assert "id" in data
    
    def test_create_tenant_as_regular_user_fails(self, client):
        """Regular user cannot create a tenant"""
        response = client.post(
            '/tenants/',
            headers={"Authorization": "Bearer user-token"},
            json={"name": "Unauthorized"}
        )
        assert response.status_code == 403
    
    def test_create_tenant_as_tenant_admin_fails(self, client):
        """Tenant admin cannot create a tenant"""
        # First create a tenant for the admin
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to create another tenant as tenant admin
        response = client.post(
            '/tenants/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Adidas"}
        )
        assert response.status_code == 403
    
    def test_create_tenant_without_auth_fails(self, client):
        """Creating tenant without authentication fails"""
        response = client.post(
            '/tenants/',
            json={"name": "NoAuth"}
        )
        assert response.status_code == 401
    
    def test_create_duplicate_tenant_fails(self, client):
        """Cannot create tenant with duplicate name"""
        # Create first tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to create duplicate
        response = client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        assert response.status_code == 400
    
    def test_delete_tenant_as_platform_admin(self, client):
        """Platform admin can delete a tenant"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Delete tenant
        response = client.delete(
            '/tenants/Nike',
            headers={"Authorization": "Bearer platform-admin-token"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Tenant deleted successfully"
    
    def test_delete_nonexistent_tenant_fails(self, client):
        """Deleting non-existent tenant fails"""
        response = client.delete(
            '/tenants/NonExistent',
            headers={"Authorization": "Bearer platform-admin-token"}
        )
        assert response.status_code == 404
    
    def test_delete_tenant_as_regular_user_fails(self, client):
        """Regular user cannot delete a tenant"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to delete as user
        response = client.delete(
            '/tenants/Nike',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 403
