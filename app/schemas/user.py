from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class HealthScreeningRequest(BaseModel):
    has_hiv: bool = False
    has_cancer: bool = False
    has_hepatitis: bool = False
    has_diabetes_insulin: bool = False
    has_heart_disease: bool = False
    had_recent_surgery: bool = False
    is_pregnant_or_recent_birth: bool = False
    had_recent_tattoo: bool = False
    had_malaria_recently: bool = False


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    blood_group: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    is_available_to_donate: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    blood_group: Optional[str]
    age: Optional[int]
    bio: Optional[str]
    is_available_to_donate: bool
    is_eligible_to_donate: bool
    health_screening_done: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DonorSearchResponse(BaseModel):
    id: int
    full_name: str
    blood_group: Optional[str]
    city: Optional[str]
    state: Optional[str]
    phone: Optional[str]
    age: Optional[int]
    bio: Optional[str]

    class Config:
        from_attributes = True
