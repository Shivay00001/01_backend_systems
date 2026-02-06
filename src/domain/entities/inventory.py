"""
Inventory Entity - Product and stock management domain model.

Implements inventory management with stock movements and tracking.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StockMovementType(str, Enum):
    """Types of stock movements."""
    
    PURCHASE = "purchase"       # Stock received from supplier
    SALE = "sale"              # Stock sold to customer
    ADJUSTMENT = "adjustment"   # Manual adjustment
    TRANSFER = "transfer"       # Transfer between locations
    RETURN = "return"          # Customer return
    DAMAGE = "damage"          # Damaged goods
    EXPIRED = "expired"        # Expired goods


class InventoryItem(BaseModel):
    """
    Inventory Item Entity - Represents a product in inventory.
    
    This is an aggregate root for inventory management.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique item identifier")
    organization_id: UUID = Field(..., description="Organization this item belongs to")
    
    # Product identification
    sku: str = Field(..., min_length=1, max_length=100, description="Stock keeping unit")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    barcode: Optional[str] = Field(None, description="Barcode/UPC")
    
    # Categorization
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    
    # Pricing
    cost_price: Decimal = Field(default=Decimal("0"), ge=0, description="Cost price")
    selling_price: Decimal = Field(default=Decimal("0"), ge=0, description="Selling price")
    currency: str = Field(default="USD", description="Currency")
    
    # Stock levels
    quantity_on_hand: int = Field(default=0, ge=0, description="Current stock")
    quantity_reserved: int = Field(default=0, ge=0, description="Reserved for orders")
    quantity_on_order: int = Field(default=0, ge=0, description="On order from suppliers")
    reorder_point: int = Field(default=10, ge=0, description="Reorder threshold")
    reorder_quantity: int = Field(default=50, ge=0, description="Default reorder quantity")
    
    # Physical attributes
    weight: Optional[Decimal] = Field(None, description="Weight in kg")
    dimensions: Optional[str] = Field(None, description="Dimensions (LxWxH)")
    
    # Status
    is_active: bool = Field(default=True, description="Whether item is active")
    is_trackable: bool = Field(default=True, description="Whether to track inventory")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "from_attributes": True,
    }
    
    @property
    def quantity_available(self) -> int:
        """Calculate available stock (on hand minus reserved)."""
        return max(0, self.quantity_on_hand - self.quantity_reserved)
    
    @property
    def needs_reorder(self) -> bool:
        """Check if item needs reordering."""
        return self.quantity_available <= self.reorder_point
    
    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.cost_price == 0:
            return Decimal("100")
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100
    
    def receive_stock(self, quantity: int, reference: Optional[str] = None) -> "StockMovement":
        """
        Receive stock from a purchase.
        
        Args:
            quantity: Quantity received
            reference: Optional reference (PO number, etc.)
            
        Returns:
            StockMovement: The created movement record
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        self.quantity_on_hand += quantity
        self.updated_at = datetime.utcnow()
        
        return StockMovement(
            inventory_item_id=self.id,
            movement_type=StockMovementType.PURCHASE,
            quantity=quantity,
            reference=reference,
            quantity_after=self.quantity_on_hand,
        )
    
    def reserve_stock(self, quantity: int, order_id: Optional[UUID] = None) -> None:
        """
        Reserve stock for an order.
        
        Args:
            quantity: Quantity to reserve
            order_id: Optional order reference
            
        Raises:
            ValueError: If insufficient stock available
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if quantity > self.quantity_available:
            raise ValueError(
                f"Insufficient stock. Available: {self.quantity_available}, Requested: {quantity}"
            )
        
        self.quantity_reserved += quantity
        self.updated_at = datetime.utcnow()
    
    def release_reservation(self, quantity: int) -> None:
        """
        Release reserved stock.
        
        Args:
            quantity: Quantity to release
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        self.quantity_reserved = max(0, self.quantity_reserved - quantity)
        self.updated_at = datetime.utcnow()
    
    def sell_stock(self, quantity: int, order_id: Optional[UUID] = None) -> "StockMovement":
        """
        Record a sale, reducing stock.
        
        Args:
            quantity: Quantity sold
            order_id: Optional order reference
            
        Returns:
            StockMovement: The created movement record
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if quantity > self.quantity_on_hand:
            raise ValueError(
                f"Insufficient stock. On hand: {self.quantity_on_hand}, Requested: {quantity}"
            )
        
        self.quantity_on_hand -= quantity
        # Also reduce reservation if applicable
        if self.quantity_reserved > 0:
            self.quantity_reserved = max(0, self.quantity_reserved - quantity)
        
        self.updated_at = datetime.utcnow()
        
        return StockMovement(
            inventory_item_id=self.id,
            movement_type=StockMovementType.SALE,
            quantity=-quantity,
            reference=str(order_id) if order_id else None,
            quantity_after=self.quantity_on_hand,
        )
    
    def adjust_stock(
        self,
        quantity: int,
        reason: str,
        movement_type: StockMovementType = StockMovementType.ADJUSTMENT,
    ) -> "StockMovement":
        """
        Adjust stock level manually.
        
        Args:
            quantity: Adjustment amount (positive or negative)
            reason: Reason for adjustment
            movement_type: Type of movement
            
        Returns:
            StockMovement: The created movement record
        """
        new_quantity = self.quantity_on_hand + quantity
        if new_quantity < 0:
            raise ValueError(
                f"Adjustment would result in negative stock: {new_quantity}"
            )
        
        self.quantity_on_hand = new_quantity
        self.updated_at = datetime.utcnow()
        
        return StockMovement(
            inventory_item_id=self.id,
            movement_type=movement_type,
            quantity=quantity,
            reference=reason,
            quantity_after=self.quantity_on_hand,
        )


class StockMovement(BaseModel):
    """
    Stock Movement Entity - Records inventory changes.
    
    Provides audit trail for all stock movements.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Movement identifier")
    inventory_item_id: UUID = Field(..., description="Related inventory item")
    
    movement_type: StockMovementType = Field(..., description="Type of movement")
    quantity: int = Field(..., description="Quantity (positive for in, negative for out)")
    quantity_after: int = Field(..., ge=0, description="Stock after movement")
    
    reference: Optional[str] = Field(None, description="Reference (PO, SO, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Audit
    created_by: Optional[UUID] = Field(None, description="User who created the movement")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "from_attributes": True,
    }
