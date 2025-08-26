"""
Redis client configuration and connection management
"""

import redis.asyncio as redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper with caching utilities"""
    
    def __init__(self):
        self.redis_pool = None
        self.is_connected = False
    
    async def connect(self):
        """Initialize Redis connection pool"""
        try:
            # Parse Redis URL
            redis_url = settings.redis_url
            
            # Convert redis:// to rediss:// for Upstash SSL
            if "upstash.io" in redis_url and redis_url.startswith("redis://"):
                redis_url = redis_url.replace("redis://", "rediss://")
                logger.info(f"Using SSL Redis URL for Upstash: {redis_url.split('@')[0]}@***")
            
            # Create connection pool - simple approach for Upstash
            # Let redis-py handle SSL automatically from the URL
            self.redis_pool = redis.ConnectionPool.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            
            self.is_connected = True
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            # Don't raise exception - allow app to run without Redis
    
    async def disconnect(self):
        """Close Redis connection pool"""
        if self.redis_pool:
            await self.redis_pool.disconnect()
            self.is_connected = False
            logger.info("Redis connection closed")
    
    def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client instance"""
        if not self.is_connected or not self.redis_pool:
            return None
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None,
        serialize: bool = True
    ) -> bool:
        """Set value in Redis with optional expiration"""
        if not self.is_connected:
            return False
        
        try:
            client = self.get_client()
            if not client:
                return False
            
            # Serialize value if needed
            if serialize:
                if isinstance(value, (dict, list, tuple)):
                    value = json.dumps(value, default=str)
                elif not isinstance(value, (str, int, float, bool)):
                    value = pickle.dumps(value)
            
            # Set expiration
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            
            await client.set(key, value, ex=expire)
            return True
            
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get(
        self, 
        key: str, 
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get value from Redis with optional deserialization"""
        if not self.is_connected:
            return default
        
        try:
            client = self.get_client()
            if not client:
                return default
            
            value = await client.get(key)
            if value is None:
                return default
            
            # Deserialize if needed
            if deserialize and isinstance(value, str):
                try:
                    # Try JSON first
                    return json.loads(value)
                except json.JSONDecodeError:
                    try:
                        # Try pickle
                        return pickle.loads(value.encode())
                    except:
                        # Return as string
                        return value
            
            return value
            
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        if not self.is_connected:
            return 0
        
        try:
            client = self.get_client()
            if not client:
                return 0
            
            return await client.delete(*keys)
            
        except Exception as e:
            logger.error(f"Redis DELETE error for keys {keys}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected:
            return False
        
        try:
            client = self.get_client()
            if not client:
                return False
            
            return bool(await client.exists(key))
            
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in Redis"""
        if not self.is_connected:
            return None
        
        try:
            client = self.get_client()
            if not client:
                return None
            
            return await client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on existing key"""
        if not self.is_connected:
            return False
        
        try:
            client = self.get_client()
            if not client:
                return False
            
            return await client.expire(key, seconds)
            
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

# Global Redis client instance
redis_client = RedisClient()

# Cache key generators
def get_cache_key(prefix: str, *args) -> str:
    """Generate standardized cache key"""
    return f"krib:{prefix}:" + ":".join(str(arg) for arg in args)

def get_user_cache_key(user_id: str, resource: str, *args) -> str:
    """Generate user-specific cache key"""
    return get_cache_key("user", user_id, resource, *args)

def get_property_cache_key(property_id: str, resource: str, *args) -> str:
    """Generate property-specific cache key"""
    return get_cache_key("property", property_id, resource, *args)

# Cache decorators
def cache_result(expire_seconds: int = 300, key_prefix: str = "api"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = get_cache_key(key_prefix, func.__name__, str(hash(str(args) + str(kwargs))))
            
            # Try to get from cache
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_client.set(cache_key, result, expire=expire_seconds)
            
            return result
        return wrapper
    return decorator
