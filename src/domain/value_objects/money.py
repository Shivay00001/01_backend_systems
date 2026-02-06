"""
Money Value Object - Immutable representation of monetary values.

Implements proper decimal handling and currency awareness.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Self

from pydantic import BaseModel, Field


class Money(BaseModel):
    """
    Money Value Object - Represents a monetary amount with currency.
    
    This is an immutable value object that ensures:
    - Proper decimal precision for financial calculations
    - Currency-aware operations
    - Immutability (all operations return new instances)
    """
    
    amount: Decimal = Field(..., description="Monetary amount")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    
    model_config = {
        "frozen": True,  # Immutable
    }
    
    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create a zero money instance."""
        return cls(amount=Decimal("0"), currency=currency)
    
    @classmethod
    def from_cents(cls, cents: int, currency: str = "USD") -> "Money":
        """Create money from cents (minor units)."""
        return cls(amount=Decimal(cents) / 100, currency=currency)
    
    def to_cents(self) -> int:
        """Convert to cents (minor units)."""
        return int(self.amount * 100)
    
    def round(self, decimal_places: int = 2) -> "Money":
        """Round to specified decimal places."""
        rounded = self.amount.quantize(
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        )
        return Money(amount=rounded, currency=self.currency)
    
    def add(self, other: "Money") -> "Money":
        """
        Add two money values.
        
        Args:
            other: Money to add
            
        Returns:
            New Money instance with sum
            
        Raises:
            ValueError: If currencies don't match
        """
        self._ensure_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        """
        Subtract money value.
        
        Args:
            other: Money to subtract
            
        Returns:
            New Money instance with difference
        """
        self._ensure_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)
    
    def multiply(self, factor: Decimal | int | float) -> "Money":
        """
        Multiply by a factor.
        
        Args:
            factor: Multiplication factor
            
        Returns:
            New Money instance with product
        """
        return Money(
            amount=self.amount * Decimal(str(factor)),
            currency=self.currency
        )
    
    def divide(self, divisor: Decimal | int | float) -> "Money":
        """
        Divide by a divisor.
        
        Args:
            divisor: Division divisor
            
        Returns:
            New Money instance with quotient
            
        Raises:
            ValueError: If dividing by zero
        """
        if Decimal(str(divisor)) == 0:
            raise ValueError("Cannot divide by zero")
        return Money(
            amount=self.amount / Decimal(str(divisor)),
            currency=self.currency
        )
    
    def percentage(self, percent: Decimal | int | float) -> "Money":
        """
        Calculate percentage of this amount.
        
        Args:
            percent: Percentage (e.g., 15 for 15%)
            
        Returns:
            New Money instance representing the percentage
        """
        return self.multiply(Decimal(str(percent)) / 100)
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0
    
    def negate(self) -> "Money":
        """Return negated amount."""
        return Money(amount=-self.amount, currency=self.currency)
    
    def abs(self) -> "Money":
        """Return absolute value."""
        return Money(amount=abs(self.amount), currency=self.currency)
    
    def _ensure_same_currency(self, other: "Money") -> None:
        """Ensure two money values have the same currency."""
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )
    
    def __str__(self) -> str:
        """Format as string with currency symbol."""
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "INR": "₹",
        }
        symbol = symbols.get(self.currency, self.currency + " ")
        return f"{symbol}{self.amount:.2f}"
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another Money object."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency
    
    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._ensure_same_currency(other)
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount <= other.amount
    
    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._ensure_same_currency(other)
        return self.amount > other.amount
    
    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount >= other.amount
    
    def __add__(self, other: "Money") -> "Money":
        """Support + operator."""
        return self.add(other)
    
    def __sub__(self, other: "Money") -> "Money":
        """Support - operator."""
        return self.subtract(other)
    
    def __mul__(self, other: Decimal | int | float) -> "Money":
        """Support * operator."""
        return self.multiply(other)
    
    def __truediv__(self, other: Decimal | int | float) -> "Money":
        """Support / operator."""
        return self.divide(other)
    
    def __neg__(self) -> "Money":
        """Support unary - operator."""
        return self.negate()
    
    def __abs__(self) -> "Money":
        """Support abs() function."""
        return self.abs()
