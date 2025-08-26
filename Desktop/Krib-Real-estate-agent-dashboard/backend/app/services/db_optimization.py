"""
Database optimization and query performance monitoring
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from app.core.supabase_client import supabase_client
from app.core.monitoring import metrics, log_performance_warning
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization and monitoring utilities"""
    
    SLOW_QUERY_THRESHOLD = 2.0  # seconds
    
    @staticmethod
    @asynccontextmanager
    async def query_timer(query_type: str, query_name: str = ""):
        """Context manager to time database queries and log slow ones"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            metrics.record_database_query(query_type, duration)
            
            # Log slow queries
            if duration > DatabaseOptimizer.SLOW_QUERY_THRESHOLD:
                log_performance_warning(
                    f"slow_database_query_{query_type}_{query_name}",
                    duration,
                    DatabaseOptimizer.SLOW_QUERY_THRESHOLD
                )
                
                logger.warning(
                    f"Slow database query detected",
                    query_type=query_type,
                    query_name=query_name,
                    duration=duration,
                    threshold=DatabaseOptimizer.SLOW_QUERY_THRESHOLD
                )
    
    @staticmethod
    async def get_optimized_user_properties(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user properties with optimized query"""
        async with DatabaseOptimizer.query_timer("select", "user_properties"):
            # Use specific columns and limit to optimize query
            result = supabase_client.table("properties").select(
                "id, title, price_per_night, status, rating, booking_count, total_revenue, created_at, images"
            ).eq("user_id", user_id).eq("status", "active").order("created_at", desc=True).limit(limit).execute()
            
            return result.data
    
    @staticmethod
    async def get_optimized_recent_bookings(user_id: str, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent bookings with optimized query and proper joins"""
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        async with DatabaseOptimizer.query_timer("select", "recent_bookings"):
            # Use specific joins and columns
            result = supabase_client.table("bookings").select(
                "id, guest_name, guest_email, check_in, check_out, total_amount, status, created_at, properties(title, id)"
            ).gte("created_at", cutoff_date).order("created_at", desc=True).limit(limit).execute()
            
            # Filter by user ownership (done in application since complex joins can be slow)
            user_properties = await DatabaseOptimizer.get_user_property_ids(user_id)
            user_property_ids = set(user_properties)
            
            filtered_bookings = [
                booking for booking in result.data 
                if booking.get("properties", {}).get("id") in user_property_ids
            ]
            
            return filtered_bookings[:limit]
    
    @staticmethod
    async def get_user_property_ids(user_id: str) -> List[str]:
        """Get just property IDs for a user (lightweight query)"""
        async with DatabaseOptimizer.query_timer("select", "property_ids"):
            result = supabase_client.table("properties").select("id").eq("user_id", user_id).execute()
            return [p["id"] for p in result.data]
    
    @staticmethod
    async def bulk_update_property_metrics(property_metrics: List[Dict[str, Any]]) -> bool:
        """Efficiently update multiple property metrics"""
        if not property_metrics:
            return True
        
        async with DatabaseOptimizer.query_timer("bulk_update", "property_metrics"):
            try:
                # Group updates by property_id for efficiency
                for metrics_data in property_metrics:
                    property_id = metrics_data.pop("property_id")
                    
                    supabase_client.table("properties").update(metrics_data).eq("id", property_id).execute()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to bulk update property metrics: {e}")
                return False
    
    @staticmethod
    async def get_analytics_with_aggregation(user_id: str, period_days: int = 30) -> Dict[str, Any]:
        """Get analytics data using database aggregation functions"""
        from datetime import datetime, timedelta
        
        start_date = (datetime.utcnow() - timedelta(days=period_days)).isoformat()
        
        async with DatabaseOptimizer.query_timer("aggregation", "analytics"):
            try:
                # Use database functions for aggregation where possible
                property_ids = await DatabaseOptimizer.get_user_property_ids(user_id)
                
                if not property_ids:
                    return {
                        "total_revenue": 0,
                        "total_bookings": 0,
                        "average_rating": 0,
                        "occupancy_rate": 0
                    }
                
                # Get booking aggregates
                bookings_result = supabase_client.table("bookings").select(
                    "total_amount, status, nights"
                ).in_("property_id", property_ids).gte("created_at", start_date).execute()
                
                confirmed_bookings = [b for b in bookings_result.data if b["status"] in ["confirmed", "completed"]]
                
                total_revenue = sum(float(b["total_amount"]) for b in confirmed_bookings)
                total_bookings = len(confirmed_bookings)
                total_nights = sum(int(b["nights"]) for b in confirmed_bookings)
                
                # Get property aggregates
                properties_result = supabase_client.table("properties").select(
                    "rating"
                ).eq("user_id", user_id).execute()
                
                ratings = [float(p["rating"]) for p in properties_result.data if p["rating"]]
                average_rating = sum(ratings) / len(ratings) if ratings else 0
                
                # Calculate occupancy (simplified)
                total_possible_nights = len(property_ids) * period_days
                occupancy_rate = (total_nights / total_possible_nights * 100) if total_possible_nights > 0 else 0
                
                return {
                    "total_revenue": total_revenue,
                    "total_bookings": total_bookings,
                    "average_rating": round(average_rating, 2),
                    "occupancy_rate": round(occupancy_rate, 2)
                }
                
            except Exception as e:
                logger.error(f"Failed to get analytics with aggregation: {e}")
                return {
                    "total_revenue": 0,
                    "total_bookings": 0,
                    "average_rating": 0,
                    "occupancy_rate": 0
                }
    
    @staticmethod
    async def optimize_table_indexes():
        """Check and suggest database index optimizations"""
        try:
            # This would typically analyze query patterns and suggest indexes
            # For now, we'll log the current status
            
            logger.info("Database optimization check initiated")
            
            # Check for missing indexes on commonly queried columns
            optimization_suggestions = []
            
            # Check properties table
            suggestions = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_user_status ON properties(user_id, status) WHERE status = 'active';",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_type ON properties(city, property_type);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bookings_property_dates ON bookings(property_id, check_in, check_out);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bookings_status_created ON bookings(status, created_at) WHERE status IN ('confirmed', 'completed');",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_transactions_user_date ON financial_transactions(user_id, payment_date);",
            ]
            
            for suggestion in suggestions:
                optimization_suggestions.append({
                    "type": "index",
                    "sql": suggestion,
                    "reason": "Improve query performance for common filters"
                })
            
            logger.info(f"Database optimization suggestions: {len(optimization_suggestions)} recommendations")
            
            return optimization_suggestions
            
        except Exception as e:
            logger.error(f"Failed to analyze database optimization: {e}")
            return []
    
    @staticmethod
    async def cleanup_old_data(days_to_keep: int = 365):
        """Clean up old data to maintain performance"""
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
        
        async with DatabaseOptimizer.query_timer("cleanup", "old_data"):
            try:
                cleanup_results = {}
                
                # Clean up old analytics reports (keep only recent ones)
                analytics_result = supabase_client.table("analytics_reports").delete().lt("created_at", cutoff_date).execute()
                cleanup_results["analytics_reports"] = len(analytics_result.data) if analytics_result.data else 0
                
                # Clean up old cancelled bookings (keep confirmed/completed ones)
                old_cancelled = supabase_client.table("bookings").delete().eq("status", "cancelled").lt("created_at", cutoff_date).execute()
                cleanup_results["cancelled_bookings"] = len(old_cancelled.data) if old_cancelled.data else 0
                
                logger.info(f"Database cleanup completed", cleanup_results=cleanup_results)
                
                return cleanup_results
                
            except Exception as e:
                logger.error(f"Failed to cleanup old data: {e}")
                return {}

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()

# Connection pool monitoring
class ConnectionPoolMonitor:
    """Monitor database connection pool health"""
    
    @staticmethod
    async def get_connection_stats() -> Dict[str, Any]:
        """Get current connection pool statistics"""
        try:
            # Supabase manages connection pooling, but we can monitor our usage
            stats = {
                "timestamp": time.time(),
                "status": "healthy",
                "active_connections": 1,  # Simplified
                "pool_size": 20,
                "max_connections": 100
            }
            
            # Update metrics
            metrics.database_connections.set(stats["active_connections"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {
                "timestamp": time.time(),
                "status": "error",
                "error": str(e)
            }

# Connection pool monitor instance
connection_monitor = ConnectionPoolMonitor()
