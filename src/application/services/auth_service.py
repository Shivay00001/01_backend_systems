"""
Authentication Service - Handles user authentication and token management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import get_settings
from src.domain.entities.user import User


class AuthenticationService:
    """
    Service for handling authentication operations.
    
    Manages password hashing, verification, and JWT token generation.
    """
    
    ALGORITHM = "HS256"
    
    def __init__(self):
        """Initialize authentication service."""
        self._settings = get_settings()
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self._pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        return self._pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User identifier
            email: User email
            role: User role
            expires_delta: Optional custom expiration
            
        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self._settings.access_token_expire_minutes)
        
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire,
            "type": "access",
        }
        
        return jwt.encode(
            to_encode,
            self._settings.secret_key,
            algorithm=self.ALGORITHM,
        )
    
    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User identifier
            expires_delta: Optional custom expiration
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self._settings.refresh_token_expire_days)
        
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
        }
        
        return jwt.encode(
            to_encode,
            self._settings.secret_key,
            algorithm=self.ALGORITHM,
        )
    
    def decode_token(self, token: str) -> Optional[dict]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self.ALGORITHM],
            )
            return payload
        except JWTError:
            return None
    
    def validate_access_token(self, token: str) -> Optional[dict]:
        """
        Validate an access token.
        
        Args:
            token: JWT access token
            
        Returns:
            Token payload if valid access token, None otherwise
        """
        payload = self.decode_token(token)
        if payload and payload.get("type") == "access":
            return payload
        return None
    
    def validate_refresh_token(self, token: str) -> Optional[str]:
        """
        Validate a refresh token.
        
        Args:
            token: JWT refresh token
            
        Returns:
            User ID if valid refresh token, None otherwise
        """
        payload = self.decode_token(token)
        if payload and payload.get("type") == "refresh":
            return payload.get("sub")
        return None
    
    def authenticate_user(
        self,
        user: User,
        password: str,
    ) -> bool:
        """
        Authenticate a user with password.
        
        Args:
            user: User entity
            password: Plain text password
            
        Returns:
            True if authentication successful
            
        Raises:
            ValueError: If account is locked or inactive
        """
        if not user.is_active:
            raise ValueError("Account is inactive")
        
        if user.is_locked():
            raise ValueError("Account is temporarily locked")
        
        if not self.verify_password(password, user.hashed_password):
            user.record_failed_login()
            return False
        
        user.record_successful_login()
        return True


# Singleton instance
_auth_service: Optional[AuthenticationService] = None


def get_auth_service() -> AuthenticationService:
    """Get authentication service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service
