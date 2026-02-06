"""
Order Repository - Data access for order entities.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.order import Order, OrderItem, OrderStatus
from src.infrastructure.database.models import OrderModel, OrderItemModel
from src.infrastructure.repositories.base import BaseRepository


class OrderRepository(BaseRepository[OrderModel, Order]):
    """Repository for Order entity data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrderModel)
    
    def _to_entity(self, model: OrderModel) -> Order:
        """Convert OrderModel to Order entity."""
        items = [
            OrderItem(
                id=UUID(item.id),
                product_id=UUID(item.product_id),
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                tax_percent=item.tax_percent,
                notes=item.notes,
            )
            for item in model.items
        ] if model.items else []
        
        return Order(
            id=UUID(model.id),
            order_number=model.order_number,
            organization_id=UUID(model.organization_id),
            customer_id=UUID(model.customer_id) if model.customer_id else None,
            customer_name=model.customer_name,
            customer_email=model.customer_email,
            billing_address=model.billing_address,
            shipping_address=model.shipping_address,
            items=items,
            status=model.status,
            currency=model.currency,
            shipping_cost=model.shipping_cost,
            handling_fee=model.handling_fee,
            internal_notes=model.internal_notes,
            customer_notes=model.customer_notes,
            created_by=UUID(model.created_by_id) if model.created_by_id else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
            confirmed_at=model.confirmed_at,
            shipped_at=model.shipped_at,
            delivered_at=model.delivered_at,
        )
    
    def _to_model(self, entity: Order) -> OrderModel:
        """Convert Order entity to OrderModel."""
        model = OrderModel(
            id=str(entity.id),
            order_number=entity.order_number,
            organization_id=str(entity.organization_id),
            customer_id=str(entity.customer_id) if entity.customer_id else None,
            customer_name=entity.customer_name,
            customer_email=entity.customer_email,
            billing_address=entity.billing_address,
            shipping_address=entity.shipping_address,
            status=entity.status,
            currency=entity.currency,
            shipping_cost=entity.shipping_cost,
            handling_fee=entity.handling_fee,
            internal_notes=entity.internal_notes,
            customer_notes=entity.customer_notes,
            created_by_id=str(entity.created_by) if entity.created_by else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            confirmed_at=entity.confirmed_at,
            shipped_at=entity.shipped_at,
            delivered_at=entity.delivered_at,
        )
        
        model.items = [
            OrderItemModel(
                id=str(item.id),
                order_id=str(entity.id),
                product_id=str(item.product_id),
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                tax_percent=item.tax_percent,
                notes=item.notes,
            )
            for item in entity.items
        ]
        
        return model
    
    async def get_by_id(self, id: UUID | str) -> Optional[Order]:
        """Get order by ID with items eagerly loaded."""
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == str(id))
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.order_number == order_number)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_organization(
        self,
        organization_id: UUID,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get orders for an organization with optional status filter."""
        conditions = [OrderModel.organization_id == str(organization_id)]
        if status:
            conditions.append(OrderModel.status == status)
        
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(and_(*conditions))
            .order_by(OrderModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_by_customer(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get orders for a specific customer."""
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.customer_id == str(customer_id))
            .order_by(OrderModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_by_date_range(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Order]:
        """Get orders within a date range."""
        query = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(
                and_(
                    OrderModel.organization_id == str(organization_id),
                    OrderModel.created_at >= start_date,
                    OrderModel.created_at <= end_date,
                )
            )
            .order_by(OrderModel.created_at.desc())
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def generate_order_number(self, organization_id: UUID) -> str:
        """Generate a unique order number for the organization."""
        from sqlalchemy import func
        
        # Get count of orders for this org to generate sequential number
        query = (
            select(func.count())
            .select_from(OrderModel)
            .where(OrderModel.organization_id == str(organization_id))
        )
        result = await self._session.execute(query)
        count = result.scalar() or 0
        
        # Format: ORG-YYYYMMDD-XXXXX
        date_str = datetime.utcnow().strftime("%Y%m%d")
        return f"ORD-{date_str}-{count + 1:05d}"
