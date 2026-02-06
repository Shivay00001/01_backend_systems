"""
Base Repository - Abstract repository pattern implementation.

Provides common CRUD operations for all entities.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)
EntityType = TypeVar("EntityType")


class BaseRepository(ABC, Generic[ModelType, EntityType]):
    """
    Abstract base repository providing common data access patterns.
    
    Implements the repository pattern for clean separation between
    domain and infrastructure layers.
    """
    
    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
            model_class: The SQLAlchemy model class
        """
        self._session = session
        self._model_class = model_class
    
    @abstractmethod
    def _to_entity(self, model: ModelType) -> EntityType:
        """Convert database model to domain entity."""
        pass
    
    @abstractmethod
    def _to_model(self, entity: EntityType) -> ModelType:
        """Convert domain entity to database model."""
        pass
    
    async def get_by_id(self, id: UUID | str) -> Optional[EntityType]:
        """
        Get entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            Entity if found, None otherwise
        """
        result = await self._session.get(self._model_class, str(id))
        return self._to_entity(result) if result else None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EntityType]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of entities
        """
        query = (
            select(self._model_class)
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def add(self, entity: EntityType) -> EntityType:
        """
        Add a new entity.
        
        Args:
            entity: Entity to add
            
        Returns:
            Added entity with generated ID
        """
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)
    
    async def update(self, entity: EntityType) -> EntityType:
        """
        Update an existing entity.
        
        Args:
            entity: Entity with updated data
            
        Returns:
            Updated entity
        """
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return self._to_entity(merged)
    
    async def delete(self, id: UUID | str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            True if deleted, False if not found
        """
        model = await self._session.get(self._model_class, str(id))
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False
    
    async def exists(self, id: UUID | str) -> bool:
        """
        Check if entity exists.
        
        Args:
            id: Entity identifier
            
        Returns:
            True if exists, False otherwise
        """
        model = await self._session.get(self._model_class, str(id))
        return model is not None
    
    async def count(self) -> int:
        """
        Count total entities.
        
        Returns:
            Total count
        """
        from sqlalchemy import func
        query = select(func.count()).select_from(self._model_class)
        result = await self._session.execute(query)
        return result.scalar() or 0
