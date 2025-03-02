from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional

from db import get_db_session
from services.settings_service import SettingsService
from services.auth_service import get_current_user
from models.api import (
    SettingsProfileResponse,
    SettingsProfileCreate,
    SettingsProfileUpdate,
)

router = APIRouter(prefix="/settings")
settings_service = SettingsService()

@router.get("/profiles", response_model=List[SettingsProfileResponse])
async def get_settings_profiles(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get all settings profiles for the current user."""
    return await settings_service.get_user_profiles(current_user.id, session)

@router.get("/profiles/active", response_model=SettingsProfileResponse)
async def get_active_profile(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get the active settings profile for the current user."""
    profile = await settings_service.get_active_profile(current_user.id, session)
    
    if not profile:
        # Ensure default profile exists
        profile = await settings_service.ensure_default_profile(current_user.id, session)
    
    return profile

@router.post("/profiles", response_model=SettingsProfileResponse)
async def create_settings_profile(
    profile: SettingsProfileCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new settings profile."""
    return await settings_service.create_profile(
        current_user.id,
        profile.name,
        profile.settings,
        profile.is_active,
        session
    )

@router.put("/profiles/{profile_id}", response_model=SettingsProfileResponse)
async def update_settings_profile(
    profile_id: int,
    profile: SettingsProfileUpdate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Update an existing settings profile."""
    updated_profile = await settings_service.update_profile(
        profile_id,
        profile.name,
        profile.settings,
        profile.is_active,
        session
    )
    
    if not updated_profile:
        raise HTTPException(status_code=404, detail=f"Profile with ID {profile_id} not found")
    
    return updated_profile

@router.delete("/profiles/{profile_id}")
async def delete_settings_profile(
    profile_id: int,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Delete a settings profile."""
    success = await settings_service.delete_profile(profile_id, session)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Profile with ID {profile_id} not found")
    
    return {"message": f"Profile with ID {profile_id} deleted successfully"}