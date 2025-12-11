from typing import List, Optional
from pydantic import BaseModel, Field, validator


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class TenantOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class UserSignup(BaseModel):
    """Schema for public user signup - only username and password"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=4)

    @validator('username')
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

class UserLogin(BaseModel):
    """Schema for user login - username and password"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=4)

class UserCreate(BaseModel):
    """Schema for admin user creation - includes role and tenant"""
    username: str = Field(..., min_length=1, max_length=50)
    role: Optional[str] = 'user'
    tenant_name: Optional[str] = None
    password: Optional[str] = Field(default='password', min_length=4)  # Default password for Keycloak

    @validator('username')
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    tenant_id: Optional[int]

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., gt=0)
    available_quantity: int = Field(..., ge=0)

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()

    @validator('price')
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    available_quantity: int
    tenant_id: int

    class Config:
        orm_mode = True

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

    @validator('quantity')
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    user_id: int
    total_quantity: int
    total_amount: float
    items: List[OrderItemOut]

    class Config:
        orm_mode = True
