"""
Supabase client configuration
"""

from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase client with service role key for admin operations
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)

# Initialize Supabase client with anon key for user operations
supabase_anon: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)
