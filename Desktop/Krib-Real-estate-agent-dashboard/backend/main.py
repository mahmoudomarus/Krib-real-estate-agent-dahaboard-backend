"""
RentalAI FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import redis_client
from app.core.monitoring import init_sentry, metrics_middleware, metrics_endpoint, health_check_with_metrics
from app.core.rate_limiter import limiter, custom_rate_limit_handler
from app.api.routes import auth, properties, bookings, analytics, upload, financials, users, locations
from app.api.routes import agencies, applications, viewings  # New long-term rental routes
from app.core.supabase_client import supabase_client
from slowapi.errors import RateLimitExceeded

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Krib AI Backend...")
    
    # Initialize Sentry error tracking
    init_sentry()
    print("✅ Sentry error tracking initialized")
    
    await init_db()
    print("✅ Database initialized")
    
    # Initialize Redis
    await redis_client.connect()
    if redis_client.is_connected:
        print("✅ Redis cache connected")
    else:
        print("⚠️ Redis cache unavailable - running without cache")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Krib AI Backend...")
    await redis_client.disconnect()
    print("✅ Redis connection closed")

app = FastAPI(
    title="Krib AI API",
    description="Krib AI - AI-Powered Property Rental Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware Configuration

# Simple HTTPS redirect fix for Render
@app.middleware("http")
async def https_fix_middleware(request, call_next):
    """Simple fix for HTTPS behind proxy"""
    response = await call_next(request)
    
    # Fix any HTTP redirects to HTTPS
    if "location" in response.headers:
        location = response.headers["location"]
        if "onrender.com" in location and location.startswith("http://"):
            response.headers["location"] = location.replace("http://", "https://")
    
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://krib-host-dahsboard.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics and monitoring
app.middleware("http")(metrics_middleware)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(financials.router, prefix="/api/financials", tags=["financials"])

# Long-term rental platform routers
app.include_router(agencies.router, prefix="/api/agencies", tags=["agencies"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(viewings.router, prefix="/api/viewings", tags=["viewings"])

@app.get("/")
async def root():
    return {
        "message": "Krib AI Long-Term Rental Platform API is running! 🏢✨",
        "version": "2.0.0",
        "platform": "Long-Term Rental Management System",
        "features": [
            "Multi-tenant agency management",
            "Agent territory assignments", 
            "Tenant application processing",
            "Property viewing scheduling",
            "Lease agreement management",
            "DocuSign integration",
            "AI-powered tenant qualification"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with monitoring"""
    return await health_check_with_metrics()

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
