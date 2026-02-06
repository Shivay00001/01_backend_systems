"""
User Routes - User management endpoints.
"""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.auth_service import get_auth_service
from src.domain.entities.user import User, UserRole
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.user_repository import UserRepository


router = APIRouter()


class CreateUserRequest(BaseModel):
    """Create user request model."""
    
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.VIEWER


class UpdateUserRequest(BaseModel):
    """Update user request model."""
    
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model."""
    
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: str


class UserListResponse(BaseModel):
    """Paginated user list response."""
    
    items: List[UserResponse]
    total: int
    skip: int
    limit: int


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create a new user account",
)
async def create_user(
    request: CreateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """
    Create a new user.
    
    Args:
        request: User creation data
        session: Database session
        
    Returns:
        Created user
    """
    user_repo = UserRepository(session)
    auth_service = get_auth_service()
    
    # Check if email exists
    if await user_repo.email_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        email=request.email,
        hashed_password=auth_service.hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
    )
    
    created_user = await user_repo.add(user)
    
    return UserResponse(
        id=str(created_user.id),
        email=created_user.email,
        full_name=created_user.full_name,
        role=created_user.role.value,
        is_active=created_user.is_active,
        is_verified=created_user.is_verified,
        created_at=created_user.created_at.isoformat(),
    )


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
    description="Get paginated list of users",
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
) -> UserListResponse:
    """
    List users with pagination.
    
    Args:
        session: Database session
        skip: Pagination offset
        limit: Maximum results
        active_only: Filter to active users only
        
    Returns:
        Paginated user list
    """
    user_repo = UserRepository(session)
    
    if active_only:
        users = await user_repo.get_active_users(skip=skip, limit=limit)
    else:
        users = await user_repo.get_all(skip=skip, limit=limit)
    
    total = await user_repo.count()
    
    return UserListResponse(
        items=[
            UserResponse(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                role=u.role.value,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at.isoformat(),
            )
            for u in users
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    description="Get user by ID",
)
async def get_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """
    Get user by ID.
    
    Args:
        user_id: User identifier
        session: Database session
        
    Returns:
        User details
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user details",
)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """
    Update user details.
    
    Args:
        user_id: User identifier
        request: Update data
        session: Database session
        
    Returns:
        Updated user
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if request.full_name is not None:
        user.update_profile(full_name=request.full_name)
    
    if request.role is not None:
        user.role = request.role
    
    if request.is_active is not None:
        if request.is_active:
            user.activate()
        else:
            user.deactivate()
    
    updated_user = await user_repo.update(user)
    
    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role.value,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at.isoformat(),
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Soft delete user (deactivate)",
)
async def delete_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    Soft delete user by deactivating.
    
    Args:
        user_id: User identifier
        session: Database session
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.deactivate()
    await user_repo.update(user)
