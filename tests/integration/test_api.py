"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_readiness_probe(self, client):
        """Test readiness probe endpoint."""
        response = client.get("/ready")
        
        assert response.status_code == 200
        assert response.json()["ready"] is True
    
    def test_liveness_probe(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/live")
        
        assert response.status_code == 200
        assert response.json()["alive"] is True


class TestUserEndpoints:
    """Tests for user management endpoints."""
    
    def test_create_user(self, client):
        """Test user creation endpoint."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": f"test_{id(self)}@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User",
                "role": "viewer"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"].endswith("@example.com")
        assert data["full_name"] == "Test User"
        assert data["role"] == "viewer"
    
    def test_list_users(self, client):
        """Test user listing endpoint."""
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestOrderEndpoints:
    """Tests for order management endpoints."""
    
    def test_create_order(self, client):
        """Test order creation endpoint."""
        response = client.post(
            "/api/v1/orders/",
            json={
                "customer_name": "John Doe",
                "customer_email": "john@example.com"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "John Doe"
        assert data["status"] == "draft"
        assert "order_number" in data
    
    def test_list_orders(self, client):
        """Test order listing endpoint."""
        response = client.get("/api/v1/orders/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestInventoryEndpoints:
    """Tests for inventory management endpoints."""
    
    def test_create_inventory_item(self, client):
        """Test inventory item creation endpoint."""
        response = client.post(
            "/api/v1/inventory/",
            json={
                "sku": f"SKU-{id(self)}",
                "name": "Test Product",
                "description": "A test product",
                "selling_price": 29.99,
                "quantity_on_hand": 100
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["quantity_on_hand"] == 100
    
    def test_list_inventory(self, client):
        """Test inventory listing endpoint."""
        response = client.get("/api/v1/inventory/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_low_stock(self, client):
        """Test low stock items endpoint."""
        response = client.get("/api/v1/inventory/low-stock")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
