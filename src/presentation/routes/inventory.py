"""
Inventory Routes - Inventory management endpoints.
"""

from decimal import Decimal
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.inventory import InventoryItem
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.inventory_repository import InventoryRepository


router = APIRouter()


class CreateInventoryItemRequest(BaseModel):
    """Create inventory item request."""
    
    sku: str
    name: str
    description: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    cost_price: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")
    quantity_on_hand: int = 0
    reorder_point: int = 10
    reorder_quantity: int = 50


class UpdateInventoryItemRequest(BaseModel):
    """Update inventory item request."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None


class AdjustStockRequest(BaseModel):
    """Stock adjustment request."""
    
    quantity: int
    reason: str


class InventoryItemResponse(BaseModel):
    """Inventory item response model."""
    
    id: str
    sku: str
    name: str
    description: Optional[str]
    barcode: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    cost_price: float
    selling_price: float
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    needs_reorder: bool
    is_active: bool
    created_at: str


class InventoryListResponse(BaseModel):
    """Paginated inventory list response."""
    
    items: List[InventoryItemResponse]
    total: int
    skip: int
    limit: int


def _item_to_response(item: InventoryItem) -> InventoryItemResponse:
    """Convert inventory item entity to response model."""
    return InventoryItemResponse(
        id=str(item.id),
        sku=item.sku,
        name=item.name,
        description=item.description,
        barcode=item.barcode,
        category=item.category,
        brand=item.brand,
        cost_price=float(item.cost_price),
        selling_price=float(item.selling_price),
        quantity_on_hand=item.quantity_on_hand,
        quantity_reserved=item.quantity_reserved,
        quantity_available=item.quantity_available,
        needs_reorder=item.needs_reorder,
        is_active=item.is_active,
        created_at=item.created_at.isoformat(),
    )


# Hardcoded org ID for demo
DEMO_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory item",
    description="Create a new inventory item",
)
async def create_inventory_item(
    request: CreateInventoryItemRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InventoryItemResponse:
    """
    Create a new inventory item.
    
    Args:
        request: Item creation data
        session: Database session
        
    Returns:
        Created inventory item
    """
    inventory_repo = InventoryRepository(session)
    
    # Check if SKU exists
    existing = await inventory_repo.get_by_sku(request.sku, DEMO_ORG_ID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SKU already exists",
        )
    
    item = InventoryItem(
        organization_id=DEMO_ORG_ID,
        sku=request.sku,
        name=request.name,
        description=request.description,
        barcode=request.barcode,
        category=request.category,
        brand=request.brand,
        cost_price=request.cost_price,
        selling_price=request.selling_price,
        quantity_on_hand=request.quantity_on_hand,
        reorder_point=request.reorder_point,
        reorder_quantity=request.reorder_quantity,
    )
    
    created_item = await inventory_repo.add(item)
    return _item_to_response(created_item)


@router.get(
    "/",
    response_model=InventoryListResponse,
    summary="List inventory",
    description="Get paginated list of inventory items",
)
async def list_inventory(
    session: Annotated[AsyncSession, Depends(get_session)],
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> InventoryListResponse:
    """
    List inventory items with filtering.
    
    Args:
        session: Database session
        category: Optional category filter
        search: Optional search term
        skip: Pagination offset
        limit: Maximum results
        
    Returns:
        Paginated inventory list
    """
    inventory_repo = InventoryRepository(session)
    
    if search:
        items = await inventory_repo.search(DEMO_ORG_ID, search, skip, limit)
    else:
        items = await inventory_repo.get_by_organization(
            DEMO_ORG_ID,
            category=category,
            skip=skip,
            limit=limit,
        )
    
    return InventoryListResponse(
        items=[_item_to_response(i) for i in items],
        total=len(items),
        skip=skip,
        limit=limit,
    )


@router.get(
    "/low-stock",
    response_model=List[InventoryItemResponse],
    summary="Get low stock items",
    description="Get items below reorder point",
)
async def get_low_stock_items(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> List[InventoryItemResponse]:
    """Get items that need reordering."""
    inventory_repo = InventoryRepository(session)
    items = await inventory_repo.get_low_stock_items(DEMO_ORG_ID)
    return [_item_to_response(i) for i in items]


@router.get(
    "/{item_id}",
    response_model=InventoryItemResponse,
    summary="Get inventory item",
    description="Get inventory item by ID",
)
async def get_inventory_item(
    item_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InventoryItemResponse:
    """Get inventory item by ID."""
    inventory_repo = InventoryRepository(session)
    item = await inventory_repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    return _item_to_response(item)


@router.patch(
    "/{item_id}",
    response_model=InventoryItemResponse,
    summary="Update inventory item",
    description="Update inventory item details",
)
async def update_inventory_item(
    item_id: UUID,
    request: UpdateInventoryItemRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InventoryItemResponse:
    """Update inventory item."""
    inventory_repo = InventoryRepository(session)
    item = await inventory_repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    if request.name is not None:
        item.name = request.name
    if request.description is not None:
        item.description = request.description
    if request.category is not None:
        item.category = request.category
    if request.cost_price is not None:
        item.cost_price = request.cost_price
    if request.selling_price is not None:
        item.selling_price = request.selling_price
    if request.reorder_point is not None:
        item.reorder_point = request.reorder_point
    if request.reorder_quantity is not None:
        item.reorder_quantity = request.reorder_quantity
    
    updated_item = await inventory_repo.update(item)
    return _item_to_response(updated_item)


@router.post(
    "/{item_id}/adjust",
    response_model=InventoryItemResponse,
    summary="Adjust stock",
    description="Adjust inventory stock level",
)
async def adjust_stock(
    item_id: UUID,
    request: AdjustStockRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InventoryItemResponse:
    """
    Adjust stock level for an item.
    
    Quantity can be positive (add stock) or negative (remove stock).
    """
    inventory_repo = InventoryRepository(session)
    item = await inventory_repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    try:
        movement = item.adjust_stock(request.quantity, request.reason)
        await inventory_repo.add_stock_movement(movement)
        updated_item = await inventory_repo.update(item)
        return _item_to_response(updated_item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{item_id}/receive",
    response_model=InventoryItemResponse,
    summary="Receive stock",
    description="Receive stock from purchase",
)
async def receive_stock(
    item_id: UUID,
    quantity: int = Query(..., gt=0),
    reference: Optional[str] = Query(None),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> InventoryItemResponse:
    """Receive stock from a purchase."""
    inventory_repo = InventoryRepository(session)
    item = await inventory_repo.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )
    
    movement = item.receive_stock(quantity, reference)
    await inventory_repo.add_stock_movement(movement)
    updated_item = await inventory_repo.update(item)
    return _item_to_response(updated_item)
