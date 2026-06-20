from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CreateBloodRequestSchema(BaseModel):
    blood_group_needed: str
    units_needed: int = 1
    hospital_name: Optional[str] = None
    city: str
    urgency: str = "normal"   # normal / urgent / critical
    notes: Optional[str] = None


class BloodRequestResponse(BaseModel):
    id: int
    requester_id: int
    donor_id: Optional[int]
    blood_group_needed: str
    units_needed: int
    hospital_name: Optional[str]
    city: str
    urgency: str
    notes: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
