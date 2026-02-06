"""
Order Service - Business logic for order management.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from src.domain.entities.order import Order, OrderItem, OrderStatus
from src.domain.entities.inventory import InventoryItem
from src.infrastructure.repositories.order_repository import OrderRepository
from src.infrastructure.repositories.inventory_repository import InventoryRepository


class OrderService:
    """
    Service for order management business operations.
    
    Handles order lifecycle, validation, and inventory integration.
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        inventory_repository: InventoryRepository,
    ):
        """
        Initialize order service.
        
        Args:
            order_repository: Order data access
            inventory_repository: Inventory data access
        """
        self._order_repo = order_repository
        self._inventory_repo = inventory_repository
    
    async def create_order(
        self,
        organization_id: UUID,
        customer_name: str,
        customer_email: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> Order:
        """
        Create a new order.
        
        Args:
            organization_id: Organization context
            customer_name: Customer name
            customer_email: Optional customer email
            created_by: User creating the order
            
        Returns:
            Created order entity
        """
        order_number = await self._order_repo.generate_order_number(organization_id)
        
        order = Order(
            order_number=order_number,
            organization_id=organization_id,
            customer_name=customer_name,
            customer_email=customer_email,
            created_by=created_by,
            status=OrderStatus.DRAFT,
        )
        
        return await self._order_repo.add(order)
    
    async def add_item_to_order(
        self,
        order_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: Optional[Decimal] = None,
        discount_percent: Decimal = Decimal("0"),
    ) -> Order:
        """
        Add an item to an order.
        
        Args:
            order_id: Order to add item to
            product_id: Product ID
            quantity: Quantity to add
            unit_price: Override price (uses product price if not specified)
            discount_percent: Line item discount
            
        Returns:
            Updated order
            
        Raises:
            ValueError: If order not found or cannot be modified
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Get product details from inventory
        inventory_item = await self._inventory_repo.get_by_id(product_id)
        if not inventory_item:
            raise ValueError(f"Product {product_id} not found")
        
        # Check availability
        if inventory_item.quantity_available < quantity:
            raise ValueError(
                f"Insufficient stock for {inventory_item.name}. "
                f"Available: {inventory_item.quantity_available}"
            )
        
        # Create order item
        item = OrderItem(
            product_id=inventory_item.id,
            product_name=inventory_item.name,
            sku=inventory_item.sku,
            quantity=quantity,
            unit_price=unit_price or inventory_item.selling_price,
            discount_percent=discount_percent,
        )
        
        order.add_item(item)
        
        # Reserve inventory
        inventory_item.reserve_stock(quantity, order_id)
        await self._inventory_repo.update(inventory_item)
        
        return await self._order_repo.update(order)
    
    async def submit_order(self, order_id: UUID) -> Order:
        """
        Submit a draft order for processing.
        
        Args:
            order_id: Order to submit
            
        Returns:
            Updated order with PENDING status
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.submit()
        return await self._order_repo.update(order)
    
    async def confirm_order(self, order_id: UUID) -> Order:
        """
        Confirm a pending order.
        
        Args:
            order_id: Order to confirm
            
        Returns:
            Updated order with CONFIRMED status
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.confirm()
        return await self._order_repo.update(order)
    
    async def cancel_order(
        self,
        order_id: UUID,
        reason: Optional[str] = None,
    ) -> Order:
        """
        Cancel an order and release reserved inventory.
        
        Args:
            order_id: Order to cancel
            reason: Cancellation reason
            
        Returns:
            Cancelled order
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Release reserved inventory
        for item in order.items:
            inventory_item = await self._inventory_repo.get_by_id(item.product_id)
            if inventory_item:
                inventory_item.release_reservation(item.quantity)
                await self._inventory_repo.update(inventory_item)
        
        order.cancel(reason)
        return await self._order_repo.update(order)
    
    async def ship_order(
        self,
        order_id: UUID,
        tracking_number: Optional[str] = None,
    ) -> Order:
        """
        Mark order as shipped and commit inventory.
        
        Args:
            order_id: Order to ship
            tracking_number: Optional tracking number
            
        Returns:
            Updated order with SHIPPED status
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Commit inventory (convert reservation to actual sale)
        for item in order.items:
            inventory_item = await self._inventory_repo.get_by_id(item.product_id)
            if inventory_item:
                movement = inventory_item.sell_stock(item.quantity, order_id)
                await self._inventory_repo.add_stock_movement(movement)
                await self._inventory_repo.update(inventory_item)
        
        order.ship(tracking_number)
        return await self._order_repo.update(order)
    
    async def get_orders(
        self,
        organization_id: UUID,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """
        Get orders for an organization.
        
        Args:
            organization_id: Organization context
            status: Optional status filter
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of orders
        """
        return await self._order_repo.get_by_organization(
            organization_id=organization_id,
            status=status,
            skip=skip,
            limit=limit,
        )
    
    async def calculate_order_summary(self, order_id: UUID) -> dict:
        """
        Calculate order financial summary.
        
        Args:
            order_id: Order to summarize
            
        Returns:
            Summary with totals and breakdown
        """
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        return {
            "order_number": order.order_number,
            "status": order.status.value,
            "item_count": order.item_count,
            "subtotal": float(order.subtotal),
            "total_discount": float(order.total_discount),
            "total_tax": float(order.total_tax),
            "shipping_cost": float(order.shipping_cost),
            "handling_fee": float(order.handling_fee),
            "grand_total": float(order.grand_total),
            "currency": order.currency,
        }
