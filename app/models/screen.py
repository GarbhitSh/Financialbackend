from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Screen(Base):
    __tablename__ = "screens"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationship
    criteria = relationship("ScreenCriteria", back_populates="screen", cascade="all, delete-orphan")
    user = relationship("User")

class ScreenCriteria(Base):
    __tablename__ = "screen_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=False)
    field = Column(String, nullable=False)  # e.g., "pe_ratio", "market_cap"
    operator = Column(String, nullable=False)  # e.g., ">", "<", "=", "between"
    value = Column(JSON, nullable=False)  # Can store single value or range
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    screen = relationship("Screen", back_populates="criteria")
