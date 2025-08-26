"""
Agencies API routes for long-term rental platform
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.agency_schemas import (
    AgencyCreate, AgencyUpdate, AgencyResponse,
    AgentCreate, AgentUpdate, AgentResponse,
    AgencyDashboardStats, AgentPerformance,
    BulkAgentUpdate
)
from app.core.supabase_client import supabase_client
from app.api.dependencies import get_current_user, get_current_agent
from app.services.cache_service import cache_service

router = APIRouter()

# =====================================================================
# AGENCY MANAGEMENT ROUTES
# =====================================================================

@router.post("/", response_model=AgencyResponse)
async def create_agency(
    agency_data: AgencyCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Create a new real estate agency"""
    try:
        # Generate unique agency ID
        agency_id = str(uuid.uuid4())
        
        # Prepare agency data for database
        agency_record = {
            "id": agency_id,
            "name": agency_data.name,
            "license_number": agency_data.license_number,
            "license_expiry_date": agency_data.license_expiry_date.isoformat(),
            "head_office_address": agency_data.head_office_address,
            "emirates": agency_data.emirates,
            "phone": agency_data.phone,
            "email": agency_data.email,
            "website_url": agency_data.website_url,
            "establishment_year": agency_data.establishment_year,
            "default_commission_rate": float(agency_data.default_commission_rate),
            "subscription_plan": agency_data.subscription_plan.value,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("agencies").insert(agency_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agency"
            )
        
        created_agency = result.data[0]
        
        # Create the first admin agent for the user who created the agency
        admin_agent_record = {
            "id": str(uuid.uuid4()),
            "agency_id": agency_id,
            "user_id": current_user["id"],
            "name": current_user.get("name", "Agency Admin"),
            "email": current_user["email"],
            "phone": agency_data.phone,
            "role": "admin",
            "permissions": ["manage_agency", "manage_agents", "manage_properties", "manage_applications"],
            "commission_rate": float(agency_data.default_commission_rate),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert admin agent
        agent_result = supabase_client.table("agents").insert(admin_agent_record).execute()
        
        if not agent_result.data:
            # If agent creation fails, still return agency but log warning
            print(f"Warning: Failed to create admin agent for agency {agency_id}")
        
        return AgencyResponse(**created_agency)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agency: {str(e)}"
        )


@router.get("/", response_model=List[AgencyResponse])
async def get_agencies(
    status_filter: Optional[str] = None,
    emirates: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get agencies (for admin users) or current user's agencies"""
    try:
        # Get agencies the current user has access to
        query = supabase_client.table("agencies").select("*")
        
        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if emirates:
            query = query.eq("emirates", emirates)
        
        result = query.order("created_at", desc=True).execute()
        
        return [AgencyResponse(**agency_data) for agency_data in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agencies: {str(e)}"
        )


@router.get("/{agency_id}", response_model=AgencyResponse)
async def get_agency(
    agency_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific agency"""
    try:
        result = supabase_client.table("agencies").select("*").eq("id", agency_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agency not found"
            )
        
        return AgencyResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agency: {str(e)}"
        )


@router.put("/{agency_id}", response_model=AgencyResponse)
async def update_agency(
    agency_id: str,
    agency_updates: AgencyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an agency (admin only)"""
    try:
        # Verify agency exists and user has permission
        existing = supabase_client.table("agencies").select("*").eq("id", agency_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agency not found"
            )
        
        # Prepare update data (only include non-None values)
        update_data = {k: v for k, v in agency_updates.dict().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
        
            # Update in database
            result = supabase_client.table("agencies").update(update_data).eq("id", agency_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update agency"
                )
        else:
            result = existing
        
        return AgencyResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agency: {str(e)}"
        )


@router.get("/{agency_id}/dashboard", response_model=AgencyDashboardStats)
async def get_agency_dashboard(
    agency_id: str,
    current_agent: dict = Depends(get_current_agent)
):
    """Get agency dashboard statistics"""
    try:
        # Check cache first
        cached_stats = await cache_service.get_analytics_data(agency_id, "dashboard")
        if cached_stats:
            return AgencyDashboardStats(**cached_stats)
        
        # Fetch dashboard statistics
        stats = {}
        
        # Total properties
        properties_result = supabase_client.table("properties").select("id", count="exact").eq("agency_id", agency_id).execute()
        stats["total_properties"] = properties_result.count or 0
        
        # Active leases
        leases_result = supabase_client.table("lease_agreements").select("id", count="exact").eq("agency_id", agency_id).eq("status", "active").execute()
        stats["total_active_leases"] = leases_result.count or 0
        
        # Pending applications
        applications_result = supabase_client.table("tenant_applications").select("id", count="exact").in_("status", ["submitted", "under_review", "documents_pending"]).execute()
        stats["pending_applications"] = applications_result.count or 0
        
        # Total agents
        agents_result = supabase_client.table("agents").select("id", count="exact").eq("agency_id", agency_id).eq("status", "active").execute()
        stats["total_agents"] = agents_result.count or 0
        
        # Set default values for other stats
        stats.update({
            "monthly_commissions": 0.0,
            "applications_this_month": 0,
            "application_conversion_rate": 0.0,
            "average_processing_time": 0.0,
            "monthly_target_progress": 0.0,
            "quarterly_revenue": 0.0
        })
        
        dashboard_stats = AgencyDashboardStats(**stats)
        
        # Cache the results
        await cache_service.cache_analytics_data(agency_id, "dashboard", dashboard_stats.dict())
        
        return dashboard_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agency dashboard: {str(e)}"
        )

# =====================================================================
# AGENT MANAGEMENT ROUTES
# =====================================================================

@router.post("/{agency_id}/agents", response_model=AgentResponse)
async def create_agent(
    agency_id: str,
    agent_data: AgentCreate,
    current_agent: dict = Depends(get_current_agent)
):
    """Add a new agent to the agency"""
    try:
        # Verify agency exists
        agency_result = supabase_client.table("agencies").select("*").eq("id", agency_id).execute()
        if not agency_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agency not found"
            )
        
        # Generate unique agent ID
        agent_id = str(uuid.uuid4())
        
        # Prepare agent data for database
        agent_record = {
            "id": agent_id,
            "agency_id": agency_id,
            "name": agent_data.name,
            "email": agent_data.email,
            "phone": agent_data.phone,
            "nationality": agent_data.nationality,
            "languages_spoken": agent_data.languages_spoken,
            "license_number": agent_data.license_number,
            "license_expiry_date": agent_data.license_expiry_date.isoformat() if agent_data.license_expiry_date else None,
            "years_experience": agent_data.years_experience,
            "role": agent_data.role.value,
            "permissions": agent_data.permissions,
            "assigned_territories": agent_data.assigned_territories,
            "property_specializations": agent_data.property_specializations,
            "commission_rate": float(agent_data.commission_rate),
            "monthly_target": float(agent_data.monthly_target),
            "annual_target": float(agent_data.annual_target),
            "whatsapp_number": agent_data.whatsapp_number,
            "preferred_contact_method": agent_data.preferred_contact_method.value,
            "timezone": agent_data.timezone,
            "working_hours": agent_data.working_hours.dict(),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("agents").insert(agent_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent"
            )
        
        created_agent = result.data[0]
        
        return AgentResponse(**created_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("/{agency_id}/agents", response_model=List[AgentResponse])
async def get_agency_agents(
    agency_id: str,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    current_agent: dict = Depends(get_current_agent)
):
    """Get all agents for an agency"""
    try:
        query = supabase_client.table("agents").select("*").eq("agency_id", agency_id)
        
        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if role_filter:
            query = query.eq("role", role_filter)
        
        result = query.order("created_at", desc=True).execute()
        
        return [AgentResponse(**agent_data) for agent_data in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agents: {str(e)}"
        )


@router.get("/{agency_id}/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agency_id: str,
    agent_id: str,
    current_agent: dict = Depends(get_current_agent)
):
    """Get a specific agent"""
    try:
        result = supabase_client.table("agents").select("*").eq("id", agent_id).eq("agency_id", agency_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return AgentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agent: {str(e)}"
        )


@router.put("/{agency_id}/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agency_id: str,
    agent_id: str,
    agent_updates: AgentUpdate,
    current_agent: dict = Depends(get_current_agent)
):
    """Update an agent"""
    try:
        # Verify agent exists
        existing = supabase_client.table("agents").select("*").eq("id", agent_id).eq("agency_id", agency_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Prepare update data (only include non-None values)
        update_data = {}
        for key, value in agent_updates.dict().items():
            if value is not None:
                if key == "working_hours" and hasattr(value, 'dict'):
                    update_data[key] = value.dict()
                elif hasattr(value, 'value'):  # Enum values
                    update_data[key] = value.value
                else:
                    update_data[key] = value
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in database
            result = supabase_client.table("agents").update(update_data).eq("id", agent_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update agent"
                )
        else:
            result = existing
        
        return AgentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.get("/{agency_id}/performance", response_model=List[AgentPerformance])
async def get_agency_performance(
    agency_id: str,
    period: str = "month",  # month, quarter, year
    current_agent: dict = Depends(get_current_agent)
):
    """Get performance statistics for all agents in agency"""
    try:
        # Check cache first
        cache_key = f"{agency_id}_{period}"
        cached_performance = await cache_service.get_analytics_data(cache_key, "performance")
        if cached_performance:
            return [AgentPerformance(**perf) for perf in cached_performance]
        
        # Get all agents for the agency
        agents_result = supabase_client.table("agents").select("*").eq("agency_id", agency_id).eq("status", "active").execute()
        
        performance_data = []
        for agent in agents_result.data:
            # For now, return default performance data
            # In a real implementation, you'd calculate actual performance metrics
            perf = AgentPerformance(
                agent_id=agent["id"],
                agent_name=agent["name"],
                deals_this_month=0,
                deals_this_quarter=0,
                commission_this_month=0.0,
                commission_this_quarter=0.0,
                target_achievement_percentage=0.0,
                average_deal_size=0.0,
                conversion_rate=0.0,
                properties_managed=0,
                active_applications=0,
                scheduled_viewings=0
            )
            performance_data.append(perf)
        
        # Cache the results
        await cache_service.cache_analytics_data(cache_key, "performance", [p.dict() for p in performance_data])
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agency performance: {str(e)}"
        )


@router.put("/{agency_id}/agents/bulk", response_model=List[AgentResponse])
async def bulk_update_agents(
    agency_id: str,
    bulk_update: BulkAgentUpdate,
    current_agent: dict = Depends(get_current_agent)
):
    """Bulk update multiple agents"""
    try:
        if not bulk_update.agent_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No agent IDs provided"
            )
        
        # Prepare update data
        update_data = {}
        if bulk_update.role:
            update_data["role"] = bulk_update.role.value
        if bulk_update.commission_rate is not None:
            update_data["commission_rate"] = float(bulk_update.commission_rate)
        if bulk_update.assigned_territories:
            update_data["assigned_territories"] = bulk_update.assigned_territories
        if bulk_update.status:
            update_data["status"] = bulk_update.status.value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update agents
        result = supabase_client.table("agents").update(update_data).in_("id", bulk_update.agent_ids).eq("agency_id", agency_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agents"
            )
        
        return [AgentResponse(**agent_data) for agent_data in result.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update agents: {str(e)}"
        )
