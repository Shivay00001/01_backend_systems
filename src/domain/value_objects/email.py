"""
Email Value Object - Validated and normalized email address.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Email(BaseModel):
    """
    Email Value Object - Represents a validated email address.
    
    Immutable value object with email validation and normalization.
    """
    
    value: str = Field(..., description="Email address")
    
    model_config = {
        "frozen": True,  # Immutable
    }
    
    @field_validator("value", mode="before")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        """Validate and normalize email address."""
        if not v:
            raise ValueError("Email cannot be empty")
        
        # Basic email pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        # Normalize: lowercase and strip whitespace
        normalized = v.strip().lower()
        
        if not re.match(pattern, normalized):
            raise ValueError(f"Invalid email format: {v}")
        
        return normalized
    
    @property
    def local_part(self) -> str:
        """Get the local part (before @)."""
        return self.value.split("@")[0]
    
    @property
    def domain(self) -> str:
        """Get the domain part (after @)."""
        return self.value.split("@")[1]
    
    @property
    def is_corporate(self) -> bool:
        """Check if email is from a corporate domain (not free email)."""
        free_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "mail.com",
            "protonmail.com",
        }
        return self.domain not in free_domains
    
    def obfuscate(self) -> str:
        """Return obfuscated version for display."""
        local = self.local_part
        if len(local) <= 2:
            obfuscated_local = local[0] + "*"
        else:
            obfuscated_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{obfuscated_local}@{self.domain}"
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other: object) -> bool:
        """Check equality (case-insensitive)."""
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower()
        return NotImplemented
    
    def __hash__(self) -> int:
        """Hash based on normalized value."""
        return hash(self.value)
