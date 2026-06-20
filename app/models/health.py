from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Text, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class HealthDeclaration(Base):
    """
    User fills this before each donation attempt.
    If any critical condition is True, is_health_eligible on User is set False.
    """
    __tablename__ = "health_declarations"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Critical disqualifying conditions
    has_hiv         = Column(Boolean, default=False)
    has_hepatitis   = Column(Boolean, default=False)
    has_cancer      = Column(Boolean, default=False)
    has_diabetes    = Column(Boolean, default=False)
    has_heart_disease = Column(Boolean, default=False)
    has_tuberculosis  = Column(Boolean, default=False)
    had_recent_surgery = Column(Boolean, default=False)   # within 6 months
    on_medication   = Column(Boolean, default=False)
    had_recent_tattoo = Column(Boolean, default=False)    # within 6 months
    is_pregnant     = Column(Boolean, default=False)

    # Temporary disqualifiers
    had_fever_recently = Column(Boolean, default=False)   # within 2 weeks
    had_alcohol_recently = Column(Boolean, default=False) # within 24 hours

    # Additional notes
    other_conditions = Column(Text, nullable=True)

    # Result — auto-computed
    is_eligible     = Column(Boolean, default=True)
    ineligible_reason = Column(String(255), nullable=True)

    declared_at     = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_declarations")
