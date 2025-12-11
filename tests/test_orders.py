"""
Unit tests for Order Management
"""
import pytest


class TestOrderManagement:
    """Test order creation and management"""
    
    def test_user_create_order(self, client):
        """User can create an order"""
        # Setup: Create tenant and product
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={
                "name": "Air Max",
                "price": 120.0,
                "available_quantity": 50
            }
        )
        product_id = product_response.json()["id"]
        
        # Create order
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [
                    {"product_id": product_id, "quantity": 2}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_quantity"] == 2
        assert data["total_amount"] == 240.0  # 2 * 120.0
        assert len(data["items"]) == 1
    
    def test_create_order_with_multiple_items(self, client):
        """User can create order with multiple products"""
        # Setup: Create tenant and products
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product1 = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        ).json()
        product2 = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Hoodie", "price": 60.0, "available_quantity": 30}
        ).json()
        
        # Create order with multiple items
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [
                    {"product_id": product1["id"], "quantity": 2},
                    {"product_id": product2["id"], "quantity": 1}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_quantity"] == 3
        assert data["total_amount"] == 300.0  # (2*120) + (1*60)
        assert len(data["items"]) == 2
    
    def test_order_reduces_stock(self, client):
        """Creating order reduces product stock"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        )
        product_id = product_response.json()["id"]
        
        # Create order
        client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [{"product_id": product_id, "quantity": 5}]
            }
        )
        
        # Check stock reduced
        product_after = client.get(f'/Nike/products/{product_id}').json()
        assert product_after["available_quantity"] == 45  # 50 - 5
    
    def test_order_insufficient_stock_fails(self, client):
        """Cannot order more than available quantity"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 5}
        )
        product_id = product_response.json()["id"]
        
        # Try to order more than available
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [{"product_id": product_id, "quantity": 10}]
            }
        )
        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()
    
    def test_order_with_zero_quantity_fails(self, client):
        """Cannot order with zero quantity"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        )
        product_id = product_response.json()["id"]
        
        # Try to order with zero quantity
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [{"product_id": product_id, "quantity": 0}]
            }
        )
        assert response.status_code in [400, 422]  # Validation error
    
    def test_order_with_negative_quantity_fails(self, client):
        """Cannot order with negative quantity"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        )
        product_id = product_response.json()["id"]
        
        # Try to order with negative quantity
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [{"product_id": product_id, "quantity": -1}]
            }
        )
        assert response.status_code in [400, 422]
    
    def test_order_nonexistent_product_fails(self, client):
        """Cannot order non-existent product"""
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [{"product_id": 99999, "quantity": 1}]
            }
        )
        assert response.status_code == 404
    
    def test_order_empty_items_fails(self, client):
        """Cannot create order with no items"""
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={"items": []}
        )
        assert response.status_code in [400, 422]
    
    def test_order_without_auth_fails(self, client):
        """Cannot create order without authentication"""
        response = client.post(
            '/orders/',
            json={
                "items": [{"product_id": 1, "quantity": 1}]
            }
        )
        assert response.status_code == 401
    
    def test_list_user_orders(self, client):
        """User can list their orders"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        )
        product_id = product_response.json()["id"]
        
        # Create orders
        client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={"items": [{"product_id": product_id, "quantity": 1}]}
        )
        client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={"items": [{"product_id": product_id, "quantity": 2}]}
        )
        
        # List orders
        response = client.get(
            '/orders/',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_user_only_sees_own_orders(self, client):
        """User can only see their own orders"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        )
        product_id = product_response.json()["id"]
        
        # User 1 creates order
        client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={"items": [{"product_id": product_id, "quantity": 1}]}
        )
        
        # User 2 creates order
        client.post(
            '/orders/',
            headers={"Authorization": "Bearer user2-token"},
            json={"items": [{"product_id": product_id, "quantity": 2}]}
        )
        
        # User 1 lists orders - should only see their own
        response = client.get(
            '/orders/',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        # All orders should belong to user-token user
        assert all(order["user_id"] == data[0]["user_id"] for order in data)
    
    def test_order_pagination(self, client):
        """Order listing supports pagination"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product_response = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 100}
        )
        product_id = product_response.json()["id"]
        
        # Create multiple orders
        for _ in range(15):
            client.post(
                '/orders/',
                headers={"Authorization": "Bearer user-token"},
                json={"items": [{"product_id": product_id, "quantity": 1}]}
            )
        
        # Get first page
        response = client.get(
            '/orders/?skip=0&limit=5',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Get second page
        response = client.get(
            '/orders/?skip=5&limit=5',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_user_can_order_from_any_tenant(self, client):
        """User can order products from any tenant"""
        # Create two tenants with products
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
        
        nike_product = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Nike Shoe", "price": 120.0, "available_quantity": 50}
        ).json()
        
        adidas_product = client.post(
            '/Adidas/products/',
            headers={"Authorization": "Bearer adidas-admin-token"},
            json={"name": "Adidas Shoe", "price": 110.0, "available_quantity": 40}
        ).json()
        
        # User orders from both tenants in one order
        response = client.post(
            '/orders/',
            headers={"Authorization": "Bearer user-token"},
            json={
                "items": [
                    {"product_id": nike_product["id"], "quantity": 1},
                    {"product_id": adidas_product["id"], "quantity": 1}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_amount"] == 230.0  # 120 + 110
