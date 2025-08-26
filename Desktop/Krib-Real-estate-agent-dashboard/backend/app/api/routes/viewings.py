"""
Property Viewings API routes for long-term rental platform
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import uuid
from datetime import datetime, date, time

from app.models.agency_schemas import (
    ViewingCreate, ViewingUpdate, ViewingResponse,
    AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse,
    BulkAvailabilityCreate, ViewingStatus, ConfirmationStatus
)
from app.core.supabase_client import supabase_client
from app.api.dependencies import get_current_user, get_current_agent, verify_property_agent_access
from app.services.cache_service import cache_service
from app.models.schemas import SuccessResponse

router = APIRouter()

# =====================================================================
# VIEWING MANAGEMENT ROUTES
# =====================================================================

@router.post("/", response_model=ViewingResponse)
async def schedule_viewing(
    viewing_data: ViewingCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Schedule a property viewing"""
    try:
        # Verify property exists and is available
        property_result = supabase_client.table("properties").select("*").eq("id", viewing_data.property_id).execute()
        
        if not property_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        property_info = property_result.data[0]
        
        # Check if property is available
        if property_info.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not available for viewing"
            )
        
        # Auto-assign agent if not provided
        agent_id = viewing_data.agent_id
        if not agent_id and property_info.get("agent_id"):
            agent_id = property_info.get("agent_id")
        elif not agent_id and property_info.get("agency_id"):
            # Find an available agent from the agency
            available_agents = supabase_client.table("agents").select("id").eq("agency_id", property_info["agency_id"]).eq("status", "active").limit(1).execute()
            if available_agents.data:
                agent_id = available_agents.data[0]["id"]
        
        # Check for scheduling conflicts if agent is assigned
        if agent_id:
            conflicts = supabase_client.table("property_viewings").select("*").eq("agent_id", agent_id).eq("scheduled_date", viewing_data.scheduled_date.isoformat()).in_("status", ["scheduled", "confirmed"]).execute()
            
            for conflict in conflicts.data:
                conflict_time = datetime.strptime(conflict["scheduled_time"], "%H:%M:%S").time()
                # Check for time overlap (simplified check)
                if abs((datetime.combine(date.min, viewing_data.scheduled_time) - datetime.combine(date.min, conflict_time)).total_seconds()) < 3600:  # 1 hour buffer
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Agent is not available at the requested time"
                    )
        
        # Generate unique viewing ID
        viewing_id = str(uuid.uuid4())
        
        # Prepare viewing data for database
        viewing_record = {
            "id": viewing_id,
            "property_id": viewing_data.property_id,
            "agent_id": agent_id,
            "application_id": viewing_data.application_id,
            "scheduled_date": viewing_data.scheduled_date.isoformat(),
            "scheduled_time": viewing_data.scheduled_time.isoformat(),
            "duration_minutes": viewing_data.duration_minutes,
            "applicant_name": viewing_data.applicant_name,
            "applicant_email": viewing_data.applicant_email,
            "applicant_phone": viewing_data.applicant_phone,
            "number_of_attendees": viewing_data.number_of_attendees,
            "viewing_type": viewing_data.viewing_type.value,
            "meeting_platform": viewing_data.meeting_platform,
            "meeting_link": viewing_data.meeting_link,
            "meeting_password": viewing_data.meeting_password,
            "status": ViewingStatus.scheduled.value,
            "confirmation_status": ConfirmationStatus.pending.value,
            "follow_up_required": False,
            "follow_up_actions": [],
            "application_submitted": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("property_viewings").insert(viewing_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to schedule viewing"
            )
        
        created_viewing = result.data[0]
        
        # Schedule background tasks
        background_tasks.add_task(
            send_viewing_notifications,
            viewing_id,
            property_info,
            created_viewing
        )
        
        # TODO: Create Google Calendar event if agent has calendar integration
        
        return ViewingResponse(**created_viewing)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule viewing: {str(e)}"
        )


@router.get("/", response_model=List[ViewingResponse])
async def get_viewings(
    status_filter: Optional[str] = None,
    agent_id: Optional[str] = None,
    property_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
    current_agent: dict = Depends(get_current_agent)
):
    """Get viewings (filtered by agent's agency)"""
    try:
        query = supabase_client.table("property_viewings").select("*")
        
        # Apply agency filter
        if agent_id:
            query = query.eq("agent_id", agent_id)
        else:
            # Only show viewings for current agent's agency
            agency_agents = supabase_client.table("agents").select("id").eq("agency_id", current_agent["agency_id"]).execute()
            if agency_agents.data:
                agent_ids = [agent["id"] for agent in agency_agents.data]
                query = query.in_("agent_id", agent_ids)
        
        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if property_id:
            query = query.eq("property_id", property_id)
        if date_from:
            query = query.gte("scheduled_date", date_from.isoformat())
        if date_to:
            query = query.lte("scheduled_date", date_to.isoformat())
        
        # Apply pagination
        result = query.order("scheduled_date", desc=False).order("scheduled_time", desc=False).range(offset, offset + limit - 1).execute()
        
        return [ViewingResponse(**viewing_data) for viewing_data in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch viewings: {str(e)}"
        )


@router.get("/{viewing_id}", response_model=ViewingResponse)
async def get_viewing(
    viewing_id: str,
    current_agent: dict = Depends(get_current_agent)
):
    """Get a specific viewing"""
    try:
        result = supabase_client.table("property_viewings").select("*").eq("id", viewing_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viewing not found"
            )
        
        viewing = result.data[0]
        
        # Check if agent has access
        if viewing["agent_id"] != current_agent["id"]:
            # Check if viewing is for property in same agency
            property_result = supabase_client.table("properties").select("agency_id").eq("id", viewing["property_id"]).execute()
            if not property_result.data or property_result.data[0]["agency_id"] != current_agent["agency_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return ViewingResponse(**viewing)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch viewing: {str(e)}"
        )


@router.put("/{viewing_id}", response_model=ViewingResponse)
async def update_viewing(
    viewing_id: str,
    viewing_updates: ViewingUpdate,
    background_tasks: BackgroundTasks,
    current_agent: dict = Depends(get_current_agent)
):
    """Update a viewing (agent only)"""
    try:
        # Verify viewing exists and agent has access
        existing = supabase_client.table("property_viewings").select("*").eq("id", viewing_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viewing not found"
            )
        
        viewing = existing.data[0]
        
        # Check agent access
        if viewing["agent_id"] != current_agent["id"]:
            # Check if viewing is for property in same agency
            property_result = supabase_client.table("properties").select("agency_id").eq("id", viewing["property_id"]).execute()
            if not property_result.data or property_result.data[0]["agency_id"] != current_agent["agency_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Prepare update data
        update_data = {}
        for key, value in viewing_updates.dict().items():
            if value is not None:
                if key in ["scheduled_date"]:
                    update_data[key] = value.isoformat()
                elif key in ["scheduled_time"]:
                    update_data[key] = value.isoformat()
                elif hasattr(value, 'value'):  # Enum values
                    update_data[key] = value.value
                else:
                    update_data[key] = value
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Handle status changes
            if "status" in update_data:
                if update_data["status"] == ViewingStatus.confirmed.value:
                    update_data["confirmation_status"] = ConfirmationStatus.confirmed.value
                elif update_data["status"] == ViewingStatus.cancelled.value:
                    update_data["cancelled_at"] = datetime.utcnow().isoformat()
                    update_data["cancelled_by"] = "agent"
            
            # Update in database
            result = supabase_client.table("property_viewings").update(update_data).eq("id", viewing_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update viewing"
                )
            
            # Schedule notifications if status changed
            if "status" in update_data:
                background_tasks.add_task(
                    send_viewing_status_notification,
                    viewing_id,
                    update_data["status"],
                    result.data[0]
                )
        else:
            result = existing
        
        return ViewingResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update viewing: {str(e)}"
        )


@router.post("/{viewing_id}/confirm", response_model=ViewingResponse)
async def confirm_viewing(
    viewing_id: str,
    current_agent: dict = Depends(get_current_agent)
):
    """Confirm a viewing"""
    try:
        # Verify viewing exists and agent has access
        existing = supabase_client.table("property_viewings").select("*").eq("id", viewing_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viewing not found"
            )
        
        viewing = existing.data[0]
        
        if viewing["agent_id"] != current_agent["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if viewing["status"] not in [ViewingStatus.scheduled.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only scheduled viewings can be confirmed"
            )
        
        # Update status
        result = supabase_client.table("property_viewings").update({
            "status": ViewingStatus.confirmed.value,
            "confirmation_status": ConfirmationStatus.confirmed.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", viewing_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm viewing"
            )
        
        return ViewingResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm viewing: {str(e)}"
        )


@router.post("/{viewing_id}/cancel", response_model=ViewingResponse)
async def cancel_viewing(
    viewing_id: str,
    cancellation_reason: Optional[str] = None,
    current_agent: dict = Depends(get_current_agent)
):
    """Cancel a viewing"""
    try:
        # Verify viewing exists and agent has access
        existing = supabase_client.table("property_viewings").select("*").eq("id", viewing_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viewing not found"
            )
        
        viewing = existing.data[0]
        
        if viewing["agent_id"] != current_agent["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if viewing["status"] in [ViewingStatus.cancelled.value, ViewingStatus.completed.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Viewing cannot be cancelled"
            )
        
        # Update status
        result = supabase_client.table("property_viewings").update({
            "status": ViewingStatus.cancelled.value,
            "cancelled_by": "agent",
            "cancellation_reason": cancellation_reason,
            "cancelled_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", viewing_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel viewing"
            )
        
        return ViewingResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel viewing: {str(e)}"
        )

# =====================================================================
# AGENT AVAILABILITY ROUTES
# =====================================================================

@router.post("/availability", response_model=AvailabilityResponse)
async def create_availability(
    availability_data: AvailabilityCreate,
    current_agent: dict = Depends(get_current_agent)
):
    """Create agent availability slot"""
    try:
        # Verify agent can create availability for themselves or they're managing another agent
        if availability_data.agent_id != current_agent["id"]:
            if current_agent["role"] not in ["manager", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create availability for yourself"
                )
        
        # Check for conflicts
        conflicts = supabase_client.table("agent_availability").select("*").eq("agent_id", availability_data.agent_id).eq("date", availability_data.date.isoformat()).execute()
        
        for conflict in conflicts.data:
            conflict_start = datetime.strptime(conflict["start_time"], "%H:%M:%S").time()
            conflict_end = datetime.strptime(conflict["end_time"], "%H:%M:%S").time()
            
            # Check for time overlap
            if (availability_data.start_time < conflict_end and availability_data.end_time > conflict_start):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Availability slot conflicts with existing slot"
                )
        
        # Generate unique availability ID
        availability_id = str(uuid.uuid4())
        
        # Prepare availability data for database
        availability_record = {
            "id": availability_id,
            "agent_id": availability_data.agent_id,
            "date": availability_data.date.isoformat(),
            "start_time": availability_data.start_time.isoformat(),
            "end_time": availability_data.end_time.isoformat(),
            "is_available": True,
            "max_viewings": availability_data.max_viewings,
            "current_bookings": 0,
            "slot_type": availability_data.slot_type.value,
            "recurring_pattern": availability_data.recurring_pattern.value,
            "preferred_areas": availability_data.preferred_areas,
            "travel_buffer_minutes": availability_data.travel_buffer_minutes,
            "notes": availability_data.notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("agent_availability").insert(availability_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create availability"
            )
        
        return AvailabilityResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create availability: {str(e)}"
        )


@router.get("/availability", response_model=List[AvailabilityResponse])
async def get_agent_availability(
    agent_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_agent: dict = Depends(get_current_agent)
):
    """Get agent availability slots"""
    try:
        # Default to current agent if no agent_id provided
        if not agent_id:
            agent_id = current_agent["id"]
        
        # Check if requesting availability for another agent in same agency
        if agent_id != current_agent["id"]:
            other_agent = supabase_client.table("agents").select("agency_id").eq("id", agent_id).execute()
            if not other_agent.data or other_agent.data[0]["agency_id"] != current_agent["agency_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view availability for agents in your agency"
                )
        
        query = supabase_client.table("agent_availability").select("*").eq("agent_id", agent_id)
        
        # Apply date filters
        if date_from:
            query = query.gte("date", date_from.isoformat())
        if date_to:
            query = query.lte("date", date_to.isoformat())
        
        result = query.order("date").order("start_time").execute()
        
        return [AvailabilityResponse(**availability_data) for availability_data in result.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch availability: {str(e)}"
        )


@router.post("/availability/bulk", response_model=List[AvailabilityResponse])
async def create_bulk_availability(
    bulk_data: BulkAvailabilityCreate,
    current_agent: dict = Depends(get_current_agent)
):
    """Create bulk availability slots for multiple days"""
    try:
        # Verify agent can create availability for the specified agent
        if bulk_data.agent_id != current_agent["id"]:
            if current_agent["role"] not in ["manager", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create availability for yourself"
                )
        
        availability_records = []
        current_date = bulk_data.start_date
        
        while current_date <= bulk_data.end_date:
            # Check if this day is in the specified days of week
            if current_date.weekday() in bulk_data.days_of_week:
                # Check for conflicts
                conflicts = supabase_client.table("agent_availability").select("*").eq("agent_id", bulk_data.agent_id).eq("date", current_date.isoformat()).execute()
                
                has_conflict = False
                for conflict in conflicts.data:
                    conflict_start = datetime.strptime(conflict["start_time"], "%H:%M:%S").time()
                    conflict_end = datetime.strptime(conflict["end_time"], "%H:%M:%S").time()
                    
                    # Check for time overlap
                    if (bulk_data.start_time < conflict_end and bulk_data.end_time > conflict_start):
                        has_conflict = True
                        break
                
                # Only create if no conflict
                if not has_conflict:
                    availability_record = {
                        "id": str(uuid.uuid4()),
                        "agent_id": bulk_data.agent_id,
                        "date": current_date.isoformat(),
                        "start_time": bulk_data.start_time.isoformat(),
                        "end_time": bulk_data.end_time.isoformat(),
                        "is_available": True,
                        "max_viewings": bulk_data.max_viewings,
                        "current_bookings": 0,
                        "slot_type": bulk_data.slot_type.value,
                        "recurring_pattern": "none",
                        "preferred_areas": bulk_data.preferred_areas,
                        "travel_buffer_minutes": bulk_data.travel_buffer_minutes,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    availability_records.append(availability_record)
            
            # Move to next day
            current_date = date.fromordinal(current_date.toordinal() + 1)
        
        if not availability_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No availability slots could be created (conflicts or no valid days)"
            )
        
        # Insert all records
        result = supabase_client.table("agent_availability").insert(availability_records).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create availability slots"
            )
        
        return [AvailabilityResponse(**availability_data) for availability_data in result.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk availability: {str(e)}"
        )


# =====================================================================
# BACKGROUND TASKS
# =====================================================================

async def send_viewing_notifications(viewing_id: str, property_info: dict, viewing_data: dict):
    """Send notifications when a viewing is scheduled"""
    try:
        # Send email to agent
        # Send SMS to applicant
        # Create calendar event
        print(f"Sending viewing notifications for viewing {viewing_id}")
    except Exception as e:
        print(f"Failed to send viewing notifications for viewing {viewing_id}: {e}")


async def send_viewing_status_notification(viewing_id: str, new_status: str, viewing_data: dict):
    """Send notifications when viewing status changes"""
    try:
        # Send appropriate notifications based on status
        print(f"Sending viewing status notification for viewing {viewing_id}: {new_status}")
    except Exception as e:
        print(f"Failed to send viewing status notification for viewing {viewing_id}: {e}")
