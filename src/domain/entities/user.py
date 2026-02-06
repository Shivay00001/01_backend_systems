"""
User Entity - Core user domain model.

Implements the User aggregate with role-based access control and
proper encapsulation of business rules.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles for RBAC."""
    
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    
    @property
    def permissions(self) -> set[str]:
        """Get permissions for this role."""
        role_permissions = {
            UserRole.ADMIN: {"read", "write", "delete", "manage_users", "manage_system"},
            UserRole.MANAGER: {"read", "write", "delete", "manage_team"},
            UserRole.OPERATOR: {"read", "write"},
            UserRole.VIEWER: {"read"},
        }
        return role_permissions.get(self, set())
    
    def can(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions


class User(BaseModel):
    """
    User Entity - Represents a system user with authentication and authorization.
    
    This is an aggregate root in DDD terms, encapsulating all user-related
    business logic and invariants.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User's role")
    organization_id: Optional[UUID] = Field(None, description="Associated organization")
    
    # Audit fields
    is_active: bool = Field(default=True, description="Whether user is active")
    is_verified: bool = Field(default=False, description="Email verification status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Security fields
    failed_login_attempts: int = Field(default=0, description="Failed login counter")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiry")
    
    model_config = {
        "from_attributes": True,
    }
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission: The permission to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if not self.is_active:
            return False
        return self.role.can(permission)
    
    def is_locked(self) -> bool:
        """Check if the user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def record_failed_login(self) -> None:
        """
        Record a failed login attempt.
        
        Locks account after 5 consecutive failed attempts.
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def record_successful_login(self) -> None:
        """Record a successful login, resetting security counters."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
    
    def update_profile(self, full_name: Optional[str] = None) -> None:
        """
        Update user profile information.
        
        Args:
            full_name: New full name if provided
        """
        if full_name is not None:
            self.full_name = full_name
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def change_role(self, new_role: UserRole, changed_by: "User") -> None:
        """
        Change user role with authorization check.
        
        Args:
            new_role: The new role to assign
            changed_by: The user performing the role change
            
        Raises:
            PermissionError: If changed_by lacks permission
        """
        if not changed_by.has_permission("manage_users"):
            raise PermissionError("User lacks permission to change roles")
        
        self.role = new_role
        self.updated_at = datetime.utcnow()
