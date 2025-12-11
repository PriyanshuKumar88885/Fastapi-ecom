"""
Unit tests for Product Management
"""
import pytest


class TestProductManagement:
    """Test product CRUD operations"""
    
    def test_tenant_admin_create_product(self, client):
        """Tenant admin can create product in their tenant"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create product
        response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={
                "name": "Air Max 90",
                "description": "Classic sneaker",
                "category": "shoes",
                "price": 120.0,
                "available_quantity": 50
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Air Max 90"
        assert data["price"] == 120.0
        assert data["available_quantity"] == 50
        assert data["tenant_id"] is not None
    
    def test_platform_admin_create_product(self, client):
        """Platform admin can create product in any tenant"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create product as platform admin
        response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={
                "name": "Air Jordan 1",
                "category": "shoes",
                "price": 180.0,
                "available_quantity": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Air Jordan 1"
    
    def test_regular_user_cannot_create_product(self, client):
        """Regular user cannot create product"""
        # Create tenant
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Try to create product as user
        response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "name": "Unauthorized Product",
                "price": 100.0,
                "available_quantity": 10
            }
        )
        assert response.status_code == 403
    
    def test_tenant_admin_cannot_create_in_other_tenant(self, client):
        """Tenant admin cannot create product in another tenant"""
        # Create two tenants
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Adidas"}
        )
        
        # Nike admin tries to create in Adidas
        response = client.post(
            '/Adidas/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={
                "name": "Unauthorized",
                "price": 100.0,
                "available_quantity": 10
            }
        )
        assert response.status_code == 403
    
    def test_create_duplicate_product_in_tenant_fails(self, client):
        """Cannot create duplicate product name in same tenant"""
        # Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={
                "name": "Air Max",
                "price": 120.0,
                "available_quantity": 50
            }
        )
        
        # Try to create duplicate
        response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={
                "name": "Air Max",
                "price": 130.0,
                "available_quantity": 30
            }
        )
        assert response.status_code == 400
    
    def test_list_products_for_tenant(self, client):
        """Anyone can list products for a tenant"""
        # Create tenant and products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Product 1", "price": 100.0, "available_quantity": 10}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Product 2", "price": 150.0, "available_quantity": 20}
        )
        
        # List products (no auth required)
        response = client.get('/Nike/products/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_list_all_products(self, client):
        """Anyone can list all products from all tenants"""
        # Create tenants and products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Adidas"}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Nike Product", "price": 100.0, "available_quantity": 10}
        )
        client.post(
            '/Adidas/products/',
            headers={"Authorization": "Bearer adidas-admin-token"},
            json={"name": "Adidas Product", "price": 120.0, "available_quantity": 15}
        )
        
        # List all products
        response = client.get('/products/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_filter_products_by_category(self, client):
        """Can filter products by category"""
        # Create tenant and products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Sneakers", "category": "shoes", "price": 120.0, "available_quantity": 10}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "T-Shirt", "category": "clothing", "price": 30.0, "available_quantity": 50}
        )
        
        # Filter by category
        response = client.get('/Nike/products/?category=shoes')
        assert response.status_code == 200
        data = response.json()
        assert all(p["category"] == "shoes" for p in data)
    
    def test_search_products(self, client):
        """Can search products by name"""
        # Create tenant and products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max 90", "price": 120.0, "available_quantity": 10}
        )
        client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Jordan", "price": 180.0, "available_quantity": 20}
        )
        
        # Search for "Air"
        response = client.get('/Nike/products/?search=Air')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all("Air" in p["name"] for p in data)
    
    def test_get_product_by_id(self, client):
        """Can get specific product by ID"""
        # Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        create_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 10}
        )
        product_id = create_response.json()["id"]
        
        # Get product
        response = client.get(f'/Nike/products/{product_id}')
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Air Max"
    
    def test_update_product_as_tenant_admin(self, client):
        """Tenant admin can update their product"""
        # Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        create_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 10}
        )
        product_id = create_response.json()["id"]
        
        # Update product
        response = client.put(
            f'/Nike/products/{product_id}',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max Updated", "price": 99.99, "available_quantity": 50}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Air Max Updated"
        assert data["price"] == 99.99
        assert data["available_quantity"] == 50
    
    def test_tenant_admin_cannot_update_other_tenant_product(self, client):
        """Tenant admin cannot update another tenant's product"""
        # Create tenants and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Adidas"}
        )
        create_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Nike Product", "price": 120.0, "available_quantity": 10}
        )
        product_id = create_response.json()["id"]
        
        # Adidas admin tries to update Nike product
        response = client.put(
            f'/Nike/products/{product_id}',
            headers={"Authorization": "Bearer adidas-admin-token"},
            json={"price": 50.0}
        )
        assert response.status_code == 403
    
    def test_delete_product_as_tenant_admin(self, client):
        """Tenant admin can delete their product"""
        # Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        create_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 10}
        )
        product_id = create_response.json()["id"]
        
        # Delete product
        response = client.delete(
            f'/Nike/products/{product_id}',
            headers={"Authorization": "Bearer nike-admin-token"}
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "deleted"
    
    def test_regular_user_cannot_delete_product(self, client):
        """Regular user cannot delete product"""
        # Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        create_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 10}
        )
        product_id = create_response.json()["id"]
        
        # Try to delete as user
        response = client.delete(
            f'/Nike/products/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 403
    
    def test_pagination_works(self, client):
        """Product listing supports pagination"""
        # Create tenant and multiple products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        for i in range(15):
            client.post(
                '/Nike/products/',
                headers={"Authorization": "Bearer nike-admin-token"},
                json={"name": f"Product {i}", "price": 100.0, "available_quantity": 10}
            )
        
        # Get first page
        response = client.get('/Nike/products/?skip=0&limit=5')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Get second page
        response = client.get('/Nike/products/?skip=5&limit=5')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
