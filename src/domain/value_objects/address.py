"""
Address Value Object - Immutable representation of a physical address.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Address(BaseModel):
    """
    Address Value Object - Represents a physical address.
    
    Immutable value object for address information.
    """
    
    street_line_1: str = Field(..., min_length=1, max_length=255)
    street_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(default="US", min_length=2, max_length=2)
    
    model_config = {
        "frozen": True,  # Immutable
    }
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        lines = [self.street_line_1]
        if self.street_line_2:
            lines.append(self.street_line_2)
        
        city_line = self.city
        if self.state:
            city_line += f", {self.state}"
        city_line += f" {self.postal_code}"
        lines.append(city_line)
        lines.append(self.country)
        
        return "\n".join(lines)
    
    @property
    def single_line(self) -> str:
        """Get single-line formatted address."""
        parts = [self.street_line_1]
        if self.street_line_2:
            parts.append(self.street_line_2)
        parts.append(self.city)
        if self.state:
            parts.append(self.state)
        parts.append(self.postal_code)
        parts.append(self.country)
        
        return ", ".join(parts)
    
    def with_updated(
        self,
        street_line_1: Optional[str] = None,
        street_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
    ) -> "Address":
        """
        Create a new address with updated fields.
        
        Returns a new Address instance with specified fields updated.
        """
        return Address(
            street_line_1=street_line_1 or self.street_line_1,
            street_line_2=street_line_2 if street_line_2 is not None else self.street_line_2,
            city=city or self.city,
            state=state if state is not None else self.state,
            postal_code=postal_code or self.postal_code,
            country=country or self.country,
        )
    
    def __str__(self) -> str:
        """String representation."""
        return self.single_line
    
    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Address):
            return NotImplemented
        return (
            self.street_line_1 == other.street_line_1
            and self.street_line_2 == other.street_line_2
            and self.city == other.city
            and self.state == other.state
            and self.postal_code == other.postal_code
            and self.country == other.country
        )
