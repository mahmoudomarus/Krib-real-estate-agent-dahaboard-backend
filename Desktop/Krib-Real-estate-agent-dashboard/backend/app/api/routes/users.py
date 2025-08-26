"""
User management routes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserUpdate, UserResponse, SuccessResponse, PasswordChangeRequest
from app.core.supabase_client import supabase_client, supabase_anon
from app.api.dependencies import get_current_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        result = supabase_client.table("users").select("*").eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        profile = result.data[0]
        return UserResponse(
            id=profile["id"],
            name=profile["name"],
            email=profile["email"],
            phone=profile.get("phone"),
            avatar_url=profile.get("avatar_url"),
            created_at=profile["created_at"],
            updated_at=profile["updated_at"],
            settings=profile.get("settings", {}),
            total_revenue=profile.get("total_revenue", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_updates: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        update_data = user_updates.dict(exclude_unset=True)
        
        if update_data:
            result = supabase_client.table("users").update(update_data).eq(
                "id", current_user["id"]
            ).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            profile = result.data[0]
            return UserResponse(
                id=profile["id"],
                name=profile["name"],
                email=profile["email"],
                phone=profile.get("phone"),
                avatar_url=profile.get("avatar_url"),
                created_at=profile["created_at"],
                updated_at=profile["updated_at"],
                settings=profile.get("settings", {}),
                total_revenue=profile.get("total_revenue", 0)
            )
        else:
            # No updates provided, return current profile
            return await get_user_profile(current_user)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.put("/settings", response_model=SuccessResponse)
async def update_user_settings(
    settings: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Update user settings (notifications, preferences, etc.)"""
    try:
        result = supabase_client.table("users").update({
            "settings": settings
        }).eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return SuccessResponse(message="Settings updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password - handles both email/password and OAuth users"""
    try:
        # Get user's auth information from Supabase
        user_response = supabase_client.auth.admin.get_user_by_id(current_user["id"])
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.user
        
        # Check if user has an email provider (local auth) or OAuth provider
        has_email_provider = any(identity.provider == "email" for identity in user.identities)
        has_oauth_provider = any(identity.provider in ["google", "github", "facebook"] for identity in user.identities)
        
        if has_email_provider:
            # User has email/password auth - verify current password is provided and correct
            if not password_data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required for email/password users"
                )
            
            try:
                auth_response = supabase_anon.auth.sign_in_with_password({
                    "email": current_user["email"],
                    "password": password_data.current_password
                })
                
                if not auth_response.session:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Current password is incorrect"
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        elif has_oauth_provider and not has_email_provider:
            # OAuth user setting their first password - no current password needed
            logger.info(f"OAuth user {current_user['id']} setting first password")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine authentication method"
            )
        
        # Update password using admin API (works for both cases)
        admin_update_response = supabase_client.auth.admin.update_user_by_id(
            current_user["id"],
            {
                "password": password_data.new_password
            }
        )
        
        if not admin_update_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return SuccessResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/notifications")
async def get_user_notifications(current_user: dict = Depends(get_current_user)):
    """Get user's notification settings"""
    try:
        result = supabase_client.table("users").select("settings").eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        settings = result.data[0].get("settings", {})
        notifications = settings.get("notifications", {
            "bookings": True,
            "marketing": False,
            "system_updates": True
        })
        
        return {"notifications": notifications}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user notifications"
        )


@router.put("/notifications")
async def update_user_notifications(
    notifications: Dict[str, bool],
    current_user: dict = Depends(get_current_user)
):
    """Update user's notification settings"""
    try:
        # Get current settings
        result = supabase_client.table("users").select("settings").eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        current_settings = result.data[0].get("settings", {})
        current_settings["notifications"] = notifications
        
        # Update settings
        update_result = supabase_client.table("users").update({
            "settings": current_settings
        }).eq("id", current_user["id"]).execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notifications"
            )
        
        return SuccessResponse(message="Notification settings updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user notifications"
        )
