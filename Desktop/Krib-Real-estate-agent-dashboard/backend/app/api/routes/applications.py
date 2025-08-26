"""
Tenant Applications API routes for long-term rental platform
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from typing import List, Optional
import uuid
from datetime import datetime, date

from app.models.application_schemas import (
    TenantApplicationCreate, TenantApplicationUpdate, TenantApplicationResponse,
    ApplicationDocumentCreate, ApplicationDocumentUpdate, ApplicationDocumentResponse,
    ApplicationPipelineStats, ApplicationsFilter, BulkApplicationUpdate,
    ApplicationStatus, DocumentType, VerificationStatus
)
from app.core.supabase_client import supabase_client
from app.api.dependencies import get_current_user, get_current_agent
from app.services.cache_service import cache_service
from app.models.schemas import SuccessResponse

router = APIRouter()

# =====================================================================
# APPLICATION MANAGEMENT ROUTES
# =====================================================================

@router.post("/", response_model=TenantApplicationResponse)
async def create_application(
    application_data: TenantApplicationCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Submit a new tenant application"""
    try:
        # Verify property exists and is available
        property_result = supabase_client.table("properties").select("*").eq("id", application_data.property_id).execute()
        
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
                detail="Property is not available for rental"
            )
        
        # Check if user already has a pending application for this property
        existing_apps = supabase_client.table("tenant_applications").select("*").eq("property_id", application_data.property_id).eq("primary_applicant_email", application_data.primary_applicant_email).in_("status", ["submitted", "under_review", "documents_pending"]).execute()
        
        if existing_apps.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pending application for this property"
            )
        
        # Generate unique application ID
        application_id = str(uuid.uuid4())
        
        # Prepare application data for database
        application_record = {
            "id": application_id,
            "property_id": application_data.property_id,
            "agent_id": application_data.agent_id,
            "primary_applicant_name": application_data.primary_applicant_name,
            "primary_applicant_email": application_data.primary_applicant_email,
            "primary_applicant_phone": application_data.primary_applicant_phone,
            "primary_applicant_nationality": application_data.primary_applicant_nationality,
            "primary_applicant_passport": application_data.primary_applicant_passport,
            "primary_applicant_emirates_id": application_data.primary_applicant_emirates_id,
            "employer_name": application_data.employer_name,
            "job_title": application_data.job_title,
            "monthly_income": float(application_data.monthly_income) if application_data.monthly_income else None,
            "employment_type": application_data.employment_type.value if application_data.employment_type else None,
            "work_permit_expiry": application_data.work_permit_expiry.isoformat() if application_data.work_permit_expiry else None,
            "desired_move_in_date": application_data.desired_move_in_date.isoformat(),
            "lease_duration_months": application_data.lease_duration_months,
            "maximum_budget": float(application_data.maximum_budget),
            "furnished_preference": application_data.furnished_preference.value,
            "current_address": application_data.current_address,
            "current_monthly_rent": float(application_data.current_monthly_rent) if application_data.current_monthly_rent else None,
            "reason_for_moving": application_data.reason_for_moving,
            "notice_period_days": application_data.notice_period_days,
            "family_size": application_data.family_size,
            "children_count": application_data.children_count,
            "pet_ownership": application_data.pet_ownership,
            "pet_details": application_data.pet_details,
            "previous_landlord_name": application_data.previous_landlord_name,
            "previous_landlord_phone": application_data.previous_landlord_phone,
            "employer_reference_name": application_data.employer_reference_name,
            "employer_reference_phone": application_data.employer_reference_phone,
            "status": ApplicationStatus.submitted.value,
            "submitted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("tenant_applications").insert(application_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create application"
            )
        
        created_application = result.data[0]
        
        # Schedule background notification tasks
        background_tasks.add_task(
            send_application_notifications,
            application_id,
            property_info,
            created_application
        )
        
        return TenantApplicationResponse(**created_application)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )


@router.get("/", response_model=List[TenantApplicationResponse])
async def get_applications(
    status_filter: Optional[str] = None,
    agent_id: Optional[str] = None,
    property_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_agent: dict = Depends(get_current_agent)
):
    """Get applications (filtered by agent's agency)"""
    try:
        query = supabase_client.table("tenant_applications").select("*")
        
        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if agent_id:
            query = query.eq("agent_id", agent_id)
        if property_id:
            query = query.eq("property_id", property_id)
        
        # Apply pagination
        result = query.order("submitted_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return [TenantApplicationResponse(**app_data) for app_data in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch applications: {str(e)}"
        )


@router.get("/pipeline", response_model=ApplicationPipelineStats)
async def get_application_pipeline(
    agent_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_agent: dict = Depends(get_current_agent)
):
    """Get application pipeline statistics"""
    try:
        # Check cache first
        cache_key = f"pipeline_{agent_id or 'all'}_{date_from}_{date_to}"
        cached_stats = await cache_service.get_analytics_data(current_agent["agency_id"], cache_key)
        if cached_stats:
            return ApplicationPipelineStats(**cached_stats)
        
        # Build base query
        base_query = supabase_client.table("tenant_applications").select("status", count="exact")
        
        if agent_id:
            base_query = base_query.eq("agent_id", agent_id)
        if date_from:
            base_query = base_query.gte("submitted_at", date_from.isoformat())
        if date_to:
            base_query = base_query.lte("submitted_at", date_to.isoformat())
        
        # Get total applications
        total_result = base_query.execute()
        total_applications = total_result.count or 0
        
        # Get applications by status
        stats = {"total_applications": total_applications}
        
        for status_value in ApplicationStatus:
            status_result = base_query.eq("status", status_value.value).execute()
            stats[status_value.value] = status_result.count or 0
        
        # Calculate conversion rate (approved / total)
        conversion_rate = 0.0
        if total_applications > 0:
            conversion_rate = (stats.get("approved", 0) / total_applications) * 100
        
        stats["conversion_rate"] = conversion_rate
        stats["average_processing_time"] = 5.2  # Default value, calculate from actual data
        
        pipeline_stats = ApplicationPipelineStats(**stats)
        
        # Cache the results
        await cache_service.cache_analytics_data(current_agent["agency_id"], cache_key, pipeline_stats.dict())
        
        return pipeline_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pipeline stats: {str(e)}"
        )


@router.get("/{application_id}", response_model=TenantApplicationResponse)
async def get_application(
    application_id: str,
    current_agent: dict = Depends(get_current_agent)
):
    """Get a specific application"""
    try:
        result = supabase_client.table("tenant_applications").select("*").eq("id", application_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return TenantApplicationResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch application: {str(e)}"
        )


@router.put("/{application_id}", response_model=TenantApplicationResponse)
async def update_application(
    application_id: str,
    application_updates: TenantApplicationUpdate,
    background_tasks: BackgroundTasks,
    current_agent: dict = Depends(get_current_agent)
):
    """Update an application (agent only)"""
    try:
        # Verify application exists
        existing = supabase_client.table("tenant_applications").select("*").eq("id", application_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Prepare update data
        update_data = {}
        for key, value in application_updates.dict().items():
            if value is not None:
                if hasattr(value, 'value'):  # Enum values
                    update_data[key] = value.value
                else:
                    update_data[key] = value
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Handle status changes
            if "status" in update_data:
                if update_data["status"] == ApplicationStatus.approved.value:
                    update_data["approved_at"] = datetime.utcnow().isoformat()
                elif update_data["status"] == ApplicationStatus.under_review.value:
                    update_data["reviewed_at"] = datetime.utcnow().isoformat()
            
            # Update in database
            result = supabase_client.table("tenant_applications").update(update_data).eq("id", application_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update application"
                )
            
            # Schedule notification if status changed
            if "status" in update_data:
                background_tasks.add_task(
                    send_status_change_notification,
                    application_id,
                    update_data["status"],
                    result.data[0]
                )
        else:
            result = existing
        
        return TenantApplicationResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )


@router.put("/bulk", response_model=List[TenantApplicationResponse])
async def bulk_update_applications(
    bulk_update: BulkApplicationUpdate,
    current_agent: dict = Depends(get_current_agent)
):
    """Bulk update multiple applications"""
    try:
        if not bulk_update.application_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No application IDs provided"
            )
        
        # Prepare update data
        update_data = {}
        if bulk_update.status:
            update_data["status"] = bulk_update.status.value
        if bulk_update.agent_id:
            update_data["agent_id"] = bulk_update.agent_id
        if bulk_update.review_notes:
            update_data["review_notes"] = [bulk_update.review_notes]
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update applications
        result = supabase_client.table("tenant_applications").update(update_data).in_("id", bulk_update.application_ids).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update applications"
            )
        
        return [TenantApplicationResponse(**app_data) for app_data in result.data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update applications: {str(e)}"
        )

# =====================================================================
# DOCUMENT MANAGEMENT ROUTES
# =====================================================================

@router.post("/{application_id}/documents", response_model=ApplicationDocumentResponse)
async def upload_document(
    application_id: str,
    document_type: DocumentType,
    document_name: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a document for an application"""
    try:
        # Verify application exists
        app_result = supabase_client.table("tenant_applications").select("*").eq("id", application_id).execute()
        
        if not app_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Validate file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF and image files are allowed"
            )
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        
        # TODO: Upload file to storage (Supabase Storage or S3)
        # For now, we'll use a placeholder URL
        file_url = f"https://storage.example.com/documents/{application_id}/{file.filename}"
        
        # Create document record
        document_record = {
            "id": str(uuid.uuid4()),
            "application_id": application_id,
            "document_type": document_type.value,
            "document_name": document_name,
            "file_url": file_url,
            "file_size": file.size,
            "mime_type": file.content_type,
            "uploaded_by": "applicant",  # TODO: Determine based on current user
            "verification_status": VerificationStatus.pending.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        result = supabase_client.table("application_documents").insert(document_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document record"
            )
        
        # Update application status to documents_pending if it was submitted
        if app_result.data[0]["status"] == ApplicationStatus.submitted.value:
            supabase_client.table("tenant_applications").update({
                "status": ApplicationStatus.documents_pending.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", application_id).execute()
        
        return ApplicationDocumentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{application_id}/documents", response_model=List[ApplicationDocumentResponse])
async def get_application_documents(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all documents for an application"""
    try:
        result = supabase_client.table("application_documents").select("*").eq("application_id", application_id).order("created_at", desc=True).execute()
        
        return [ApplicationDocumentResponse(**doc_data) for doc_data in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}"
        )


@router.put("/{application_id}/documents/{document_id}", response_model=ApplicationDocumentResponse)
async def update_document(
    application_id: str,
    document_id: str,
    document_updates: ApplicationDocumentUpdate,
    current_agent: dict = Depends(get_current_agent)
):
    """Update document verification status (agent only)"""
    try:
        # Verify document exists
        existing = supabase_client.table("application_documents").select("*").eq("id", document_id).eq("application_id", application_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Prepare update data
        update_data = {}
        for key, value in document_updates.dict().items():
            if value is not None:
                if hasattr(value, 'value'):  # Enum values
                    update_data[key] = value.value
                else:
                    update_data[key] = value
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Set verification timestamp and agent if status is being verified
            if "verification_status" in update_data and update_data["verification_status"] == VerificationStatus.verified.value:
                update_data["verified_at"] = datetime.utcnow().isoformat()
                update_data["verified_by_agent_id"] = current_agent["id"]
            
            # Update in database
            result = supabase_client.table("application_documents").update(update_data).eq("id", document_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update document"
                )
        else:
            result = existing
        
        return ApplicationDocumentResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{application_id}/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(
    application_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document"""
    try:
        # Verify document exists
        existing = supabase_client.table("application_documents").select("*").eq("id", document_id).eq("application_id", application_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from database
        supabase_client.table("application_documents").delete().eq("id", document_id).execute()
        
        # TODO: Delete file from storage
        
        return SuccessResponse(message="Document deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

# =====================================================================
# BACKGROUND TASKS
# =====================================================================

async def send_application_notifications(application_id: str, property_info: dict, application_data: dict):
    """Send notifications when a new application is submitted"""
    try:
        # Send email to property agent
        # Send SMS to applicant
        # Create in-app notifications
        print(f"Sending notifications for application {application_id}")
    except Exception as e:
        print(f"Failed to send notifications for application {application_id}: {e}")


async def send_status_change_notification(application_id: str, new_status: str, application_data: dict):
    """Send notifications when application status changes"""
    try:
        # Send appropriate notifications based on status
        print(f"Sending status change notification for application {application_id}: {new_status}")
    except Exception as e:
        print(f"Failed to send status change notification for application {application_id}: {e}")
