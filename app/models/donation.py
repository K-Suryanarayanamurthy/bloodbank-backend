from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.user import BloodGroup
import enum

class DonationStatus(str, enum.Enum):
    PENDING   = "pending"    # Request made, waiting for donor response
    ACCEPTED  = "accepted"   # Donor accepted
    COMPLETED = "completed"  # Donation done
    CANCELLED = "cancelled"  # Either side cancelled

class DonationRecord(Base):
    """Tracks every blood donation request and its outcome."""
    __tablename__ = "donation_records"

    id            = Column(Integer, primary_key=True, index=True)
    donor_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    seeker_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_group   = Column(Enum(BloodGroup), nullable=False)
    hospital_name = Column(String(200), nullable=True)
    city          = Column(String(100), nullable=True)
    urgency_note  = Column(Text, nullable=True)
    status        = Column(Enum(DonationStatus), default=DonationStatus.PENDING)
    requested_at  = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    donor  = relationship("User", foreign_keys=[donor_id], back_populates="donation_records")
    seeker = relationship("User", foreign_keys=[seeker_id])
