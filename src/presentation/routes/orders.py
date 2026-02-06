"""
Order Routes - Order management endpoints.
"""

from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order import OrderStatus
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.order_repository import OrderRepository
from src.infrastructure.repositories.inventory_repository import InventoryRepository
from src.application.services.order_service import OrderService


router = APIRouter()


class CreateOrderRequest(BaseModel):
    """Create order request model."""
    
    customer_name: str
    customer_email: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None


class AddItemRequest(BaseModel):
    """Add item to order request."""
    
    product_id: UUID
    quantity: int
    unit_price: Optional[Decimal] = None
    discount_percent: Decimal = Decimal("0")


class OrderItemResponse(BaseModel):
    """Order item response model."""
    
    id: str
    product_id: str
    product_name: str
    sku: str
    quantity: int
    unit_price: float
    discount_percent: float
    total: float


class OrderResponse(BaseModel):
    """Order response model."""
    
    id: str
    order_number: str
    customer_name: str
    customer_email: Optional[str]
    status: str
    items: List[OrderItemResponse]
    subtotal: float
    total_discount: float
    total_tax: float
    shipping_cost: float
    grand_total: float
    currency: str
    created_at: str


class OrderListResponse(BaseModel):
    """Paginated order list response."""
    
    items: List[OrderResponse]
    total: int
    skip: int
    limit: int


def _order_to_response(order) -> OrderResponse:
    """Convert order entity to response model."""
    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        status=order.status.value,
        items=[
            OrderItemResponse(
                id=str(item.id),
                product_id=str(item.product_id),
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                discount_percent=float(item.discount_percent),
                total=float(item.total),
            )
            for item in order.items
        ],
        subtotal=float(order.subtotal),
        total_discount=float(order.total_discount),
        total_tax=float(order.total_tax),
        shipping_cost=float(order.shipping_cost),
        grand_total=float(order.grand_total),
        currency=order.currency,
        created_at=order.created_at.isoformat(),
    )


# Hardcoded org ID for demo - in production, get from authenticated user
DEMO_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
    description="Create a new order",
)
async def create_order(
    request: CreateOrderRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """
    Create a new order.
    
    Args:
        request: Order creation data
        session: Database session
        
    Returns:
        Created order
    """
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    order = await order_service.create_order(
        organization_id=DEMO_ORG_ID,
        customer_name=request.customer_name,
        customer_email=request.customer_email,
    )
    
    return _order_to_response(order)


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="List orders",
    description="Get paginated list of orders",
)
async def list_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> OrderListResponse:
    """
    List orders with pagination.
    
    Args:
        session: Database session
        status_filter: Optional status filter
        skip: Pagination offset
        limit: Maximum results
        
    Returns:
        Paginated order list
    """
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    orders = await order_service.get_orders(
        organization_id=DEMO_ORG_ID,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    
    return OrderListResponse(
        items=[_order_to_response(o) for o in orders],
        total=len(orders),  # In production, get actual count
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order",
    description="Get order by ID",
)
async def get_order(
    order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """
    Get order by ID.
    
    Args:
        order_id: Order identifier
        session: Database session
        
    Returns:
        Order details
    """
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    
    return _order_to_response(order)


@router.post(
    "/{order_id}/items",
    response_model=OrderResponse,
    summary="Add item to order",
    description="Add an item to an existing order",
)
async def add_order_item(
    order_id: UUID,
    request: AddItemRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """
    Add item to order.
    
    Args:
        order_id: Order identifier
        request: Item details
        session: Database session
        
    Returns:
        Updated order
    """
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    try:
        order = await order_service.add_item_to_order(
            order_id=order_id,
            product_id=request.product_id,
            quantity=request.quantity,
            unit_price=request.unit_price,
            discount_percent=request.discount_percent,
        )
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/submit",
    response_model=OrderResponse,
    summary="Submit order",
    description="Submit a draft order for processing",
)
async def submit_order(
    order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """Submit order for processing."""
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    try:
        order = await order_service.submit_order(order_id)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    summary="Confirm order",
    description="Confirm a pending order",
)
async def confirm_order(
    order_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderResponse:
    """Confirm a pending order."""
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    try:
        order = await order_service.confirm_order(order_id)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order",
    description="Cancel an order",
)
async def cancel_order(
    order_id: UUID,
    reason: Optional[str] = Query(None),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> OrderResponse:
    """Cancel an order."""
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    order_service = OrderService(order_repo, inventory_repo)
    
    try:
        order = await order_service.cancel_order(order_id, reason)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
