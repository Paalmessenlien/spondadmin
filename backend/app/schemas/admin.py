"""
Admin user schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


class AdminBase(BaseModel):
    """
    Base admin schema with common fields
    """
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class AdminCreate(AdminBase):
    """
    Schema for creating a new admin with password strength validation
    """
    password: str = Field(..., min_length=8, max_length=100, description="Password must be at least 8 characters with uppercase, lowercase, digit, and special character")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength requirements:
        - At least 8 characters (enforced by Field)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        return v

    @model_validator(mode='after')
    def validate_username_password_different(self) -> 'AdminCreate':
        """
        Ensure username and password are not the same
        """
        if self.username.lower() == self.password.lower():
            raise ValueError('Password cannot be the same as username')
        if self.email.split('@')[0].lower() == self.password.lower():
            raise ValueError('Password cannot be the same as email username')
        return self


class AdminUpdate(BaseModel):
    """
    Schema for updating an admin (all fields optional)
    """
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="Password must be at least 8 characters with uppercase, lowercase, digit, and special character")
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate password strength requirements when password is being updated
        """
        if v is None:
            return v

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        return v


class AdminResponse(AdminBase):
    """
    Schema for admin response (without password)
    """
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminLogin(BaseModel):
    """
    Schema for admin login
    """
    username: str
    password: str
