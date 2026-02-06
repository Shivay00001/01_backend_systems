"""
Unit tests for domain entities.
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.user import User, UserRole
from src.domain.entities.order import Order, OrderItem, OrderStatus
from src.domain.entities.inventory import InventoryItem, StockMovementType
from src.domain.entities.organization import Organization, OrganizationPlan


class TestUser:
    """Tests for User entity."""
    
    def test_create_user(self):
        """Test user creation with default values."""
        user = User(
            email="test@example.com",
            hashed_password="hashed123",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.role == UserRole.VIEWER
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_has_permission(self):
        """Test permission checking based on role."""
        admin = User(
            email="admin@example.com",
            hashed_password="hashed",
            full_name="Admin",
            role=UserRole.ADMIN
        )
        viewer = User(
            email="viewer@example.com",
            hashed_password="hashed",
            full_name="Viewer",
            role=UserRole.VIEWER
        )
        
        assert admin.has_permission("write") is True
        assert admin.has_permission("manage_users") is True
        assert viewer.has_permission("read") is True
        assert viewer.has_permission("write") is False
    
    def test_user_deactivation(self):
        """Test deactivated user loses permissions."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test",
            role=UserRole.ADMIN
        )
        
        assert user.has_permission("write") is True
        user.deactivate()
        assert user.is_active is False
        assert user.has_permission("write") is False
    
    def test_failed_login_tracking(self):
        """Test failed login attempt tracking."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test"
        )
        
        for _ in range(4):
            user.record_failed_login()
        
        assert user.failed_login_attempts == 4
        assert user.is_locked() is False
        
        user.record_failed_login()  # 5th attempt
        assert user.is_locked() is True


class TestOrder:
    """Tests for Order entity."""
    
    def test_create_order(self):
        """Test order creation."""
        org_id = uuid4()
        order = Order(
            order_number="ORD-001",
            organization_id=org_id,
            customer_name="John Doe"
        )
        
        assert order.status == OrderStatus.DRAFT
        assert order.items == []
        assert order.grand_total == Decimal("0")
    
    def test_add_item_to_order(self):
        """Test adding items to order."""
        order = Order(
            order_number="ORD-001",
            organization_id=uuid4(),
            customer_name="John Doe"
        )
        
        item = OrderItem(
            product_id=uuid4(),
            product_name="Widget",
            sku="WDG-001",
            quantity=2,
            unit_price=Decimal("25.00")
        )
        
        order.add_item(item)
        
        assert len(order.items) == 1
        assert order.subtotal == Decimal("50.00")
    
    def test_order_status_transitions(self):
        """Test valid status transitions."""
        order = Order(
            order_number="ORD-001",
            organization_id=uuid4(),
            customer_name="John Doe",
            items=[
                OrderItem(
                    product_id=uuid4(),
                    product_name="Widget",
                    sku="WDG-001",
                    quantity=1,
                    unit_price=Decimal("10.00")
                )
            ]
        )
        
        assert order.status == OrderStatus.DRAFT
        order.submit()
        assert order.status == OrderStatus.PENDING
        order.confirm()
        assert order.status == OrderStatus.CONFIRMED
    
    def test_cannot_modify_confirmed_order(self):
        """Test that confirmed orders cannot be modified."""
        order = Order(
            order_number="ORD-001",
            organization_id=uuid4(),
            customer_name="John Doe",
            status=OrderStatus.CONFIRMED,
            items=[]
        )
        
        item = OrderItem(
            product_id=uuid4(),
            product_name="Widget",
            sku="WDG-001",
            quantity=1,
            unit_price=Decimal("10.00")
        )
        
        with pytest.raises(ValueError, match="Cannot add items"):
            order.add_item(item)


class TestInventoryItem:
    """Tests for InventoryItem entity."""
    
    def test_create_inventory_item(self):
        """Test inventory item creation."""
        item = InventoryItem(
            organization_id=uuid4(),
            sku="SKU-001",
            name="Test Product",
            quantity_on_hand=100,
            selling_price=Decimal("19.99")
        )
        
        assert item.quantity_available == 100
        assert item.needs_reorder is False
    
    def test_reserve_stock(self):
        """Test stock reservation."""
        item = InventoryItem(
            organization_id=uuid4(),
            sku="SKU-001",
            name="Test Product",
            quantity_on_hand=100
        )
        
        item.reserve_stock(20)
        
        assert item.quantity_reserved == 20
        assert item.quantity_available == 80
    
    def test_insufficient_stock_reservation(self):
        """Test reservation fails with insufficient stock."""
        item = InventoryItem(
            organization_id=uuid4(),
            sku="SKU-001",
            name="Test Product",
            quantity_on_hand=10
        )
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            item.reserve_stock(20)
    
    def test_receive_stock_creates_movement(self):
        """Test receiving stock creates movement record."""
        item = InventoryItem(
            organization_id=uuid4(),
            sku="SKU-001",
            name="Test Product",
            quantity_on_hand=50
        )
        
        movement = item.receive_stock(25, "PO-123")
        
        assert item.quantity_on_hand == 75
        assert movement.quantity == 25
        assert movement.movement_type == StockMovementType.PURCHASE
        assert movement.quantity_after == 75
    
    def test_low_stock_detection(self):
        """Test low stock detection based on reorder point."""
        item = InventoryItem(
            organization_id=uuid4(),
            sku="SKU-001",
            name="Test Product",
            quantity_on_hand=5,
            reorder_point=10
        )
        
        assert item.needs_reorder is True


class TestOrganization:
    """Tests for Organization entity."""
    
    def test_create_organization(self):
        """Test organization creation."""
        org = Organization(
            name="Test Corp",
            slug="test-corp"
        )
        
        assert org.plan == OrganizationPlan.FREE
        assert org.is_active is True
    
    def test_feature_access_by_plan(self):
        """Test feature access based on plan."""
        free_org = Organization(name="Free Org", slug="free", plan=OrganizationPlan.FREE)
        pro_org = Organization(name="Pro Org", slug="pro", plan=OrganizationPlan.PROFESSIONAL)
        
        assert free_org.has_feature("dashboard") is True
        assert free_org.has_feature("api") is False
        assert pro_org.has_feature("api") is True
    
    def test_user_limits_by_plan(self):
        """Test user limits based on plan."""
        free_org = Organization(name="Free Org", slug="free", plan=OrganizationPlan.FREE)
        
        assert free_org.can_add_user(2) is True
        assert free_org.can_add_user(3) is False  # Free plan allows 3 users max
