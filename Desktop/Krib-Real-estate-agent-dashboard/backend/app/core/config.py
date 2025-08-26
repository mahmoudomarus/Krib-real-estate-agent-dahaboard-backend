"""
Configuration settings for Krib AI backend
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Krib AI API"
    debug: bool = True
    secret_key: str = "your-super-secret-key-change-in-production"
    
    # JWT
    jwt_secret_key: str = "your-jwt-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    
    # Supabase S3-Compatible Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-2"
    s3_bucket_name: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    
    # AI Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Redis (Upstash)
    redis_url: str = "redis://localhost:6379"
    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None
    
    # Monitoring and Observability
    sentry_dsn: Optional[str] = None
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    # Rate Limiting
    enable_rate_limiting: bool = True
    default_rate_limit: str = "1000/hour"
    
    # DocuSign Integration
    docusign_integrator_key: Optional[str] = None
    docusign_user_id: Optional[str] = None
    docusign_account_id: Optional[str] = None
    docusign_base_url: str = "https://demo.docusign.net"
    docusign_app_name: str = "kribz"
    
    # Google Calendar Integration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_api_key: Optional[str] = None
    google_project_id: str = "krib-real-estate"
    
    # Render & Vercel Integration
    render_service_id: str = "srv-d2meovruibrs73bb53tg"
    vercel_project_id: str = "prj_UNmC6xr9pmDbiFXooaKt6fmfXKzN"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
