"""
Rate limiting implementation using Redis
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Optional
import logging
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

def get_user_id_from_request(request: Request) -> str:
    """Extract user ID from request for rate limiting"""
    try:
        # Try to get user ID from auth token
        auth_header = request.headers.get("authorization")
        if auth_header and hasattr(request.state, "user"):
            return getattr(request.state, "user", {}).get("id", get_remote_address(request))
        
        # Fallback to IP address
        return get_remote_address(request)
    except:
        return get_remote_address(request)

def redis_key_func(request: Request) -> str:
    """Generate Redis key for rate limiting"""
    user_id = get_user_id_from_request(request)
    endpoint = request.url.path
    return f"rate_limit:{endpoint}:{user_id}"

# Custom storage backend for Redis
class RedisStorage:
    """Redis storage backend for SlowAPI"""
    
    def __init__(self):
        self.redis = None
    
    async def get(self, key: str) -> Optional[int]:
        """Get current count from Redis"""
        if not redis_client.is_connected:
            return None
        
        try:
            client = redis_client.get_client()
            if not client:
                return None
            
            value = await client.get(key)
            return int(value) if value else None
        except Exception as e:
            logger.error(f"Redis rate limiter GET error: {e}")
            return None
    
    async def set(self, key: str, value: int, expire: int) -> bool:
        """Set count in Redis with expiration"""
        if not redis_client.is_connected:
            return False
        
        try:
            client = redis_client.get_client()
            if not client:
                return False
            
            await client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis rate limiter SET error: {e}")
            return False
    
    async def incr(self, key: str, expire: int) -> int:
        """Increment counter in Redis"""
        if not redis_client.is_connected:
            return 1  # Allow request if Redis is down
        
        try:
            client = redis_client.get_client()
            if not client:
                return 1
            
            # Use Redis pipeline for atomic increment
            pipe = client.pipeline()
            await pipe.incr(key)
            await pipe.expire(key, expire)
            results = await pipe.execute()
            
            return int(results[0])
        except Exception as e:
            logger.error(f"Redis rate limiter INCR error: {e}")
            return 1  # Allow request on error

# Initialize rate limiter with Redis backend
redis_storage = RedisStorage()

# Create limiter instance
limiter = Limiter(
    key_func=redis_key_func,
    storage_uri="memory://",  # Fallback storage
    default_limits=["1000/hour", "50/minute"]  # Default limits
)

# Rate limiting rules for different endpoints
RATE_LIMIT_RULES = {
    # Authentication endpoints
    "/api/auth/login": "5/minute",
    "/api/auth/register": "3/minute",
    "/api/auth/refresh": "10/minute",
    
    # Property endpoints  
    "/api/properties": "100/hour",
    "/api/properties/create": "10/hour",
    "/api/properties/update": "20/hour",
    "/api/properties/delete": "5/hour",
    
    # Analytics endpoints (expensive operations)
    "/api/analytics": "50/hour",
    "/api/analytics/market": "20/hour",
    "/api/analytics/forecast": "30/hour",
    
    # Financial endpoints
    "/api/financials/summary": "100/hour", 
    "/api/financials/payouts": "20/hour",
    "/api/financials/bank-accounts": "50/hour",
    
    # Upload endpoints
    "/api/upload": "20/hour",
    "/api/upload/image": "50/hour",
    
    # Booking endpoints
    "/api/bookings": "200/hour",
    "/api/bookings/create": "10/hour",
    "/api/bookings/update": "20/hour",
}

def get_rate_limit_for_endpoint(endpoint: str) -> str:
    """Get rate limit rule for specific endpoint"""
    # Check exact match first
    if endpoint in RATE_LIMIT_RULES:
        return RATE_LIMIT_RULES[endpoint]
    
    # Check prefix matches
    for rule_endpoint, limit in RATE_LIMIT_RULES.items():
        if endpoint.startswith(rule_endpoint):
            return limit
    
    # Default limits
    return "200/hour"

async def check_rate_limit(request: Request, response: Response) -> bool:
    """Manual rate limit check for advanced logic"""
    endpoint = request.url.path
    user_id = get_user_id_from_request(request)
    
    # Get rate limit for this endpoint
    rate_limit = get_rate_limit_for_endpoint(endpoint)
    
    # Parse rate limit (e.g., "10/minute" -> 10 requests per 60 seconds)
    try:
        limit_parts = rate_limit.split("/")
        max_requests = int(limit_parts[0])
        time_window = limit_parts[1]
        
        # Convert time window to seconds
        if time_window == "minute":
            window_seconds = 60
        elif time_window == "hour":
            window_seconds = 3600
        elif time_window == "day":
            window_seconds = 86400
        else:
            window_seconds = 3600  # Default to hour
        
        # Generate Redis key
        key = f"rate_limit:{endpoint}:{user_id}"
        
        # Increment counter
        current_count = await redis_storage.incr(key, window_seconds)
        
        # Check if limit exceeded
        if current_count > max_requests:
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(window_seconds)
            return False
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max_requests - current_count)
        response.headers["X-RateLimit-Reset"] = str(window_seconds)
        
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True  # Allow request on error

# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    return {
        "error": "Rate limit exceeded",
        "detail": f"Too many requests. Limit: {exc.detail}",
        "retry_after": exc.retry_after,
        "type": "rate_limit_error"
    }

# Middleware to add rate limiting headers
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to add rate limiting to all requests"""
    response = await call_next(request)
    
    # Add rate limiting headers for monitoring
    if not any(header.startswith("X-RateLimit") for header in response.headers):
        endpoint = request.url.path
        user_id = get_user_id_from_request(request)
        rate_limit = get_rate_limit_for_endpoint(endpoint)
        
        # Parse rate limit for headers
        try:
            limit_parts = rate_limit.split("/")
            max_requests = int(limit_parts[0])
            
            key = f"rate_limit:{endpoint}:{user_id}"
            current_count = await redis_storage.get(key) or 0
            
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - current_count))
        except:
            pass
    
    return response
