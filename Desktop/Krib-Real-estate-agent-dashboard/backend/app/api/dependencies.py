"""
FastAPI dependencies for authentication and authorization
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        User data dictionary
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token with Supabase
        user_response = supabase_client.auth.get_user(token)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        
        # Get additional user profile data
        profile_result = supabase_client.table("users").select("*").eq("id", user.id).execute()
        
        if profile_result.data:
            # Return merged user data
            profile = profile_result.data[0]
            return {
                "id": user.id,
                "email": user.email,
                "name": profile.get("name", user.user_metadata.get("name", "")),
                "phone": profile.get("phone"),
                "avatar_url": profile.get("avatar_url"),
                "settings": profile.get("settings", {}),
                "total_revenue": profile.get("total_revenue", 0),
                "created_at": profile.get("created_at"),
                "updated_at": profile.get("updated_at")
            }
        else:
            # Create profile if it doesn't exist (for OAuth users)
            profile_data = {
                "id": user.id,
                "name": user.user_metadata.get("full_name") or user.user_metadata.get("name") or user.email.split("@")[0],
                "email": user.email,
                "settings": {},
                "total_revenue": 0
            }
            
            # Insert new profile
            supabase_client.table("users").insert(profile_data).execute()
            
            return {
                "id": user.id,
                "email": user.email,
                "name": profile_data["name"],
                "phone": None,
                "avatar_url": None,
                "settings": {},
                "total_revenue": 0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current active user (add additional checks if needed)
    
    Args:
        current_user: User data from get_current_user
        
    Returns:
        Active user data
        
    Raises:
        HTTPException: If user is inactive/suspended
    """
    # Add any additional checks here (e.g., user status, subscription, etc.)
    # For now, just return the user
    return current_user


async def verify_property_ownership(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify that the current user owns the specified property
    
    Args:
        property_id: Property ID to verify
        current_user: Current authenticated user
        
    Returns:
        Property data if user owns it
        
    Raises:
        HTTPException: If property not found or user doesn't own it
    """
    try:
        result = supabase_client.table("properties").select("*").eq("id", property_id).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found or access denied"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Property ownership verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify property ownership"
        )


async def verify_booking_access(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify that the current user has access to the specified booking
    (either owns the property or is the guest)
    
    Args:
        booking_id: Booking ID to verify
        current_user: Current authenticated user
        
    Returns:
        Booking data if user has access
        
    Raises:
        HTTPException: If booking not found or user doesn't have access
    """
    try:
        # Get booking with property information
        result = supabase_client.table("bookings").select("""
            *,
            properties!inner(user_id)
        """).eq("id", booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        booking = result.data[0]
        
        # Check if user owns the property
        if booking["properties"]["user_id"] == current_user["id"]:
            return booking
        
        # Check if user is the guest (by email)
        if booking["guest_email"] == current_user["email"]:
            return booking
        
        # User has no access to this booking
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this booking"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking access verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify booking access"
        )


async def get_current_agent(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current authenticated agent from user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Agent data with agency information
        
    Raises:
        HTTPException: If user is not an active agent
    """
    try:
        # Get agent profile linked to this user
        agent_result = supabase_client.table("agents").select("*").eq("user_id", current_user["id"]).eq("status", "active").execute()
        
        if not agent_result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an active agent"
            )
        
        agent = agent_result.data[0]
        
        # Get agency info
        agency_result = supabase_client.table("agencies").select("*").eq("id", agent["agency_id"]).execute()
        
        if not agency_result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent's agency not found"
            )
        
        agency = agency_result.data[0]
        
        return {
            **agent,
            "agency_name": agency["name"],
            "agency_emirates": agency["emirates"],
            "agency_status": agency["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Failed to verify agent credentials"
        )


async def verify_application_access(
    application_id: str,
    current_agent: dict = Depends(get_current_agent)
) -> dict:
    """
    Verify agent has access to a specific application
    
    Args:
        application_id: Application ID to verify
        current_agent: Current authenticated agent
        
    Returns:
        Application data if agent has access
        
    Raises:
        HTTPException: If application not found or agent doesn't have access
    """
    try:
        # Get application with property info
        application_result = supabase_client.table("tenant_applications").select("""
            *,
            properties!inner(agent_id, agency_id)
        """).eq("id", application_id).execute()
        
        if not application_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        application = application_result.data[0]
        
        # Check if agent has access (same agency or assigned agent)
        if (application["agent_id"] != current_agent["id"] and 
            application["properties"]["agency_id"] != current_agent["agency_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application access verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify application access"
        )


async def verify_property_agent_access(
    property_id: str,
    current_agent: dict = Depends(get_current_agent)
) -> dict:
    """
    Verify agent has access to a specific property
    
    Args:
        property_id: Property ID to verify
        current_agent: Current authenticated agent
        
    Returns:
        Property data if agent has access
        
    Raises:
        HTTPException: If property not found or agent doesn't have access
    """
    try:
        # Get property
        property_result = supabase_client.table("properties").select("*").eq("id", property_id).execute()
        
        if not property_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        property_info = property_result.data[0]
        
        # Check if agent has access (same agency or assigned agent)
        if (property_info.get("agent_id") != current_agent["id"] and 
            property_info.get("agency_id") != current_agent["agency_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return property_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Property access verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify property access"
        )


def require_permissions(required_permissions: list):
    """
    Decorator to require specific permissions
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        Dependency function that checks permissions
    """
    def permission_checker(current_agent: dict = Depends(get_current_agent)):
        agent_permissions = current_agent.get("permissions", [])
        
        # Admin role has all permissions
        if current_agent.get("role") == "admin":
            return current_agent
        
        # Check if agent has required permissions
        for permission in required_permissions:
            if permission not in agent_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return current_agent
    
    return permission_checker


def require_role(required_roles: list):
    """
    Decorator to require specific roles
    
    Args:
        required_roles: List of acceptable roles
        
    Returns:
        Dependency function that checks roles
    """
    def role_checker(current_agent: dict = Depends(get_current_agent)):
        agent_role = current_agent.get("role")
        
        if agent_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(required_roles)}"
            )
        
        return current_agent
    
    return role_checker
