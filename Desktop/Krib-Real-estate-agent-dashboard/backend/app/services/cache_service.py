"""
High-level caching service for common operations
"""

from typing import Dict, List, Any, Optional
from datetime import timedelta
import hashlib
import json
from app.core.redis_client import redis_client, get_cache_key, get_user_cache_key, get_property_cache_key

class CacheService:
    """High-level caching operations for the application"""
    
    # Cache expiration times (in seconds)
    CACHE_TIMES = {
        "user_profile": 300,        # 5 minutes
        "properties": 180,          # 3 minutes
        "analytics": 600,           # 10 minutes
        "market_data": 1800,        # 30 minutes
        "financial_summary": 300,   # 5 minutes
        "bookings": 120,           # 2 minutes
        "property_details": 600,    # 10 minutes
        "search_results": 180,      # 3 minutes
    }
    
    @staticmethod
    async def cache_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Cache user profile data"""
        cache_key = get_user_cache_key(user_id, "profile")
        return await redis_client.set(
            cache_key, 
            profile_data, 
            expire=CacheService.CACHE_TIMES["user_profile"]
        )
    
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        cache_key = get_user_cache_key(user_id, "profile")
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def cache_user_properties(user_id: str, properties: List[Dict[str, Any]]) -> bool:
        """Cache user's properties list"""
        cache_key = get_user_cache_key(user_id, "properties")
        return await redis_client.set(
            cache_key, 
            properties, 
            expire=CacheService.CACHE_TIMES["properties"]
        )
    
    @staticmethod
    async def get_user_properties(user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached user properties"""
        cache_key = get_user_cache_key(user_id, "properties")
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def invalidate_user_properties(user_id: str):
        """Invalidate user properties cache"""
        cache_key = get_user_cache_key(user_id, "properties")
        await redis_client.delete(cache_key)
    
    @staticmethod
    async def cache_property_details(property_id: str, property_data: Dict[str, Any]) -> bool:
        """Cache property details"""
        cache_key = get_property_cache_key(property_id, "details")
        return await redis_client.set(
            cache_key, 
            property_data, 
            expire=CacheService.CACHE_TIMES["property_details"]
        )
    
    @staticmethod
    async def get_property_details(property_id: str) -> Optional[Dict[str, Any]]:
        """Get cached property details"""
        cache_key = get_property_cache_key(property_id, "details")
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def invalidate_property_details(property_id: str):
        """Invalidate property details cache"""
        cache_key = get_property_cache_key(property_id, "details")
        await redis_client.delete(cache_key)
    
    @staticmethod
    async def cache_analytics_data(user_id: str, period: str, analytics_data: Dict[str, Any]) -> bool:
        """Cache analytics data for user"""
        cache_key = get_user_cache_key(user_id, "analytics", period)
        return await redis_client.set(
            cache_key, 
            analytics_data, 
            expire=CacheService.CACHE_TIMES["analytics"]
        )
    
    @staticmethod
    async def get_analytics_data(user_id: str, period: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics data"""
        cache_key = get_user_cache_key(user_id, "analytics", period)
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def cache_market_data(location: str, market_data: Dict[str, Any]) -> bool:
        """Cache market intelligence data"""
        cache_key = get_cache_key("market", location)
        return await redis_client.set(
            cache_key, 
            market_data, 
            expire=CacheService.CACHE_TIMES["market_data"]
        )
    
    @staticmethod
    async def get_market_data(location: str) -> Optional[Dict[str, Any]]:
        """Get cached market data"""
        cache_key = get_cache_key("market", location)
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def cache_financial_summary(user_id: str, period: str, summary_data: Dict[str, Any]) -> bool:
        """Cache financial summary"""
        cache_key = get_user_cache_key(user_id, "financial", period)
        return await redis_client.set(
            cache_key, 
            summary_data, 
            expire=CacheService.CACHE_TIMES["financial_summary"]
        )
    
    @staticmethod
    async def get_financial_summary(user_id: str, period: str) -> Optional[Dict[str, Any]]:
        """Get cached financial summary"""
        cache_key = get_user_cache_key(user_id, "financial", period)
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def invalidate_financial_data(user_id: str):
        """Invalidate all financial cache for user"""
        patterns = [
            get_user_cache_key(user_id, "financial", "*"),
        ]
        # Redis doesn't support pattern deletion directly, so we'd need to implement
        # For now, we'll set short expiration
        for period in ["7days", "30days", "90days", "1year"]:
            cache_key = get_user_cache_key(user_id, "financial", period)
            await redis_client.expire(cache_key, 1)  # Expire in 1 second
    
    @staticmethod
    async def cache_search_results(search_params: Dict[str, Any], results: List[Dict[str, Any]]) -> bool:
        """Cache property search results"""
        # Create hash of search parameters for cache key
        search_hash = hashlib.md5(json.dumps(search_params, sort_keys=True).encode()).hexdigest()
        cache_key = get_cache_key("search", search_hash)
        
        return await redis_client.set(
            cache_key, 
            results, 
            expire=CacheService.CACHE_TIMES["search_results"]
        )
    
    @staticmethod
    async def get_search_results(search_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        search_hash = hashlib.md5(json.dumps(search_params, sort_keys=True).encode()).hexdigest()
        cache_key = get_cache_key("search", search_hash)
        return await redis_client.get(cache_key, default=None)
    
    @staticmethod
    async def increment_api_calls(endpoint: str, user_id: str) -> int:
        """Increment API call counter for rate limiting"""
        cache_key = get_cache_key("rate_limit", endpoint, user_id)
        count = await redis_client.increment(cache_key)
        
        # Set expiration on first increment
        if count == 1:
            await redis_client.expire(cache_key, 3600)  # 1 hour window
        
        return count
    
    @staticmethod
    async def get_api_call_count(endpoint: str, user_id: str) -> int:
        """Get current API call count"""
        cache_key = get_cache_key("rate_limit", endpoint, user_id)
        count = await redis_client.get(cache_key, default=0, deserialize=False)
        return int(count) if count else 0
    
    @staticmethod
    async def clear_user_cache(user_id: str):
        """Clear all cache entries for a user (useful for logout/data changes)"""
        # This is a simplified version - in production you'd want to use Redis SCAN
        cache_patterns = [
            get_user_cache_key(user_id, "profile"),
            get_user_cache_key(user_id, "properties"),
            get_user_cache_key(user_id, "analytics", "*"),
            get_user_cache_key(user_id, "financial", "*"),
        ]
        
        # Set short expiration instead of deletion for simplicity
        for pattern in cache_patterns:
            if "*" not in pattern:
                await redis_client.expire(pattern, 1)
            else:
                # Handle patterns (would need Redis SCAN in production)
                for period in ["7days", "30days", "90days", "1year"]:
                    if "analytics" in pattern:
                        key = get_user_cache_key(user_id, "analytics", period)
                    elif "financial" in pattern:
                        key = get_user_cache_key(user_id, "financial", period)
                    else:
                        continue
                    await redis_client.expire(key, 1)

# Global cache service instance
cache_service = CacheService()
