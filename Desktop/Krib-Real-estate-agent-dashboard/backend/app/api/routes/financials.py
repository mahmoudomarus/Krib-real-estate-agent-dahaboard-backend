"""
Financial and Payouts API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.schemas import (
    FinancialSummary, 
    PayoutRequest, 
    PayoutResponse,
    BankAccountCreate,
    BankAccountResponse,
    PayoutSettingsUpdate,
    PayoutSettingsResponse,
    TransactionResponse
)
from app.core.supabase_client import supabase_client
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/summary", response_model=FinancialSummary)
async def get_financial_summary(
    period: str = Query("30days", description="Period: 7days, 30days, 90days, 1year"),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive financial summary for the host"""
    try:
        user_id = current_user["id"]
        
        # Calculate total balance using our database function
        balance_result = supabase_client.rpc("calculate_host_balance", {"host_user_id": user_id}).execute()
        total_balance = float(balance_result.data) if balance_result.data else 0.0
        
        # Calculate pending earnings
        pending_result = supabase_client.rpc("get_pending_earnings", {"host_user_id": user_id}).execute()
        pending_earnings = float(pending_result.data) if pending_result.data else 0.0
        
        # Get recent transactions
        transactions_result = supabase_client.table("financial_transactions").select(
            "*, bookings(guest_name, check_in, check_out), properties(title)"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        
        recent_transactions = []
        total_earnings = 0
        for tx in transactions_result.data:
            recent_transactions.append({
                "id": tx["id"],
                "type": tx["transaction_type"],
                "amount": float(tx["net_amount"]),
                "status": tx["status"],
                "date": tx["payment_date"],
                "property_title": tx["properties"]["title"] if tx["properties"] else "Unknown",
                "guest_name": tx["bookings"]["guest_name"] if tx["bookings"] else "Unknown"
            })
            if tx["status"] == "completed":
                total_earnings += float(tx["net_amount"])
        
        # Get payouts for the period
        date_filter = _get_date_filter(period)
        payouts_result = supabase_client.table("host_payouts").select("*").eq(
            "user_id", user_id
        ).gte("created_at", date_filter.isoformat()).execute()
        
        total_payouts = sum(float(p["payout_amount"]) for p in payouts_result.data if p["status"] == "completed")
        
        # Platform fees calculation
        platform_fees_result = supabase_client.table("financial_transactions").select(
            "platform_fee, payment_processing_fee"
        ).eq("user_id", user_id).gte("created_at", date_filter.isoformat()).execute()
        
        total_platform_fees = sum(
            float(tx["platform_fee"]) + float(tx["payment_processing_fee"]) 
            for tx in platform_fees_result.data
        )
        
        return FinancialSummary(
            total_balance=total_balance,
            pending_earnings=pending_earnings,
            total_earnings=total_earnings,
            total_payouts=total_payouts,
            platform_fees=total_platform_fees,
            recent_transactions=recent_transactions,
            payout_frequency="weekly",  # From settings
            next_payout_date=_calculate_next_payout_date(user_id)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial summary: {str(e)}"
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of financial transactions"""
    try:
        query = supabase_client.table("financial_transactions").select(
            "*, bookings(guest_name, check_in, check_out), properties(title)"
        ).eq("user_id", current_user["id"])
        
        if status_filter:
            query = query.eq("status", status_filter)
            
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        transactions = []
        for tx in result.data:
            transactions.append(TransactionResponse(
                id=tx["id"],
                booking_id=tx["booking_id"],
                property_title=tx["properties"]["title"] if tx["properties"] else "Unknown",
                guest_name=tx["bookings"]["guest_name"] if tx["bookings"] else "Unknown",
                transaction_type=tx["transaction_type"],
                gross_amount=float(tx["gross_amount"]),
                platform_fee=float(tx["platform_fee"]),
                payment_processing_fee=float(tx["payment_processing_fee"]),
                net_amount=float(tx["net_amount"]),
                status=tx["status"],
                payment_date=tx["payment_date"],
                created_at=tx["created_at"]
            ))
            
        return transactions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {str(e)}"
        )


@router.post("/bank-accounts", response_model=BankAccountResponse)
async def add_bank_account(
    bank_account: BankAccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new bank account for payouts"""
    try:
        # If this is marked as primary, unset other primary accounts
        if bank_account.is_primary:
            supabase_client.table("host_bank_accounts").update({
                "is_primary": False
            }).eq("user_id", current_user["id"]).execute()
        
        result = supabase_client.table("host_bank_accounts").insert({
            "user_id": current_user["id"],
            "account_holder_name": bank_account.account_holder_name,
            "bank_name": bank_account.bank_name,
            "account_number_last4": bank_account.account_number_last4,
            "routing_number": bank_account.routing_number,
            "account_type": bank_account.account_type,
            "is_primary": bank_account.is_primary
        }).execute()
        
        return BankAccountResponse(**result.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add bank account: {str(e)}"
        )


@router.get("/bank-accounts", response_model=List[BankAccountResponse])
async def get_bank_accounts(current_user: dict = Depends(get_current_user)):
    """Get all bank accounts for the user"""
    try:
        result = supabase_client.table("host_bank_accounts").select("*").eq(
            "user_id", current_user["id"]
        ).order("is_primary", desc=True).execute()
        
        return [BankAccountResponse(**account) for account in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bank accounts: {str(e)}"
        )


@router.post("/payouts/request", response_model=PayoutResponse)
async def request_payout(
    payout_request: PayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request a payout of available earnings"""
    try:
        user_id = current_user["id"]
        
        # Check available balance
        pending_result = supabase_client.rpc("get_pending_earnings", {"host_user_id": user_id}).execute()
        available_amount = float(pending_result.data) if pending_result.data else 0.0
        
        if payout_request.amount > available_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested amount ${payout_request.amount} exceeds available balance ${available_amount}"
            )
        
        # Get payout settings for minimum amount check
        settings_result = supabase_client.table("payout_settings").select("*").eq(
            "user_id", user_id
        ).execute()
        
        min_payout = 25.00  # Default
        if settings_result.data:
            min_payout = float(settings_result.data[0]["minimum_payout_amount"])
            
        if payout_request.amount < min_payout:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum payout amount is ${min_payout}"
            )
        
        # Verify bank account exists and belongs to user
        bank_result = supabase_client.table("host_bank_accounts").select("*").eq(
            "id", payout_request.bank_account_id
        ).eq("user_id", user_id).execute()
        
        if not bank_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found"
            )
            
        # Create payout request
        payout_result = supabase_client.table("host_payouts").insert({
            "user_id": user_id,
            "bank_account_id": payout_request.bank_account_id,
            "payout_amount": payout_request.amount,
            "payout_method": "bank_transfer",
            "status": "pending"
        }).execute()
        
        payout = payout_result.data[0]
        
        # TODO: Here you would integrate with payment processor (Stripe, etc.)
        # For now, we'll mark it as processing
        supabase_client.table("host_payouts").update({
            "status": "processing",
            "processed_at": datetime.now().isoformat()
        }).eq("id", payout["id"]).execute()
        
        return PayoutResponse(
            id=payout["id"],
            amount=float(payout["payout_amount"]),
            status=payout["status"],
            bank_account_id=payout["bank_account_id"],
            requested_at=payout["requested_at"],
            estimated_arrival=_calculate_arrival_date()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request payout: {str(e)}"
        )


@router.get("/payouts", response_model=List[PayoutResponse])
async def get_payouts(
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get user's payout history"""
    try:
        result = supabase_client.table("host_payouts").select(
            "*, host_bank_accounts(bank_name, account_number_last4)"
        ).eq("user_id", current_user["id"]).order("created_at", desc=True).limit(limit).execute()
        
        payouts = []
        for payout in result.data:
            payouts.append(PayoutResponse(
                id=payout["id"],
                amount=float(payout["payout_amount"]),
                status=payout["status"],
                bank_account_id=payout["bank_account_id"],
                bank_info=payout["host_bank_accounts"],
                requested_at=payout["requested_at"],
                completed_at=payout.get("completed_at"),
                failure_reason=payout.get("failure_reason")
            ))
            
        return payouts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payouts: {str(e)}"
        )


@router.get("/settings", response_model=PayoutSettingsResponse)
async def get_payout_settings(current_user: dict = Depends(get_current_user)):
    """Get user's payout settings"""
    try:
        result = supabase_client.table("payout_settings").select("*").eq(
            "user_id", current_user["id"]
        ).execute()
        
        if not result.data:
            # Create default settings
            default_settings = {
                "user_id": current_user["id"],
                "payout_frequency": "weekly",
                "minimum_payout_amount": 25.00,
                "auto_payout_enabled": True,
                "hold_period_days": 1
            }
            
            create_result = supabase_client.table("payout_settings").insert(default_settings).execute()
            return PayoutSettingsResponse(**create_result.data[0])
        
        return PayoutSettingsResponse(**result.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payout settings: {str(e)}"
        )


@router.put("/settings", response_model=PayoutSettingsResponse)
async def update_payout_settings(
    settings: PayoutSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's payout settings"""
    try:
        update_data = settings.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now().isoformat()
        
        result = supabase_client.table("payout_settings").update(update_data).eq(
            "user_id", current_user["id"]
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payout settings not found"
            )
            
        return PayoutSettingsResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update payout settings: {str(e)}"
        )


# Helper functions
def _get_date_filter(period: str) -> datetime:
    """Get date filter based on period"""
    now = datetime.now()
    if period == "7days":
        return now - timedelta(days=7)
    elif period == "30days":
        return now - timedelta(days=30)
    elif period == "90days":
        return now - timedelta(days=90)
    elif period == "1year":
        return now - timedelta(days=365)
    else:
        return now - timedelta(days=30)


def _calculate_next_payout_date(user_id: str) -> Optional[str]:
    """Calculate next automatic payout date"""
    try:
        settings_result = supabase_client.table("payout_settings").select("*").eq(
            "user_id", user_id
        ).execute()
        
        if not settings_result.data or not settings_result.data[0]["auto_payout_enabled"]:
            return None
            
        settings = settings_result.data[0]
        frequency = settings["payout_frequency"]
        
        now = datetime.now()
        if frequency == "weekly":
            days_ahead = settings.get("payout_day_of_week", 5) - now.weekday()  # Default Friday
            if days_ahead <= 0:
                days_ahead += 7
            return (now + timedelta(days=days_ahead)).date().isoformat()
        elif frequency == "monthly":
            target_day = settings.get("payout_day_of_month", 1)
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=min(target_day, 28))  # Avoid month-end issues
            return next_month.date().isoformat()
            
        return None
    except:
        return None


def _calculate_arrival_date() -> str:
    """Calculate estimated arrival date for payout (typically 1-2 business days)"""
    return (datetime.now() + timedelta(days=2)).date().isoformat()
