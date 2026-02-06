"""
User Repository - Data access for user entities.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User, UserRole
from src.infrastructure.database.models import UserModel
from src.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel, User]):
    """Repository for User entity data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity."""
        return User(
            id=UUID(model.id),
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            role=model.role,
            organization_id=UUID(model.organization_id) if model.organization_id else None,
            is_active=model.is_active,
            is_verified=model.is_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
        )
    
    def _to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        return UserModel(
            id=str(entity.id),
            email=entity.email,
            hashed_password=entity.hashed_password,
            full_name=entity.full_name,
            role=entity.role,
            organization_id=str(entity.organization_id) if entity.organization_id else None,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_login_at=entity.last_login_at,
            failed_login_attempts=entity.failed_login_attempts,
            locked_until=entity.locked_until,
        )
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email address to search
            
        Returns:
            User if found, None otherwise
        """
        query = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all users in an organization.
        
        Args:
            organization_id: Organization ID
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of users
        """
        query = (
            select(UserModel)
            .where(UserModel.organization_id == str(organization_id))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get only active users."""
        query = (
            select(UserModel)
            .where(UserModel.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        query = select(UserModel.id).where(UserModel.email == email.lower())
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None
