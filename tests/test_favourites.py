"""
Unit tests for Favourites Management
"""
import pytest


class TestFavourites:
    """Test favourite products functionality"""
    
    def test_user_add_favourite(self, client):
        """User can add product to favourites"""
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
        
        # Add to favourites
        response = client.post(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "added"
    
    def test_add_duplicate_favourite_fails(self, client):
        """Cannot add same product to favourites twice"""
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
        
        # Add to favourites first time
        client.post(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        
        # Try to add again
        response = client.post(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 400
    
    def test_add_nonexistent_product_to_favourites_fails(self, client):
        """Cannot add non-existent product to favourites"""
        response = client.post(
            '/users/me/favourites/99999',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 404
    
    def test_add_favourite_without_auth_fails(self, client):
        """Cannot add favourite without authentication"""
        response = client.post('/users/me/favourites/1')
        assert response.status_code == 401
    
    def test_list_user_favourites(self, client):
        """User can list their favourite products"""
        # Setup
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
            json={"name": "Air Jordan", "price": 180.0, "available_quantity": 30}
        ).json()
        
        # Add to favourites
        client.post(
            f'/users/me/favourites/{product1["id"]}',
            headers={"Authorization": "Bearer user-token"}
        )
        client.post(
            f'/users/me/favourites/{product2["id"]}',
            headers={"Authorization": "Bearer user-token"}
        )
        
        # List favourites
        response = client.get(
            '/users/me/favourites',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        product_ids = [p["id"] for p in data]
        assert product1["id"] in product_ids
        assert product2["id"] in product_ids
    
    def test_user_only_sees_own_favourites(self, client):
        """User can only see their own favourites"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        product = client.post(
            '/Nike/products/',
            headers={"Authorization": "Bearer nike-admin-token"},
            json={"name": "Air Max", "price": 120.0, "available_quantity": 50}
        ).json()
        
        # User 1 adds favourite
        client.post(
            f'/users/me/favourites/{product["id"]}',
            headers={"Authorization": "Bearer user-token"}
        )
        
        # User 2 lists favourites - should be empty
        response = client.get(
            '/users/me/favourites',
            headers={"Authorization": "Bearer user2-token"}
        )
        assert response.status_code == 200
        data = response.json()
        # User 2 should have no favourites (or not include user 1's favourite)
        assert product["id"] not in [p["id"] for p in data]
    
    def test_remove_favourite(self, client):
        """User can remove product from favourites"""
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
        
        # Add to favourites
        client.post(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        
        # Remove from favourites
        response = client.delete(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "removed"
    
    def test_remove_non_favourited_product_fails(self, client):
        """Cannot remove product that's not in favourites"""
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
        
        # Try to remove without adding first
        response = client.delete(
            f'/users/me/favourites/{product_id}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 404
    
    def test_remove_favourite_without_auth_fails(self, client):
        """Cannot remove favourite without authentication"""
        response = client.delete('/users/me/favourites/1')
        assert response.status_code == 401
    
    def test_favourites_pagination(self, client):
        """Favourites listing supports pagination"""
        # Setup
        client.post(
            '/tenants/',
            headers={"Authorization": "Bearer platform-admin-token"},
            json={"name": "Nike"}
        )
        
        # Create multiple products and add to favourites
        for i in range(15):
            product = client.post(
                '/Nike/products/',
                headers={"Authorization": "Bearer nike-admin-token"},
                json={"name": f"Product {i}", "price": 100.0, "available_quantity": 10}
            ).json()
            client.post(
                f'/users/me/favourites/{product["id"]}',
                headers={"Authorization": "Bearer user-token"}
            )
        
        # Get first page
        response = client.get(
            '/users/me/favourites?skip=0&limit=5',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Get second page
        response = client.get(
            '/users/me/favourites?skip=5&limit=5',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_user_can_favourite_from_any_tenant(self, client):
        """User can favourite products from any tenant"""
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
        
        # User favourites from both tenants
        response1 = client.post(
            f'/users/me/favourites/{nike_product["id"]}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f'/users/me/favourites/{adidas_product["id"]}',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response2.status_code == 200
        
        # List all favourites
        response = client.get(
            '/users/me/favourites',
            headers={"Authorization": "Bearer user-token"}
        )
        assert response.status_code == 200
        data = response.json()
        product_ids = [p["id"] for p in data]
        assert nike_product["id"] in product_ids
        assert adidas_product["id"] in product_ids
