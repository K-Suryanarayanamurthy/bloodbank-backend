from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class BloodGroup(str, enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"

class User(Base):
    __tablename__ = "users"

    id                     = Column(Integer, primary_key=True, index=True)
    full_name              = Column(String(100), nullable=False)
    email                  = Column(String(150), unique=True, index=True, nullable=False)
    phone                  = Column(String(15), nullable=True)
    password_hash          = Column(String(255), nullable=False)
    city                   = Column(String(100), nullable=True)
    state                  = Column(String(100), nullable=True)
    blood_group            = Column(Enum(BloodGroup), nullable=True)
    bio                    = Column(Text, nullable=True)
    is_available_to_donate = Column(Boolean, default=True)
    is_health_eligible = Column(Boolean, default=False)
    is_admin               = Column(Boolean, default=False)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime, default=datetime.utcnow)
    updated_at             = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    health_declarations = relationship("HealthDeclaration", back_populates="user", cascade="all, delete")
    sent_messages       = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete")
    received_messages   = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete")
    otps                = relationship("OTP", back_populates="user", cascade="all, delete")

    # Specify foreign_keys to resolve ambiguity
    donation_records    = relationship("DonationRecord", foreign_keys="DonationRecord.donor_id", back_populates="donor", cascade="all, delete")
    blood_requests      = relationship("DonationRecord", foreign_keys="DonationRecord.seeker_id", back_populates="seeker", cascade="all, delete")