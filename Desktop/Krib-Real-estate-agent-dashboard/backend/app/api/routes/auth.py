"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import LoginRequest, UserCreate, UserResponse, Token, SuccessResponse
from app.core.supabase_client import supabase_client, supabase_anon
from app.api.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
async def sign_up(user_data: UserCreate):
    """Register a new user"""
    try:
        # Create user with Supabase Auth
        auth_response = supabase_anon.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name
                }
            }
        })
        
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        user = auth_response.user
        
        # Create user profile in our database
        profile_data = {
            "id": user.id,
            "name": user_data.name,
            "email": user_data.email,
            "settings": {
                "notifications": {
                    "bookings": True,
                    "marketing": False,
                    "system_updates": True
                },
                "preferences": {
                    "currency": "USD",
                    "timezone": "America/New_York",
                    "language": "English"
                }
            },
            "total_revenue": 0
        }
        
        # Insert profile
        profile_result = supabase_client.table("users").insert(profile_data).execute()
        
        if not profile_result.data:
            # If profile creation fails, still return user data
            logger.warning(f"Failed to create profile for user {user.id}")
        
        return UserResponse(
            id=user.id,
            name=user_data.name,
            email=user_data.email,
            phone=None,
            avatar_url=None,
            created_at=user.created_at,
            updated_at=user.updated_at or user.created_at,
            settings=profile_data["settings"],
            total_revenue=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/signin", response_model=Token)
async def sign_in(login_data: LoginRequest):
    """Authenticate user and return access token"""
    try:
        # Authenticate with Supabase
        auth_response = supabase_anon.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        
        if not auth_response.session or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        session = auth_response.session
        user = auth_response.user
        
        # Get user profile
        profile_result = supabase_client.table("users").select("*").eq("id", user.id).execute()
        
        if profile_result.data:
            profile = profile_result.data[0]
            user_data = UserResponse(
                id=user.id,
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
            # Create missing profile
            profile_data = {
                "id": user.id,
                "name": user.user_metadata.get("name", user.email.split("@")[0]),
                "email": user.email,
                "settings": {},
                "total_revenue": 0
            }
            supabase_client.table("users").insert(profile_data).execute()
            
            user_data = UserResponse(
                id=user.id,
                name=profile_data["name"],
                email=user.email,
                phone=None,
                avatar_url=None,
                created_at=user.created_at,
                updated_at=user.updated_at or user.created_at,
                settings={},
                total_revenue=0
            )
        
        return Token(
            access_token=session.access_token,
            token_type="bearer",
            expires_in=session.expires_in or 3600,
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/signout", response_model=SuccessResponse)
async def sign_out(current_user: dict = Depends(get_current_user)):
    """Sign out current user"""
    try:
        # Note: In a real app, you might want to blacklist the token
        # For now, we'll just return success as the client will discard the token
        return SuccessResponse(message="Signed out successfully")
        
    except Exception as e:
        logger.error(f"Signout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign out"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token (if needed for extended sessions)"""
    try:
        # For Supabase, tokens are typically refreshed automatically
        # This endpoint can be used for custom token refresh logic if needed
        
        # For now, return current user data
        # In a real implementation, you'd refresh the token with Supabase
        
        return Token(
            access_token="refreshed_token_would_go_here",
            token_type="bearer", 
            expires_in=3600,
            user=UserResponse(**current_user)
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )
