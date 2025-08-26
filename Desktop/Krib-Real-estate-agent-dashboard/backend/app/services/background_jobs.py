"""
Background job processing with Celery
"""

from celery import Celery
from typing import Dict, Any, List
import logging
import time
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.monitoring import metrics

# Initialize Celery
celery_app = Celery(
    "krib_ai_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.services.background_jobs"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = logging.getLogger(__name__)

# Task decorators with monitoring
def monitored_task(*args, **kwargs):
    """Decorator to add monitoring to Celery tasks"""
    def decorator(func):
        @celery_app.task(*args, **kwargs)
        def wrapper(*task_args, **task_kwargs):
            start_time = time.time()
            task_name = func.__name__
            
            try:
                result = func(*task_args, **task_kwargs)
                duration = time.time() - start_time
                
                # Record success metrics
                metrics.record_background_job(task_name, "success", duration)
                
                logger.info(
                    f"Background job completed successfully",
                    task_name=task_name,
                    duration=duration,
                    args=task_args,
                    kwargs=task_kwargs
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failure metrics
                metrics.record_background_job(task_name, "failure", duration)
                
                logger.error(
                    f"Background job failed",
                    task_name=task_name,
                    duration=duration,
                    error=str(e),
                    args=task_args,
                    kwargs=task_kwargs,
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator

# Email notification tasks
@monitored_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id: str, booking_data: Dict[str, Any]):
    """Send booking confirmation email to guest and host"""
    try:
        # Simulate email sending (replace with actual email service)
        time.sleep(2)  # Simulate email API call
        
        logger.info(
            "Booking confirmation email sent",
            booking_id=booking_id,
            guest_email=booking_data.get("guest_email"),
            property_title=booking_data.get("property_title")
        )
        
        return {"status": "sent", "booking_id": booking_id}
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise

@monitored_task(bind=True, max_retries=3)
def send_payout_notification_email(self, user_id: str, payout_data: Dict[str, Any]):
    """Send payout notification email to host"""
    try:
        # Simulate email sending
        time.sleep(1)
        
        logger.info(
            "Payout notification email sent",
            user_id=user_id,
            payout_amount=payout_data.get("amount"),
            payout_id=payout_data.get("payout_id")
        )
        
        return {"status": "sent", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Failed to send payout notification: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise

# Analytics and reporting tasks
@monitored_task()
def generate_daily_analytics_report(date_str: str):
    """Generate daily analytics report for all users"""
    try:
        from app.core.supabase_client import supabase_client
        
        report_date = datetime.fromisoformat(date_str).date()
        
        # Get all active users
        users_result = supabase_client.table("users").select("id, email, name").execute()
        users = users_result.data
        
        reports_generated = 0
        
        for user in users:
            try:
                # Generate analytics for each user
                user_analytics = _calculate_user_daily_analytics(user["id"], report_date)
                
                # Store analytics in database
                analytics_data = {
                    "user_id": user["id"],
                    "date": report_date.isoformat(),
                    "data": user_analytics,
                    "report_type": "daily"
                }
                
                supabase_client.table("analytics_reports").insert(analytics_data).execute()
                reports_generated += 1
                
            except Exception as user_error:
                logger.error(f"Failed to generate analytics for user {user['id']}: {user_error}")
                continue
        
        logger.info(f"Daily analytics report completed: {reports_generated} reports generated")
        
        return {
            "status": "completed",
            "date": date_str,
            "reports_generated": reports_generated,
            "total_users": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily analytics report: {e}")
        raise

@monitored_task()
def update_market_intelligence_data():
    """Update market intelligence data from external sources"""
    try:
        from app.services.dubai_market_service import DubaiMarketService
        
        market_service = DubaiMarketService()
        
        # Update market benchmarks
        updated_areas = []
        for area in ["marina", "downtown", "jlt", "jbr"]:
            try:
                market_data = market_service.get_market_benchmarks(area)
                
                # Store in cache for quick access
                from app.services.cache_service import cache_service
                await cache_service.cache_market_data(area, market_data)
                
                updated_areas.append(area)
                
            except Exception as area_error:
                logger.error(f"Failed to update market data for {area}: {area_error}")
                continue
        
        logger.info(f"Market intelligence updated for areas: {updated_areas}")
        
        return {
            "status": "completed",
            "updated_areas": updated_areas,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update market intelligence: {e}")
        raise

# Financial processing tasks
@monitored_task(bind=True, max_retries=5)
def process_automatic_payout(self, user_id: str):
    """Process automatic payout for user"""
    try:
        from app.core.supabase_client import supabase_client
        
        # Get user's payout settings
        settings_result = supabase_client.table("payout_settings").select("*").eq("user_id", user_id).execute()
        
        if not settings_result.data:
            logger.warning(f"No payout settings found for user {user_id}")
            return {"status": "skipped", "reason": "no_payout_settings"}
        
        payout_settings = settings_result.data[0]
        
        if not payout_settings.get("auto_payout_enabled"):
            return {"status": "skipped", "reason": "auto_payout_disabled"}
        
        # Check available balance
        balance_result = supabase_client.rpc("calculate_host_balance", {"host_user_id": user_id}).execute()
        available_balance = float(balance_result.data) if balance_result.data else 0.0
        
        minimum_amount = float(payout_settings.get("minimum_payout_amount", 25.0))
        
        if available_balance < minimum_amount:
            return {"status": "skipped", "reason": "insufficient_balance", "balance": available_balance}
        
        # Get primary bank account
        bank_result = supabase_client.table("host_bank_accounts").select("*").eq("user_id", user_id).eq("is_primary", True).execute()
        
        if not bank_result.data:
            logger.warning(f"No primary bank account found for user {user_id}")
            return {"status": "failed", "reason": "no_bank_account"}
        
        bank_account = bank_result.data[0]
        
        # Create payout request
        payout_data = {
            "user_id": user_id,
            "bank_account_id": bank_account["id"],
            "payout_amount": available_balance,
            "payout_method": "bank_transfer",
            "status": "pending",
            "automatic": True
        }
        
        payout_result = supabase_client.table("host_payouts").insert(payout_data).execute()
        payout = payout_result.data[0]
        
        # Send notification email
        send_payout_notification_email.delay(user_id, {
            "amount": available_balance,
            "payout_id": payout["id"],
            "bank_account": bank_account["bank_name"]
        })
        
        logger.info(f"Automatic payout processed for user {user_id}: ${available_balance}")
        
        return {
            "status": "processed",
            "payout_id": payout["id"],
            "amount": available_balance,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to process automatic payout for user {user_id}: {e}")
        
        if self.request.retries < self.max_retries:
            # Exponential backoff: 5min, 10min, 20min, 40min, 80min
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        raise

# Image processing tasks
@monitored_task()
def optimize_property_images(property_id: str, image_urls: List[str]):
    """Optimize and generate thumbnails for property images"""
    try:
        from PIL import Image
        import requests
        from io import BytesIO
        
        optimized_images = []
        
        for image_url in image_urls:
            try:
                # Download image
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # Open image
                image = Image.open(BytesIO(response.content))
                
                # Generate different sizes
                sizes = [
                    ("thumbnail", (300, 200)),
                    ("medium", (800, 600)),
                    ("large", (1200, 900))
                ]
                
                image_variants = {}
                
                for size_name, dimensions in sizes:
                    # Resize image
                    resized = image.copy()
                    resized.thumbnail(dimensions, Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary
                    if resized.mode != "RGB":
                        resized = resized.convert("RGB")
                    
                    # Save to bytes
                    output = BytesIO()
                    resized.save(output, format="JPEG", quality=85, optimize=True)
                    output.seek(0)
                    
                    # Upload to storage (simplified - would need actual storage service)
                    # For now, just log the operation
                    image_variants[size_name] = f"{image_url}_{size_name}.jpg"
                
                optimized_images.append({
                    "original": image_url,
                    "variants": image_variants
                })
                
            except Exception as image_error:
                logger.error(f"Failed to optimize image {image_url}: {image_error}")
                continue
        
        # Update property with optimized image URLs
        from app.core.supabase_client import supabase_client
        supabase_client.table("properties").update({
            "optimized_images": optimized_images
        }).eq("id", property_id).execute()
        
        logger.info(f"Image optimization completed for property {property_id}: {len(optimized_images)} images processed")
        
        return {
            "status": "completed",
            "property_id": property_id,
            "images_processed": len(optimized_images),
            "optimized_images": optimized_images
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize images for property {property_id}: {e}")
        raise

# Scheduled tasks
@celery_app.task()
def run_daily_maintenance():
    """Run daily maintenance tasks"""
    today = datetime.utcnow().date()
    
    tasks = [
        generate_daily_analytics_report.delay(today.isoformat()),
        update_market_intelligence_data.delay(),
    ]
    
    # Process automatic payouts for eligible users
    from app.core.supabase_client import supabase_client
    users_result = supabase_client.table("payout_settings").select("user_id").eq("auto_payout_enabled", True).execute()
    
    for user_setting in users_result.data:
        process_automatic_payout.delay(user_setting["user_id"])
    
    return {"status": "maintenance_tasks_scheduled", "date": today.isoformat()}

# Helper functions
def _calculate_user_daily_analytics(user_id: str, date: datetime.date) -> Dict[str, Any]:
    """Calculate daily analytics for a user"""
    try:
        from app.core.supabase_client import supabase_client
        
        # Get user's properties
        properties_result = supabase_client.table("properties").select("id").eq("user_id", user_id).execute()
        property_ids = [p["id"] for p in properties_result.data]
        
        if not property_ids:
            return {"revenue": 0, "bookings": 0, "views": 0}
        
        # Get bookings for the date
        bookings_result = supabase_client.table("bookings").select("*").in_("property_id", property_ids).gte("created_at", date.isoformat()).lt("created_at", (date + timedelta(days=1)).isoformat()).execute()
        
        bookings = bookings_result.data
        daily_revenue = sum(float(b["total_amount"]) for b in bookings if b["status"] in ["confirmed", "completed"])
        daily_bookings = len(bookings)
        
        return {
            "revenue": daily_revenue,
            "bookings": daily_bookings,
            "properties": len(property_ids),
            "date": date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate daily analytics for user {user_id}: {e}")
        return {"revenue": 0, "bookings": 0, "views": 0}

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "daily-maintenance": {
        "task": "app.services.background_jobs.run_daily_maintenance",
        "schedule": 60.0 * 60.0 * 24.0,  # Every 24 hours
    },
    "update-market-data": {
        "task": "app.services.background_jobs.update_market_intelligence_data",
        "schedule": 60.0 * 60.0 * 6.0,  # Every 6 hours
    },
}
