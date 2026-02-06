"""
Inventory Repository - Data access for inventory entities.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.inventory import InventoryItem, StockMovement, StockMovementType
from src.infrastructure.database.models import InventoryItemModel, StockMovementModel
from src.infrastructure.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[InventoryItemModel, InventoryItem]):
    """Repository for InventoryItem entity data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, InventoryItemModel)
    
    def _to_entity(self, model: InventoryItemModel) -> InventoryItem:
        """Convert InventoryItemModel to InventoryItem entity."""
        return InventoryItem(
            id=UUID(model.id),
            organization_id=UUID(model.organization_id),
            sku=model.sku,
            name=model.name,
            description=model.description,
            barcode=model.barcode,
            category=model.category,
            brand=model.brand,
            tags=[],  # Tags stored separately if needed
            cost_price=model.cost_price,
            selling_price=model.selling_price,
            currency=model.currency,
            quantity_on_hand=model.quantity_on_hand,
            quantity_reserved=model.quantity_reserved,
            quantity_on_order=model.quantity_on_order,
            reorder_point=model.reorder_point,
            reorder_quantity=model.reorder_quantity,
            weight=model.weight,
            dimensions=model.dimensions,
            is_active=model.is_active,
            is_trackable=model.is_trackable,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _to_model(self, entity: InventoryItem) -> InventoryItemModel:
        """Convert InventoryItem entity to InventoryItemModel."""
        return InventoryItemModel(
            id=str(entity.id),
            organization_id=str(entity.organization_id),
            sku=entity.sku,
            name=entity.name,
            description=entity.description,
            barcode=entity.barcode,
            category=entity.category,
            brand=entity.brand,
            cost_price=entity.cost_price,
            selling_price=entity.selling_price,
            currency=entity.currency,
            quantity_on_hand=entity.quantity_on_hand,
            quantity_reserved=entity.quantity_reserved,
            quantity_on_order=entity.quantity_on_order,
            reorder_point=entity.reorder_point,
            reorder_quantity=entity.reorder_quantity,
            weight=entity.weight,
            dimensions=entity.dimensions,
            is_active=entity.is_active,
            is_trackable=entity.is_trackable,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
    
    async def get_by_sku(
        self,
        sku: str,
        organization_id: UUID,
    ) -> Optional[InventoryItem]:
        """Get inventory item by SKU within organization."""
        query = select(InventoryItemModel).where(
            and_(
                InventoryItemModel.sku == sku,
                InventoryItemModel.organization_id == str(organization_id),
            )
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_barcode(
        self,
        barcode: str,
        organization_id: UUID,
    ) -> Optional[InventoryItem]:
        """Get inventory item by barcode."""
        query = select(InventoryItemModel).where(
            and_(
                InventoryItemModel.barcode == barcode,
                InventoryItemModel.organization_id == str(organization_id),
            )
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_organization(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InventoryItem]:
        """Get inventory items for an organization."""
        conditions = [InventoryItemModel.organization_id == str(organization_id)]
        
        if active_only:
            conditions.append(InventoryItemModel.is_active == True)
        if category:
            conditions.append(InventoryItemModel.category == category)
        
        query = (
            select(InventoryItemModel)
            .where(and_(*conditions))
            .order_by(InventoryItemModel.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_low_stock_items(
        self,
        organization_id: UUID,
    ) -> List[InventoryItem]:
        """Get items below reorder point."""
        query = select(InventoryItemModel).where(
            and_(
                InventoryItemModel.organization_id == str(organization_id),
                InventoryItemModel.is_active == True,
                InventoryItemModel.is_trackable == True,
                InventoryItemModel.quantity_on_hand <= InventoryItemModel.reorder_point,
            )
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def search(
        self,
        organization_id: UUID,
        query_text: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InventoryItem]:
        """Search inventory items by name, SKU, or description."""
        search_pattern = f"%{query_text}%"
        query = (
            select(InventoryItemModel)
            .where(
                and_(
                    InventoryItemModel.organization_id == str(organization_id),
                    or_(
                        InventoryItemModel.name.ilike(search_pattern),
                        InventoryItemModel.sku.ilike(search_pattern),
                        InventoryItemModel.description.ilike(search_pattern),
                    )
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def add_stock_movement(self, movement: StockMovement) -> StockMovement:
        """Record a stock movement."""
        model = StockMovementModel(
            id=str(movement.id),
            inventory_item_id=str(movement.inventory_item_id),
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            quantity_after=movement.quantity_after,
            reference=movement.reference,
            notes=movement.notes,
            created_by_id=str(movement.created_by) if movement.created_by else None,
            created_at=movement.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return movement
    
    async def get_stock_movements(
        self,
        inventory_item_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StockMovement]:
        """Get stock movements for an item."""
        query = (
            select(StockMovementModel)
            .where(StockMovementModel.inventory_item_id == str(inventory_item_id))
            .order_by(StockMovementModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        return [
            StockMovement(
                id=UUID(m.id),
                inventory_item_id=UUID(m.inventory_item_id),
                movement_type=m.movement_type,
                quantity=m.quantity,
                quantity_after=m.quantity_after,
                reference=m.reference,
                notes=m.notes,
                created_by=UUID(m.created_by_id) if m.created_by_id else None,
                created_at=m.created_at,
            )
            for m in models
        ]
