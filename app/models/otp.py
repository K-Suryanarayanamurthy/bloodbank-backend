from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class OTP(Base):
    __tablename__ = "otps"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_code   = Column(String(6), nullable=False)
    is_used    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="otps")

    def is_expired(self) -> bool:
        from datetime import timedelta
        return datetime.utcnow() > self.created_at + timedelta(minutes=10)
