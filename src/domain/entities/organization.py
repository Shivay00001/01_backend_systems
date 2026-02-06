"""
Organization Entity - Multi-tenant organization model.

Represents a company or organization in the multi-tenant ERP system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OrganizationPlan(str, Enum):
    """Subscription plans for organizations."""
    
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    
    @property
    def max_users(self) -> int:
        """Maximum users allowed for this plan."""
        limits = {
            OrganizationPlan.FREE: 3,
            OrganizationPlan.STARTER: 10,
            OrganizationPlan.PROFESSIONAL: 50,
            OrganizationPlan.ENTERPRISE: 9999,
        }
        return limits.get(self, 3)
    
    @property
    def features(self) -> set[str]:
        """Features included in this plan."""
        base_features = {"dashboard", "orders", "inventory"}
        plan_features = {
            OrganizationPlan.FREE: base_features,
            OrganizationPlan.STARTER: base_features | {"reports", "export"},
            OrganizationPlan.PROFESSIONAL: base_features | {"reports", "export", "api", "integrations"},
            OrganizationPlan.ENTERPRISE: base_features | {"reports", "export", "api", "integrations", "sso", "audit_log"},
        }
        return plan_features.get(self, base_features)


class Organization(BaseModel):
    """
    Organization Entity - Represents a tenant organization.
    
    This is an aggregate root for organization-related operations.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique organization identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    plan: OrganizationPlan = Field(default=OrganizationPlan.FREE, description="Subscription plan")
    
    # Contact information
    email: Optional[str] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone")
    address: Optional[str] = Field(None, description="Business address")
    
    # Business details
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    currency: str = Field(default="USD", description="Default currency")
    timezone: str = Field(default="UTC", description="Organization timezone")
    
    # Status
    is_active: bool = Field(default=True, description="Whether organization is active")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Owner
    owner_id: Optional[UUID] = Field(None, description="Organization owner user ID")
    
    model_config = {
        "from_attributes": True,
    }
    
    def has_feature(self, feature: str) -> bool:
        """
        Check if organization has access to a feature.
        
        Args:
            feature: Feature name to check
            
        Returns:
            bool: True if feature is available
        """
        return feature in self.plan.features
    
    def can_add_user(self, current_user_count: int) -> bool:
        """
        Check if organization can add another user.
        
        Args:
            current_user_count: Current number of users
            
        Returns:
            bool: True if user can be added
        """
        return current_user_count < self.plan.max_users
    
    def upgrade_plan(self, new_plan: OrganizationPlan) -> None:
        """
        Upgrade organization to a new plan.
        
        Args:
            new_plan: The plan to upgrade to
            
        Raises:
            ValueError: If attempting to downgrade
        """
        plan_order = [
            OrganizationPlan.FREE,
            OrganizationPlan.STARTER,
            OrganizationPlan.PROFESSIONAL,
            OrganizationPlan.ENTERPRISE,
        ]
        
        current_index = plan_order.index(self.plan)
        new_index = plan_order.index(new_plan)
        
        if new_index < current_index:
            raise ValueError("Cannot downgrade plan. Contact support for downgrades.")
        
        self.plan = new_plan
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the organization."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
