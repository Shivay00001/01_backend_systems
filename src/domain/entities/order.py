"""
Order Entity - Sales order domain model.

Implements the Order aggregate with line items and business rules
for order processing.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class OrderStatus(str, Enum):
    """Order lifecycle statuses."""
    
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    
    @property
    def can_modify(self) -> bool:
        """Check if order can be modified in this status."""
        return self in {OrderStatus.DRAFT, OrderStatus.PENDING}
    
    @property
    def can_cancel(self) -> bool:
        """Check if order can be cancelled in this status."""
        return self in {
            OrderStatus.DRAFT,
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
        }


class OrderItem(BaseModel):
    """
    Order Line Item - Represents a single item in an order.
    
    This is a value object within the Order aggregate.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Line item identifier")
    product_id: UUID = Field(..., description="Reference to product")
    product_name: str = Field(..., description="Product name at time of order")
    sku: str = Field(..., description="Product SKU")
    
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_percent: Decimal = Field(default=Decimal("0"), ge=0)
    
    notes: Optional[str] = Field(None, description="Line item notes")
    
    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Calculate line item subtotal before discount and tax."""
        return self.unit_price * self.quantity
    
    @computed_field
    @property
    def discount_amount(self) -> Decimal:
        """Calculate discount amount."""
        return self.subtotal * (self.discount_percent / 100)
    
    @computed_field
    @property
    def taxable_amount(self) -> Decimal:
        """Calculate amount after discount."""
        return self.subtotal - self.discount_amount
    
    @computed_field
    @property
    def tax_amount(self) -> Decimal:
        """Calculate tax amount."""
        return self.taxable_amount * (self.tax_percent / 100)
    
    @computed_field
    @property
    def total(self) -> Decimal:
        """Calculate line item total including tax."""
        return self.taxable_amount + self.tax_amount


class Order(BaseModel):
    """
    Order Entity - Represents a sales order.
    
    This is an aggregate root managing order items and order lifecycle.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique order identifier")
    order_number: str = Field(..., description="Human-readable order number")
    organization_id: UUID = Field(..., description="Organization this order belongs to")
    
    # Customer information
    customer_id: Optional[UUID] = Field(None, description="Customer reference")
    customer_name: str = Field(..., description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    
    # Addresses
    billing_address: Optional[str] = Field(None, description="Billing address")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    
    # Order details
    items: List[OrderItem] = Field(default_factory=list, description="Order line items")
    status: OrderStatus = Field(default=OrderStatus.DRAFT, description="Order status")
    currency: str = Field(default="USD", description="Order currency")
    
    # Additional charges
    shipping_cost: Decimal = Field(default=Decimal("0"), ge=0)
    handling_fee: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Notes
    internal_notes: Optional[str] = Field(None, description="Internal notes")
    customer_notes: Optional[str] = Field(None, description="Customer-facing notes")
    
    # Audit fields
    created_by: Optional[UUID] = Field(None, description="User who created the order")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = Field(None)
    shipped_at: Optional[datetime] = Field(None)
    delivered_at: Optional[datetime] = Field(None)
    
    model_config = {
        "from_attributes": True,
    }
    
    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Calculate order subtotal from all items."""
        return sum(item.subtotal for item in self.items)
    
    @computed_field
    @property
    def total_discount(self) -> Decimal:
        """Calculate total discount across all items."""
        return sum(item.discount_amount for item in self.items)
    
    @computed_field
    @property
    def total_tax(self) -> Decimal:
        """Calculate total tax across all items."""
        return sum(item.tax_amount for item in self.items)
    
    @computed_field
    @property
    def grand_total(self) -> Decimal:
        """Calculate order grand total."""
        items_total = sum(item.total for item in self.items)
        return items_total + self.shipping_cost + self.handling_fee
    
    @computed_field
    @property
    def item_count(self) -> int:
        """Get total number of items."""
        return sum(item.quantity for item in self.items)
    
    def add_item(self, item: OrderItem) -> None:
        """
        Add an item to the order.
        
        Args:
            item: The order item to add
            
        Raises:
            ValueError: If order cannot be modified
        """
        if not self.status.can_modify:
            raise ValueError(f"Cannot add items to order in {self.status} status")
        
        self.items.append(item)
        self.updated_at = datetime.utcnow()
    
    def remove_item(self, item_id: UUID) -> None:
        """
        Remove an item from the order.
        
        Args:
            item_id: ID of the item to remove
            
        Raises:
            ValueError: If order cannot be modified or item not found
        """
        if not self.status.can_modify:
            raise ValueError(f"Cannot remove items from order in {self.status} status")
        
        original_count = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        
        if len(self.items) == original_count:
            raise ValueError(f"Item {item_id} not found in order")
        
        self.updated_at = datetime.utcnow()
    
    def confirm(self) -> None:
        """
        Confirm the order for processing.
        
        Raises:
            ValueError: If order cannot be confirmed
        """
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status} status")
        
        if not self.items:
            raise ValueError("Cannot confirm empty order")
        
        self.status = OrderStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def submit(self) -> None:
        """
        Submit draft order for review/confirmation.
        
        Raises:
            ValueError: If order cannot be submitted
        """
        if self.status != OrderStatus.DRAFT:
            raise ValueError(f"Cannot submit order in {self.status} status")
        
        if not self.items:
            raise ValueError("Cannot submit empty order")
        
        self.status = OrderStatus.PENDING
        self.updated_at = datetime.utcnow()
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the order.
        
        Args:
            reason: Optional cancellation reason
            
        Raises:
            ValueError: If order cannot be cancelled
        """
        if not self.status.can_cancel:
            raise ValueError(f"Cannot cancel order in {self.status} status")
        
        self.status = OrderStatus.CANCELLED
        if reason:
            self.internal_notes = f"{self.internal_notes or ''}\nCancelled: {reason}".strip()
        self.updated_at = datetime.utcnow()
    
    def ship(self, tracking_number: Optional[str] = None) -> None:
        """
        Mark order as shipped.
        
        Args:
            tracking_number: Optional tracking number
            
        Raises:
            ValueError: If order cannot be shipped
        """
        if self.status not in {OrderStatus.CONFIRMED, OrderStatus.PROCESSING}:
            raise ValueError(f"Cannot ship order in {self.status} status")
        
        self.status = OrderStatus.SHIPPED
        self.shipped_at = datetime.utcnow()
        if tracking_number:
            self.internal_notes = f"{self.internal_notes or ''}\nTracking: {tracking_number}".strip()
        self.updated_at = datetime.utcnow()
    
    def deliver(self) -> None:
        """
        Mark order as delivered.
        
        Raises:
            ValueError: If order cannot be marked as delivered
        """
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(f"Cannot deliver order in {self.status} status")
        
        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
