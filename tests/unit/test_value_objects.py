"""
Unit tests for value objects.
"""

from decimal import Decimal

import pytest

from src.domain.value_objects.money import Money
from src.domain.value_objects.address import Address
from src.domain.value_objects.email import Email


class TestMoney:
    """Tests for Money value object."""
    
    def test_create_money(self):
        """Test money creation."""
        money = Money(amount=Decimal("100.50"), currency="USD")
        
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
    
    def test_money_from_cents(self):
        """Test creating money from cents."""
        money = Money.from_cents(1050, "USD")
        
        assert money.amount == Decimal("10.50")
    
    def test_money_to_cents(self):
        """Test converting money to cents."""
        money = Money(amount=Decimal("10.50"), currency="USD")
        
        assert money.to_cents() == 1050
    
    def test_money_addition(self):
        """Test adding money values."""
        m1 = Money(amount=Decimal("10.00"), currency="USD")
        m2 = Money(amount=Decimal("5.50"), currency="USD")
        
        result = m1 + m2
        
        assert result.amount == Decimal("15.50")
        assert result.currency == "USD"
    
    def test_money_subtraction(self):
        """Test subtracting money values."""
        m1 = Money(amount=Decimal("10.00"), currency="USD")
        m2 = Money(amount=Decimal("3.00"), currency="USD")
        
        result = m1 - m2
        
        assert result.amount == Decimal("7.00")
    
    def test_money_multiplication(self):
        """Test multiplying money by factor."""
        money = Money(amount=Decimal("10.00"), currency="USD")
        
        result = money * 3
        
        assert result.amount == Decimal("30.00")
    
    def test_money_percentage(self):
        """Test calculating percentage of money."""
        money = Money(amount=Decimal("100.00"), currency="USD")
        
        result = money.percentage(15)
        
        assert result.amount == Decimal("15.00")
    
    def test_currency_mismatch_raises(self):
        """Test that operations on different currencies raise error."""
        usd = Money(amount=Decimal("10.00"), currency="USD")
        eur = Money(amount=Decimal("10.00"), currency="EUR")
        
        with pytest.raises(ValueError, match="Currency mismatch"):
            usd + eur
    
    def test_money_comparison(self):
        """Test money comparison operators."""
        m1 = Money(amount=Decimal("10.00"), currency="USD")
        m2 = Money(amount=Decimal("20.00"), currency="USD")
        
        assert m1 < m2
        assert m2 > m1
        assert m1 != m2
    
    def test_money_string_formatting(self):
        """Test money string representation."""
        usd = Money(amount=Decimal("99.99"), currency="USD")
        eur = Money(amount=Decimal("50.00"), currency="EUR")
        
        assert str(usd) == "$99.99"
        assert str(eur) == "€50.00"
    
    def test_money_immutability(self):
        """Test that money is immutable."""
        money = Money(amount=Decimal("10.00"), currency="USD")
        
        with pytest.raises(Exception):  # ValidationError for frozen model
            money.amount = Decimal("20.00")


class TestAddress:
    """Tests for Address value object."""
    
    def test_create_address(self):
        """Test address creation."""
        addr = Address(
            street_line_1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US"
        )
        
        assert addr.city == "New York"
        assert addr.country == "US"
    
    def test_full_address_format(self):
        """Test full address formatting."""
        addr = Address(
            street_line_1="123 Main St",
            street_line_2="Apt 4B",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US"
        )
        
        expected = "123 Main St\nApt 4B\nNew York, NY 10001\nUS"
        assert addr.full_address == expected
    
    def test_single_line_format(self):
        """Test single line address formatting."""
        addr = Address(
            street_line_1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US"
        )
        
        assert "123 Main St" in addr.single_line
        assert "New York" in addr.single_line
    
    def test_address_immutability(self):
        """Test that address is immutable."""
        addr = Address(
            street_line_1="123 Main St",
            city="New York",
            postal_code="10001"
        )
        
        with pytest.raises(Exception):
            addr.city = "Boston"


class TestEmail:
    """Tests for Email value object."""
    
    def test_create_email(self):
        """Test email creation and normalization."""
        email = Email(value="Test@Example.COM")
        
        assert email.value == "test@example.com"  # Normalized to lowercase
    
    def test_email_parts(self):
        """Test email local part and domain extraction."""
        email = Email(value="user@example.com")
        
        assert email.local_part == "user"
        assert email.domain == "example.com"
    
    def test_invalid_email_raises(self):
        """Test that invalid email raises error."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email(value="not-an-email")
    
    def test_corporate_email_detection(self):
        """Test corporate vs free email detection."""
        corporate = Email(value="user@company.com")
        free = Email(value="user@gmail.com")
        
        assert corporate.is_corporate is True
        assert free.is_corporate is False
    
    def test_email_obfuscation(self):
        """Test email obfuscation for display."""
        email = Email(value="testuser@example.com")
        
        obfuscated = email.obfuscate()
        
        assert obfuscated == "t******r@example.com"
    
    def test_email_equality(self):
        """Test email equality comparison."""
        e1 = Email(value="user@example.com")
        e2 = Email(value="USER@Example.COM")
        
        assert e1 == e2
