"""
Bookings API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, date

from app.models.schemas import (
    BookingCreate, BookingUpdate, BookingResponse, SuccessResponse
)
from app.core.supabase_client import supabase_client
from app.api.dependencies import get_current_user, verify_booking_access

router = APIRouter()


@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new booking"""
    try:
        # Verify property exists and get details
        property_result = supabase_client.table("properties").select("*").eq("id", booking_data.property_id).eq("status", "active").execute()
        
        if not property_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found or not available"
            )
        
        property_info = property_result.data[0]
        
        # Validate guest count
        if booking_data.guests > property_info["max_guests"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Property can accommodate maximum {property_info['max_guests']} guests"
            )
        
        # Calculate nights and total amount
        nights = (booking_data.check_out - booking_data.check_in).days
        if nights <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Check-out date must be after check-in date"
            )
        
        total_amount = nights * property_info["price_per_night"]
        
        # Check for date conflicts
        conflicts = supabase_client.table("bookings").select("*").eq("property_id", booking_data.property_id).in_("status", ["confirmed", "pending"]).execute()
        
        for conflict in conflicts.data:
            conflict_checkin = datetime.strptime(conflict["check_in"], "%Y-%m-%d").date()
            conflict_checkout = datetime.strptime(conflict["check_out"], "%Y-%m-%d").date()
            
            # Check if dates overlap
            if (booking_data.check_in < conflict_checkout and booking_data.check_out > conflict_checkin):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Property is not available for the selected dates"
                )
        
        # Create booking record
        booking_record = {
            "property_id": booking_data.property_id,
            "guest_name": booking_data.guest_name,
            "guest_email": booking_data.guest_email,
            "guest_phone": booking_data.guest_phone,
            "check_in": booking_data.check_in.isoformat(),
            "check_out": booking_data.check_out.isoformat(),
            "nights": nights,
            "guests": booking_data.guests,
            "total_amount": total_amount,
            "status": "pending",
            "payment_status": "pending",
            "special_requests": booking_data.special_requests
        }
        
        result = supabase_client.table("bookings").insert(booking_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking"
            )
        
        created_booking = result.data[0]
        
        # Add property details for response
        created_booking["property_title"] = property_info["title"]
        created_booking["property_address"] = property_info["address"]
        
        return BookingResponse(**created_booking)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}"
        )


@router.get("/", response_model=List[BookingResponse])
async def get_user_bookings(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all bookings for properties owned by the current user"""
    try:
        # Get user's properties
        properties_result = supabase_client.table("properties").select("id").eq("user_id", current_user["id"]).execute()
        property_ids = [p["id"] for p in properties_result.data]
        
        if not property_ids:
            return []
        
        # Build query for bookings
        query = supabase_client.table("bookings").select("""
            *,
            properties!inner(title, address)
        """).in_("property_id", property_ids)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).execute()
        
        # Format response
        bookings = []
        for booking in result.data:
            booking_data = {**booking}
            booking_data["property_title"] = booking["properties"]["title"]
            booking_data["property_address"] = booking["properties"]["address"]
            # Remove nested properties object
            del booking_data["properties"]
            bookings.append(BookingResponse(**booking_data))
        
        return bookings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bookings: {str(e)}"
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific booking"""
    try:
        booking = await verify_booking_access(booking_id, current_user)
        
        # Get property details
        property_result = supabase_client.table("properties").select("title, address").eq("id", booking["property_id"]).execute()
        
        if property_result.data:
            booking["property_title"] = property_result.data[0]["title"]
            booking["property_address"] = property_result.data[0]["address"]
        
        # Remove nested properties if it exists
        if "properties" in booking:
            del booking["properties"]
        
        return BookingResponse(**booking)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch booking: {str(e)}"
        )


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    booking_updates: BookingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a booking"""
    try:
        # Verify access and get existing booking
        existing_booking = await verify_booking_access(booking_id, current_user)
        
        # Prepare update data
        update_data = {k: v for k, v in booking_updates.dict().items() if v is not None}
        
        # Handle date changes
        if "check_in" in update_data or "check_out" in update_data:
            check_in = update_data.get("check_in", datetime.strptime(existing_booking["check_in"], "%Y-%m-%d").date())
            check_out = update_data.get("check_out", datetime.strptime(existing_booking["check_out"], "%Y-%m-%d").date())
            
            if check_out <= check_in:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Check-out date must be after check-in date"
                )
            
            # Recalculate nights and amount if dates changed
            nights = (check_out - check_in).days
            update_data["nights"] = nights
            
            # Get property price to recalculate total
            property_result = supabase_client.table("properties").select("price_per_night").eq("id", existing_booking["property_id"]).execute()
            if property_result.data:
                price_per_night = property_result.data[0]["price_per_night"]
                update_data["total_amount"] = nights * price_per_night
            
            # Convert dates to ISO format for database
            update_data["check_in"] = check_in.isoformat()
            update_data["check_out"] = check_out.isoformat()
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update booking
        result = supabase_client.table("bookings").update(update_data).eq("id", booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking"
            )
        
        updated_booking = result.data[0]
        
        # Add property details
        property_result = supabase_client.table("properties").select("title, address").eq("id", updated_booking["property_id"]).execute()
        if property_result.data:
            updated_booking["property_title"] = property_result.data[0]["title"]
            updated_booking["property_address"] = property_result.data[0]["address"]
        
        return BookingResponse(**updated_booking)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update booking: {str(e)}"
        )


@router.post("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Confirm a pending booking"""
    try:
        # Verify access
        booking = await verify_booking_access(booking_id, current_user)
        
        if booking["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending bookings can be confirmed"
            )
        
        # Update status
        result = supabase_client.table("bookings").update({
            "status": "confirmed",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm booking"
            )
        
        # Update property statistics
        supabase_client.table("properties").update({
            "booking_count": supabase_client.table("properties").select("booking_count").eq("id", booking["property_id"]).execute().data[0]["booking_count"] + 1,
            "total_revenue": supabase_client.table("properties").select("total_revenue").eq("id", booking["property_id"]).execute().data[0]["total_revenue"] + booking["total_amount"]
        }).eq("id", booking["property_id"]).execute()
        
        confirmed_booking = result.data[0]
        
        # Add property details
        property_result = supabase_client.table("properties").select("title, address").eq("id", confirmed_booking["property_id"]).execute()
        if property_result.data:
            confirmed_booking["property_title"] = property_result.data[0]["title"]
            confirmed_booking["property_address"] = property_result.data[0]["address"]
        
        return BookingResponse(**confirmed_booking)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm booking: {str(e)}"
        )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a booking"""
    try:
        # Verify access
        booking = await verify_booking_access(booking_id, current_user)
        
        if booking["status"] in ["cancelled", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be cancelled"
            )
        
        # Update status
        result = supabase_client.table("bookings").update({
            "status": "cancelled",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", booking_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel booking"
            )
        
        cancelled_booking = result.data[0]
        
        # Add property details
        property_result = supabase_client.table("properties").select("title, address").eq("id", cancelled_booking["property_id"]).execute()
        if property_result.data:
            cancelled_booking["property_title"] = property_result.data[0]["title"]
            cancelled_booking["property_address"] = property_result.data[0]["address"]
        
        return BookingResponse(**cancelled_booking)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel booking: {str(e)}"
        )
