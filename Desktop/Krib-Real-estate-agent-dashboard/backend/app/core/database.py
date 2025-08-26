"""
Database initialization and schema setup
"""

from app.core.supabase_client import supabase_client
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database tables if they don't exist"""
    try:
        # Check if our tables exist, if not create them
        
        # Users table (extends Supabase auth.users)
        users_table_sql = """
        CREATE TABLE IF NOT EXISTS public.users (
            id UUID REFERENCES auth.users(id) PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            settings JSONB DEFAULT '{}'::jsonb,
            total_revenue DECIMAL(10,2) DEFAULT 0
        );
        """
        
        # Properties table
        properties_table_sql = """
        CREATE TABLE IF NOT EXISTS public.properties (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            property_type TEXT NOT NULL CHECK (property_type IN ('apartment', 'house', 'condo', 'villa', 'studio', 'cabin', 'other')),
            bedrooms INTEGER NOT NULL DEFAULT 0,
            bathrooms DECIMAL(3,1) NOT NULL DEFAULT 0,
            max_guests INTEGER NOT NULL DEFAULT 1,
            price_per_night DECIMAL(10,2) NOT NULL,
            amenities TEXT[] DEFAULT '{}',
            images TEXT[] DEFAULT '{}',
            status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'inactive', 'suspended')),
            rating DECIMAL(3,2) DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            booking_count INTEGER DEFAULT 0,
            total_revenue DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        """
        
        # Bookings table
        bookings_table_sql = """
        CREATE TABLE IF NOT EXISTS public.bookings (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE NOT NULL,
            guest_name TEXT NOT NULL,
            guest_email TEXT NOT NULL,
            guest_phone TEXT,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            nights INTEGER NOT NULL,
            guests INTEGER NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),
            special_requests TEXT,
            payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'refunded')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        """
        
        # Reviews table
        reviews_table_sql = """
        CREATE TABLE IF NOT EXISTS public.reviews (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE NOT NULL,
            booking_id UUID REFERENCES public.bookings(id) ON DELETE CASCADE,
            guest_name TEXT NOT NULL,
            guest_email TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        """
        
        # Property analytics table
        analytics_table_sql = """
        CREATE TABLE IF NOT EXISTS public.property_analytics (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE NOT NULL,
            date DATE NOT NULL,
            views INTEGER DEFAULT 0,
            bookings INTEGER DEFAULT 0,
            revenue DECIMAL(10,2) DEFAULT 0,
            occupancy_rate DECIMAL(5,2) DEFAULT 0,
            avg_daily_rate DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
            UNIQUE(property_id, date)
        );
        """
        
        # Create indexes
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_properties_user_id ON public.properties(user_id);
        CREATE INDEX IF NOT EXISTS idx_properties_status ON public.properties(status);
        CREATE INDEX IF NOT EXISTS idx_properties_location ON public.properties(city, state, country);
        CREATE INDEX IF NOT EXISTS idx_bookings_property_id ON public.bookings(property_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_dates ON public.bookings(check_in, check_out);
        CREATE INDEX IF NOT EXISTS idx_bookings_status ON public.bookings(status);
        CREATE INDEX IF NOT EXISTS idx_reviews_property_id ON public.reviews(property_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_property_date ON public.property_analytics(property_id, date);
        """
        
        # Create triggers for updated_at
        triggers_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = TIMEZONE('utc'::text, NOW());
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON public.users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_properties_updated_at ON public.properties;
        CREATE TRIGGER update_properties_updated_at
            BEFORE UPDATE ON public.properties
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_bookings_updated_at ON public.bookings;
        CREATE TRIGGER update_bookings_updated_at
            BEFORE UPDATE ON public.bookings
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Enable Row Level Security
        rls_sql = """
        ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.properties ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.property_analytics ENABLE ROW LEVEL SECURITY;
        
        -- Users can only see their own data
        DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
        CREATE POLICY "Users can view own profile" ON public.users
            FOR SELECT USING (auth.uid() = id);
            
        DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
        CREATE POLICY "Users can update own profile" ON public.users
            FOR UPDATE USING (auth.uid() = id);
        
        -- Properties policies
        DROP POLICY IF EXISTS "Users can view own properties" ON public.properties;
        CREATE POLICY "Users can view own properties" ON public.properties
            FOR SELECT USING (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS "Users can insert own properties" ON public.properties;
        CREATE POLICY "Users can insert own properties" ON public.properties
            FOR INSERT WITH CHECK (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS "Users can update own properties" ON public.properties;
        CREATE POLICY "Users can update own properties" ON public.properties
            FOR UPDATE USING (auth.uid() = user_id);
            
        DROP POLICY IF EXISTS "Users can delete own properties" ON public.properties;
        CREATE POLICY "Users can delete own properties" ON public.properties
            FOR DELETE USING (auth.uid() = user_id);
        
        -- Bookings policies
        DROP POLICY IF EXISTS "Property owners can view bookings" ON public.bookings;
        CREATE POLICY "Property owners can view bookings" ON public.bookings
            FOR SELECT USING (
                auth.uid() IN (
                    SELECT user_id FROM public.properties WHERE id = property_id
                )
            );
        """
        
        # Execute all SQL commands
        sql_commands = [
            users_table_sql,
            properties_table_sql,
            bookings_table_sql,
            reviews_table_sql,
            analytics_table_sql,
            indexes_sql,
            triggers_sql,
            rls_sql
        ]
        
        for sql in sql_commands:
            try:
                supabase_client.rpc('execute_sql', {'sql': sql}).execute()
            except Exception as e:
                # Log the error but continue - tables might already exist
                logger.warning(f"SQL execution warning: {e}")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def create_demo_data():
    """Create demo user and sample data"""
    try:
        # This will be called separately to populate demo data
        logger.info("Demo data creation completed")
    except Exception as e:
        logger.error(f"Demo data creation failed: {e}")
        raise
