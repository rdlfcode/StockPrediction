from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    # Other user fields would go here
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to settings profiles
    profiles = relationship("SettingsProfile", back_populates="user", cascade="all, delete-orphan")

class SettingsProfile(Base):
    """Settings profile model for storing user-specific settings profiles."""
    __tablename__ = "settings_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)  # Profile name (e.g., "Default", "Conservative", "Aggressive")
    is_active = Column(Boolean, default=False)  # Whether this is the active profile
    settings = Column(JSON, nullable=False)  # JSON blob of settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="profiles")
    
    # Ensure unique profile names per user
    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_profile_name_uc'),)