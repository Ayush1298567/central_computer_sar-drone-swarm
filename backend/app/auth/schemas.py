from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List


class RoleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    name: str
    description: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    roles: Optional[List[str]] = None  # list of role names


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    username: str
    email: EmailStr
    is_active: bool
    roles: List[str] = []
