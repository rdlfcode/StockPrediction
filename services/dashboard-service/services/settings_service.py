import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from models.user_settings import User, SettingsProfile

logger = logging.getLogger(__name__)

# Default settings for new users
DEFAULT_SETTINGS = {
    # Data Ingestion Settings
    "data_fetch_interval_minutes": 15,  # How often to fetch new data (minutes)
    "historical_data_days": 730,        # Initial historical data to load (days)
    
    # Feature Engineering Settings
    "feature_calculation_intervals": [5, 10, 20, 50, 100, 200],  # Time windows for indicators
    
    # Model Settings
    "default_prediction_horizon": 5,   # Days to forecast into future
    "default_lookback_window": 30,     # Days of historical data for prediction
    "default_batch_size": 32,          # Batch size for model training
    
    # UI Settings
    "default_page_size": 20,           # Items per page in lists/tables
    "chart_theme": "light",            # Chart color theme (light/dark)
    "date_format": "MM/DD/YYYY",       # Date format for display
    "auto_refresh_interval": 60,       # Dashboard auto-refresh interval (seconds)
    
    # Alert Settings
    "enable_price_alerts": True,       # Enable price movement alerts
    "price_alert_threshold": 5.0,      # Alert threshold percentage
    "enable_prediction_alerts": True,  # Enable prediction accuracy alerts
    "prediction_alert_threshold": 10.0 # Alert threshold percentage
}

class SettingsService:
    """Service for managing user settings profiles."""
    
    async def get_user_profiles(self, user_id: int, session: AsyncSession) -> List[Dict]:
        """Get all settings profiles for a user."""
        query = select(SettingsProfile).where(SettingsProfile.user_id == user_id)
        result = await session.execute(query)
        profiles = result.scalars().all()
        
        return [
            {
                "id": profile.id,
                "name": profile.name,
                "is_active": profile.is_active,
                "settings": profile.settings,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            }
            for profile in profiles
        ]
    
    async def get_active_profile(self, user_id: int, session: AsyncSession) -> Optional[Dict]:
        """Get the active settings profile for a user."""
        query = select(SettingsProfile).where(
            SettingsProfile.user_id == user_id,
            SettingsProfile.is_active == True
        )
        result = await session.execute(query)
        profile = result.scalars().first()
        
        if not profile:
            return None
        
        return {
            "id": profile.id,
            "name": profile.name,
            "is_active": profile.is_active,
            "settings": profile.settings,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
    
    async def create_profile(
        self,
        user_id: int,
        name: str,
        settings: Dict,
        is_active: bool = False,
        session: AsyncSession
    ) -> Dict:
        """Create a new settings profile for a user."""
        # If this profile is active, deactivate all others
        if is_active:
            await self._deactivate_all_profiles(user_id, session)
        
        # Create new profile
        profile = SettingsProfile(
            user_id=user_id,
            name=name,
            settings=settings,
            is_active=is_active
        )
        
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        
        return {
            "id": profile.id,
            "name": profile.name,
            "is_active": profile.is_active,
            "settings": profile.settings,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
    
    async def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        settings: Optional[Dict] = None,
        is_active: Optional[bool] = None,
        session: AsyncSession
    ) -> Optional[Dict]:
        """Update an existing settings profile."""
        # Get profile
        query = select(SettingsProfile).where(SettingsProfile.id == profile_id)
        result = await session.execute(query)
        profile = result.scalars().first()
        
        if not profile:
            return None
        
        # If activating this profile, deactivate all others
        if is_active:
            await self._deactivate_all_profiles(profile.user_id, session)
        
        # Update profile
        if name is not None:
            profile.name = name
        
        if settings is not None:
            profile.settings = settings
        
        if is_active is not None:
            profile.is_active = is_active
        
        profile.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(profile)
        
        return {
            "id": profile.id,
            "name": profile.name,
            "is_active": profile.is_active,
            "settings": profile.settings,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
    
    async def delete_profile(self, profile_id: int, session: AsyncSession) -> bool:
        """Delete a settings profile."""
        # Get profile
        query = select(SettingsProfile).where(SettingsProfile.id == profile_id)
        result = await session.execute(query)
        profile = result.scalars().first()
        
        if not profile:
            return False
        
        # If this is the active profile, we need to set another one as active
        should_set_new_active = profile.is_active
        user_id = profile.user_id
        
        # Delete profile
        await session.delete(profile)
        await session.commit()
        
        # If this was the active profile, set another one as active
        if should_set_new_active:
            await self._set_new_active_profile(user_id, session)
        
        return True
    
    async def _deactivate_all_profiles(self, user_id: int, session: AsyncSession) -> None:
        """Deactivate all profiles for a user."""
        query = update(SettingsProfile).where(
            SettingsProfile.user_id == user_id
        ).values(is_active=False)
        
        await session.execute(query)
    
    async def _set_new_active_profile(self, user_id: int, session: AsyncSession) -> None:
        """Set a new active profile for a user after the active one is deleted."""
        # Get all profiles for the user
        query = select(SettingsProfile).where(SettingsProfile.user_id == user_id)
        result = await session.execute(query)
        profiles = result.scalars().all()
        
        if not profiles:
            # Create a default profile if none exist
            default_profile = SettingsProfile(
                user_id=user_id,
                name="Default",
                settings=DEFAULT_SETTINGS,
                is_active=True
            )
            
            session.add(default_profile)
            await session.commit()
            return
        
        # Set the first profile as active
        profiles[0].is_active = True
        await session.commit()
    
    async def ensure_default_profile(self, user_id: int, session: AsyncSession) -> Dict:
        """Ensure that a user has at least a default profile."""
        # Check if user has any profiles
        query = select(SettingsProfile).where(SettingsProfile.user_id == user_id)
        result = await session.execute(query)
        profiles = result.scalars().all()
        
        if not profiles:
            # Create default profile
            default_profile = SettingsProfile(
                user_id=user_id,
                name="Default",
                settings=DEFAULT_SETTINGS,
                is_active=True
            )
            
            session.add(default_profile)
            await session.commit()
            await session.refresh(default_profile)
            
            return {
                "id": default_profile.id,
                "name": default_profile.name,
                "is_active": default_profile.is_active,
                "settings": default_profile.settings,
                "created_at": default_profile.created_at.isoformat(),
                "updated_at": default_profile.updated_at.isoformat()
            }
        
        # Check if any profile is active
        active_profile = next((p for p in profiles if p.is_active), None)
        
        if not active_profile:
            # Set the first profile as active
            profiles[0].is_active = True
            await session.commit()
            await session.refresh(profiles[0])
            
            return {
                "id": profiles[0].id,
                "name": profiles[0].name,
                "is_active": profiles[0].is_active,
                "settings": profiles[0].settings,
                "created_at": profiles[0].created_at.isoformat(),
                "updated_at": profiles[0].updated_at.isoformat()
            }
        
        return {
            "id": active_profile.id,
            "name": active_profile.name,
            "is_active": active_profile.is_active,
            "settings": active_profile.settings,
            "created_at": active_profile.created_at.isoformat(),
            "updated_at": active_profile.updated_at.isoformat()
        }