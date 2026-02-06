"""Value Objects - Immutable domain objects without identity."""

from src.domain.value_objects.money import Money
from src.domain.value_objects.address import Address
from src.domain.value_objects.email import Email

__all__ = ["Money", "Address", "Email"]
