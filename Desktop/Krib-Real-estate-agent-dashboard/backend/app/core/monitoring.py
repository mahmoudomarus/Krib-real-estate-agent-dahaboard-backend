"""
Monitoring and observability setup with Prometheus metrics and structured logging
"""

import time
import logging
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Initialize Sentry for error tracking
def init_sentry():
    """Initialize Sentry error tracking"""
    if settings.debug:
        return  # Don't use Sentry in development
    
    sentry_dsn = getattr(settings, 'sentry_dsn', None)
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            environment="production" if not settings.debug else "development",
            attach_stacktrace=True,
        )

# Prometheus Metrics
# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Number of HTTP requests currently being processed'
)

# Application Metrics
active_users = Gauge(
    'active_users_total',
    'Number of active users'
)

properties_total = Gauge(
    'properties_total',
    'Total number of properties in the system'
)

bookings_total = Counter(
    'bookings_total',
    'Total number of bookings',
    ['status']
)

revenue_total = Gauge(
    'revenue_total_usd',
    'Total revenue in USD'
)

# Database Metrics
database_connections = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# Cache Metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

# Background Job Metrics
background_jobs_total = Counter(
    'background_jobs_total',
    'Total background jobs processed',
    ['job_type', 'status']
)

background_job_duration = Histogram(
    'background_job_duration_seconds',
    'Background job duration in seconds',
    ['job_type']
)

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint, 
            status_code=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def increment_in_flight_requests(self):
        """Increment in-flight requests counter"""
        http_requests_in_flight.inc()
    
    def decrement_in_flight_requests(self):
        """Decrement in-flight requests counter"""
        http_requests_in_flight.dec()
    
    def record_error(self, error_type: str, endpoint: str, error: Exception):
        """Record error metrics and log"""
        errors_total.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()
        
        self.logger.error(
            "Application error",
            error_type=error_type,
            endpoint=endpoint,
            error=str(error),
            exc_info=True
        )
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        cache_misses.labels(cache_type=cache_type).inc()
    
    def update_business_metrics(self, 
                               active_user_count: int,
                               total_properties: int,
                               total_revenue: float):
        """Update business-related metrics"""
        active_users.set(active_user_count)
        properties_total.set(total_properties)
        revenue_total.set(total_revenue)
    
    def record_booking(self, status: str):
        """Record booking metrics"""
        bookings_total.labels(status=status).inc()
    
    def record_database_query(self, query_type: str, duration: float):
        """Record database query metrics"""
        database_query_duration.labels(query_type=query_type).observe(duration)
    
    def record_background_job(self, job_type: str, status: str, duration: float):
        """Record background job metrics"""
        background_jobs_total.labels(job_type=job_type, status=status).inc()
        background_job_duration.labels(job_type=job_type).observe(duration)

# Global metrics collector
metrics = MetricsCollector()

# Metrics endpoint handler
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Middleware for automatic request metrics
async def metrics_middleware(request: Request, call_next):
    """Middleware to automatically collect HTTP metrics"""
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    # Increment in-flight requests
    metrics.increment_in_flight_requests()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        status_code = response.status_code
        
        # Record metrics
        metrics.record_http_request(method, endpoint, status_code, duration)
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Record error metrics
        metrics.record_error("http_error", endpoint, e)
        metrics.record_http_request(method, endpoint, 500, duration)
        
        raise
    finally:
        # Decrement in-flight requests
        metrics.decrement_in_flight_requests()

# Health check with metrics
async def health_check_with_metrics():
    """Enhanced health check with system metrics"""
    try:
        # Basic health info
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
        
        # Add metrics if available
        try:
            from app.core.redis_client import redis_client
            health_data["redis_connected"] = redis_client.is_connected
        except:
            health_data["redis_connected"] = False
        
        # Add database check
        try:
            from app.core.supabase_client import supabase_client
            response = supabase_client.table("users").select("count").limit(1).execute()
            health_data["database_connected"] = True
        except:
            health_data["database_connected"] = False
        
        return health_data
        
    except Exception as e:
        metrics.record_error("health_check", "/health", e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Logging helpers
def log_business_event(event_type: str, user_id: str, details: Dict[str, Any]):
    """Log important business events"""
    logger = structlog.get_logger(__name__)
    logger.info(
        "Business event",
        event_type=event_type,
        user_id=user_id,
        details=details
    )

def log_security_event(event_type: str, user_id: str, ip_address: str, details: Dict[str, Any]):
    """Log security-related events"""
    logger = structlog.get_logger(__name__)
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details
    )

def log_performance_warning(operation: str, duration: float, threshold: float):
    """Log performance warnings for slow operations"""
    if duration > threshold:
        logger = structlog.get_logger(__name__)
        logger.warning(
            "Performance warning",
            operation=operation,
            duration=duration,
            threshold=threshold,
            slow_query=True
        )
