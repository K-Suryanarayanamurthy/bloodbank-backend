from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.user import BloodGroup
import enum


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # filled when a donor accepts

    blood_group_needed = Column(Enum(BloodGroup), nullable=False)
    units_needed = Column(Integer, default=1)
    hospital_name = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    urgency = Column(String(20), default="normal")   # normal / urgent / critical
    notes = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id], back_populates="blood_requests_made")
    donor = relationship("User", foreign_keys=[donor_id], back_populates="blood_requests_fulfilled")
