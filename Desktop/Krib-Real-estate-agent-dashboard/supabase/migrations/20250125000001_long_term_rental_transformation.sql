-- =====================================================================
-- KRIB AI LONG-TERM RENTAL PLATFORM - COMPLETE SCHEMA
-- Migration: Fresh setup for long-term rental management system
-- Date: January 25, 2025
-- =====================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- BASIC USERS TABLE (for auth integration)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    total_revenue DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users RLS policies
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- =====================================================================
-- ENHANCED PROPERTIES TABLE (supporting both short & long-term)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.properties (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Basic Information
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price_per_night DECIMAL(10,2),
    
    -- Location
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'UAE',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Property Details
    property_type VARCHAR(50) NOT NULL DEFAULT 'apartment',
    bedrooms INTEGER NOT NULL DEFAULT 1,
    bathrooms INTEGER NOT NULL DEFAULT 1,
    max_guests INTEGER DEFAULT 2,
    area_sqft INTEGER,
    
    -- Features & Amenities
    amenities TEXT[],
    house_rules TEXT[],
    images TEXT[],
    
    -- Availability & Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'rented')),
    is_featured BOOLEAN DEFAULT false,
    
    -- Long-Term Rental specific fields
    annual_rent DECIMAL(12,2) CHECK (annual_rent >= 0),
    monthly_rent DECIMAL(10,2),
    security_deposit DECIMAL(10,2) DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 2.50,
    minimum_lease_duration INTEGER DEFAULT 12,
    maximum_lease_duration INTEGER DEFAULT 24,
    lease_type VARCHAR(20) DEFAULT 'residential' CHECK (lease_type IN ('residential', 'commercial', 'mixed_use')),
    furnished_status VARCHAR(20) DEFAULT 'unfurnished' CHECK (furnished_status IN ('furnished', 'semi_furnished', 'unfurnished')),
    parking_spaces INTEGER DEFAULT 0,
    balcony_count INTEGER DEFAULT 0,
    maid_room BOOLEAN DEFAULT false,
    laundry_room BOOLEAN DEFAULT false,
    storage_room BOOLEAN DEFAULT false,
    building_name VARCHAR(255),
    building_year INTEGER CHECK (building_year >= 1970 AND building_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    total_floors INTEGER CHECK (total_floors > 0),
    property_floor INTEGER CHECK (property_floor >= 0),
    elevator_access BOOLEAN DEFAULT false,
    service_charges DECIMAL(10,2) DEFAULT 0,
    dewa_inclusive BOOLEAN DEFAULT false,
    internet_inclusive BOOLEAN DEFAULT false,
    maintenance_included BOOLEAN DEFAULT true,
    available_from DATE DEFAULT CURRENT_DATE,
    current_tenant_name VARCHAR(255),
    lease_expiry_date DATE,
    agent_id UUID,  -- Will add FK constraint after agencies table is created
    agency_id UUID,  -- Will add FK constraint after agencies table is created
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on properties table
ALTER TABLE public.properties ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- AGENCIES TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.agencies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    license_number VARCHAR(100) UNIQUE NOT NULL,
    license_expiry_date DATE NOT NULL,
    
    -- Contact Information
    head_office_address TEXT NOT NULL,
    emirates VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    website_url VARCHAR(255),
    
    -- Business Details
    rera_certificate_url TEXT,
    trade_license_url TEXT,
    establishment_year INTEGER,
    total_agents INTEGER DEFAULT 0,
    
    -- Subscription & Billing
    subscription_plan VARCHAR(20) DEFAULT 'basic' CHECK (subscription_plan IN ('basic', 'premium', 'enterprise')),
    subscription_status VARCHAR(20) DEFAULT 'active' CHECK (subscription_status IN ('active', 'suspended', 'cancelled')),
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'annual')),
    next_billing_date DATE,
    
    -- Commission Structure
    default_commission_rate DECIMAL(5,2) DEFAULT 2.50, -- 2.5%
    
    -- Status & Timestamps
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- AGENTS TABLE (Enhanced Users)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.agents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agency_id UUID REFERENCES public.agencies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Link to Supabase auth
    
    -- Personal Information
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    nationality VARCHAR(100),
    languages_spoken TEXT[] DEFAULT '{"English"}',
    
    -- Professional Information
    license_number VARCHAR(100) UNIQUE,
    license_expiry_date DATE,
    rera_certificate_url TEXT,
    years_experience INTEGER DEFAULT 0,
    
    -- Role & Permissions
    role VARCHAR(20) DEFAULT 'agent' CHECK (role IN ('agent', 'senior_agent', 'team_lead', 'manager', 'admin')),
    permissions TEXT[] DEFAULT '{}',
    
    -- Territory & Specialization
    assigned_territories TEXT[] DEFAULT '{}',
    property_specializations TEXT[] DEFAULT '{}',
    
    -- Performance & Commission
    commission_rate DECIMAL(5,2) DEFAULT 2.50,
    monthly_target DECIMAL(12,2) DEFAULT 0,
    annual_target DECIMAL(12,2) DEFAULT 0,
    total_deals_closed INTEGER DEFAULT 0,
    total_commission_earned DECIMAL(12,2) DEFAULT 0,
    
    -- Contact Preferences
    whatsapp_number VARCHAR(20),
    preferred_contact_method VARCHAR(20) DEFAULT 'phone' CHECK (preferred_contact_method IN ('phone', 'email', 'whatsapp')),
    
    -- Calendar Integration
    google_calendar_id VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'Asia/Dubai',
    working_hours JSONB DEFAULT '{"start": "09:00", "end": "18:00", "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]}',
    
    -- Status & Authentication
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(agency_id, email)
);

-- =====================================================================
-- TENANT APPLICATIONS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.tenant_applications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    
    -- Application Tracking
    application_number VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('submitted', 'documents_pending', 'under_review', 'credit_check', 'approved', 'rejected', 'withdrawn')),
    
    -- Primary Applicant
    primary_applicant_name VARCHAR(255) NOT NULL,
    primary_applicant_email VARCHAR(255) NOT NULL,
    primary_applicant_phone VARCHAR(20) NOT NULL,
    primary_applicant_nationality VARCHAR(100),
    primary_applicant_passport VARCHAR(50),
    primary_applicant_emirates_id VARCHAR(20),
    
    -- Employment Information
    employer_name VARCHAR(255),
    job_title VARCHAR(255),
    monthly_income DECIMAL(10,2),
    employment_type VARCHAR(50) CHECK (employment_type IN ('permanent', 'contract', 'freelancer', 'self_employed')),
    work_permit_expiry DATE,
    
    -- Lease Preferences
    desired_move_in_date DATE NOT NULL,
    lease_duration_months INTEGER NOT NULL CHECK (lease_duration_months >= 6),
    maximum_budget DECIMAL(10,2) NOT NULL,
    furnished_preference VARCHAR(20) CHECK (furnished_preference IN ('furnished', 'unfurnished', 'semi_furnished', 'no_preference')),
    
    -- Current Housing
    current_address TEXT,
    current_monthly_rent DECIMAL(10,2),
    reason_for_moving TEXT,
    notice_period_days INTEGER,
    
    -- Family Information
    family_size INTEGER DEFAULT 1,
    children_count INTEGER DEFAULT 0,
    pet_ownership BOOLEAN DEFAULT false,
    pet_details TEXT,
    
    -- References
    previous_landlord_name VARCHAR(255),
    previous_landlord_phone VARCHAR(20),
    employer_reference_name VARCHAR(255),
    employer_reference_phone VARCHAR(20),
    
    -- Financial Information
    bank_statements_provided BOOLEAN DEFAULT false,
    salary_certificate_provided BOOLEAN DEFAULT false,
    credit_score INTEGER,
    credit_check_date DATE,
    credit_check_status VARCHAR(20) CHECK (credit_check_status IN ('pending', 'approved', 'rejected', 'not_required')),
    
    -- Application Processing
    review_notes TEXT[],
    rejection_reason TEXT,
    approval_conditions TEXT[],
    
    -- Security & Compliance
    identity_verified BOOLEAN DEFAULT false,
    income_verified BOOLEAN DEFAULT false,
    reference_verified BOOLEAN DEFAULT false,
    background_check_status VARCHAR(20) DEFAULT 'pending' CHECK (background_check_status IN ('pending', 'clear', 'flagged', 'not_required')),
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- APPLICATION DOCUMENTS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.application_documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    application_id UUID REFERENCES public.tenant_applications(id) ON DELETE CASCADE,
    
    -- Document Information
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN (
        'passport', 'emirates_id', 'visa_page', 'salary_certificate', 
        'bank_statement', 'employment_contract', 'noc_letter', 
        'previous_lease_agreement', 'utility_bill', 'other'
    )),
    document_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Verification Status
    verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected', 'expired')),
    verified_by_agent_id UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    verification_notes TEXT,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Document Metadata
    expiry_date DATE,
    issued_date DATE,
    issuing_authority VARCHAR(255),
    
    -- Upload Information
    uploaded_by VARCHAR(20) CHECK (uploaded_by IN ('applicant', 'agent', 'system')),
    upload_ip_address INET,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- PROPERTY VIEWINGS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.property_viewings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    application_id UUID REFERENCES public.tenant_applications(id) ON DELETE SET NULL,
    
    -- Viewing Details
    viewing_number VARCHAR(20) UNIQUE NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30 CHECK (duration_minutes > 0),
    
    -- Applicant Information
    applicant_name VARCHAR(255) NOT NULL,
    applicant_email VARCHAR(255) NOT NULL,
    applicant_phone VARCHAR(20) NOT NULL,
    number_of_attendees INTEGER DEFAULT 1,
    
    -- Viewing Type & Method
    viewing_type VARCHAR(20) DEFAULT 'in_person' CHECK (viewing_type IN ('in_person', 'virtual', 'self_guided')),
    meeting_platform VARCHAR(50),
    meeting_link TEXT,
    meeting_password VARCHAR(50),
    
    -- Status Tracking
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show', 'rescheduled')),
    confirmation_status VARCHAR(20) DEFAULT 'pending' CHECK (confirmation_status IN ('pending', 'confirmed', 'declined')),
    
    -- Communication
    confirmation_sent_at TIMESTAMP WITH TIME ZONE,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    follow_up_required BOOLEAN DEFAULT false,
    
    -- Viewing Notes & Feedback
    agent_pre_notes TEXT,
    agent_post_notes TEXT,
    applicant_feedback TEXT,
    property_condition_notes TEXT,
    interest_level VARCHAR(20) CHECK (interest_level IN ('very_interested', 'interested', 'neutral', 'not_interested')),
    
    -- Follow-up Actions
    follow_up_actions TEXT[],
    next_steps TEXT,
    application_submitted BOOLEAN DEFAULT false,
    
    -- Integration
    google_calendar_event_id VARCHAR(255),
    whatsapp_group_id VARCHAR(255),
    
    -- Cancellation Information
    cancelled_by VARCHAR(20) CHECK (cancelled_by IN ('agent', 'applicant', 'system')),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Rescheduling
    original_viewing_id UUID REFERENCES public.property_viewings(id),
    rescheduled_from_date DATE,
    rescheduled_from_time TIME,
    reschedule_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- AGENT AVAILABILITY TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.agent_availability (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id UUID REFERENCES public.agents(id) ON DELETE CASCADE,
    
    -- Availability Slot
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL CHECK (end_time > start_time),
    
    -- Slot Information
    is_available BOOLEAN DEFAULT true,
    max_viewings INTEGER DEFAULT 3,
    current_bookings INTEGER DEFAULT 0,
    
    -- Slot Type
    slot_type VARCHAR(20) DEFAULT 'regular' CHECK (slot_type IN ('regular', 'extended', 'emergency', 'blocked')),
    recurring_pattern VARCHAR(20) CHECK (recurring_pattern IN ('none', 'daily', 'weekly', 'monthly')),
    
    -- Location Preference
    preferred_areas TEXT[],
    travel_buffer_minutes INTEGER DEFAULT 30,
    
    -- Notes
    notes TEXT,
    blocked_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(agent_id, date, start_time)
);

-- =====================================================================
-- LEASE AGREEMENTS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.lease_agreements (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    property_id UUID REFERENCES public.properties(id) ON DELETE CASCADE,
    tenant_application_id UUID REFERENCES public.tenant_applications(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    agency_id UUID REFERENCES public.agencies(id) ON DELETE CASCADE,
    
    -- Lease Identification
    lease_number VARCHAR(20) UNIQUE NOT NULL,
    contract_type VARCHAR(20) DEFAULT 'residential' CHECK (contract_type IN ('residential', 'commercial', 'mixed_use')),
    
    -- Parties Information
    landlord_name VARCHAR(255) NOT NULL,
    landlord_email VARCHAR(255),
    landlord_phone VARCHAR(20),
    landlord_emirates_id VARCHAR(20),
    
    tenant_name VARCHAR(255) NOT NULL,
    tenant_email VARCHAR(255) NOT NULL,
    tenant_phone VARCHAR(20) NOT NULL,
    tenant_emirates_id VARCHAR(20),
    tenant_passport VARCHAR(50),
    
    -- Lease Terms
    lease_start_date DATE NOT NULL,
    lease_end_date DATE NOT NULL CHECK (lease_end_date > lease_start_date),
    lease_duration_months INTEGER,
    
    -- Financial Terms
    annual_rent DECIMAL(12,2) NOT NULL CHECK (annual_rent > 0),
    monthly_rent DECIMAL(10,2),
    security_deposit DECIMAL(10,2) NOT NULL CHECK (security_deposit >= 0),
    broker_commission DECIMAL(10,2) NOT NULL CHECK (broker_commission >= 0),
    commission_percentage DECIMAL(5,2),
    
    -- Payment Terms
    payment_schedule VARCHAR(20) DEFAULT 'annual' CHECK (payment_schedule IN ('monthly', 'quarterly', 'semi_annual', 'annual')),
    payment_method VARCHAR(20) DEFAULT 'bank_transfer' CHECK (payment_method IN ('bank_transfer', 'cheque', 'cash', 'online')),
    payment_due_day INTEGER DEFAULT 1 CHECK (payment_due_day >= 1 AND payment_due_day <= 28),
    late_payment_penalty_percentage DECIMAL(5,2) DEFAULT 5.00,
    
    -- Additional Charges
    service_charges_annual DECIMAL(10,2) DEFAULT 0,
    dewa_included BOOLEAN DEFAULT false,
    internet_included BOOLEAN DEFAULT false,
    maintenance_included BOOLEAN DEFAULT true,
    parking_included BOOLEAN DEFAULT false,
    additional_charges JSONB,
    
    -- Contract Terms
    auto_renewal BOOLEAN DEFAULT false,
    renewal_notice_period_days INTEGER DEFAULT 90,
    early_termination_allowed BOOLEAN DEFAULT false,
    early_termination_penalty DECIMAL(10,2),
    
    -- Property Condition
    furnished_status VARCHAR(20) CHECK (furnished_status IN ('furnished', 'semi_furnished', 'unfurnished')),
    inventory_list_url TEXT,
    property_condition_report_url TEXT,
    
    -- Legal Compliance
    rera_permit_number VARCHAR(100),
    ejari_registration_number VARCHAR(100),
    municipality_approval BOOLEAN DEFAULT false,
    
    -- Document Management
    contract_template_id UUID,
    docusign_envelope_id VARCHAR(255),
    signed_contract_url TEXT,
    
    -- Signature Status
    landlord_signature_status VARCHAR(20) DEFAULT 'pending' CHECK (landlord_signature_status IN ('pending', 'signed', 'declined')),
    landlord_signed_at TIMESTAMP WITH TIME ZONE,
    landlord_ip_address INET,
    
    tenant_signature_status VARCHAR(20) DEFAULT 'pending' CHECK (tenant_signature_status IN ('pending', 'signed', 'declined')),
    tenant_signed_at TIMESTAMP WITH TIME ZONE,
    tenant_ip_address INET,
    
    witness_required BOOLEAN DEFAULT true,
    witness_signature_status VARCHAR(20) DEFAULT 'pending' CHECK (witness_signature_status IN ('pending', 'signed', 'not_required')),
    witness_name VARCHAR(255),
    witness_emirates_id VARCHAR(20),
    witness_signed_at TIMESTAMP WITH TIME ZONE,
    
    -- Agreement Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent_for_signature', 'partially_signed', 'fully_executed', 'active', 'expired', 'terminated', 'cancelled')),
    execution_date DATE,
    registration_date DATE,
    
    -- Renewal Information
    renewal_eligibility BOOLEAN DEFAULT true,
    renewal_rent_increase_percentage DECIMAL(5,2),
    renewal_terms_notes TEXT,
    
    -- Termination Information
    termination_date DATE,
    termination_reason TEXT,
    termination_notice_served_date DATE,
    termination_penalty_paid DECIMAL(10,2),
    
    -- Commission Tracking
    commission_status VARCHAR(20) DEFAULT 'pending' CHECK (commission_status IN ('pending', 'invoiced', 'paid', 'disputed')),
    commission_invoice_number VARCHAR(50),
    commission_paid_date DATE,
    commission_payment_reference VARCHAR(100),
    
    -- Notes & Special Conditions
    special_conditions TEXT[],
    agent_notes TEXT,
    internal_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- CONTRACT TEMPLATES TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.contract_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agency_id UUID REFERENCES public.agencies(id) ON DELETE CASCADE,
    
    -- Template Information
    template_name VARCHAR(255) NOT NULL,
    template_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    description TEXT,
    
    -- Template Categorization
    property_type VARCHAR(20) CHECK (property_type IN ('residential', 'commercial', 'mixed_use')),
    contract_language VARCHAR(10) DEFAULT 'en' CHECK (contract_language IN ('en', 'ar', 'both')),
    emirates VARCHAR(50),
    
    -- Template Content
    template_content JSONB NOT NULL,
    docusign_template_id VARCHAR(255),
    
    -- Legal Compliance
    rera_compliant BOOLEAN DEFAULT false,
    dubai_land_department_approved BOOLEAN DEFAULT false,
    municipality_approved BOOLEAN DEFAULT false,
    legal_review_date DATE,
    legal_reviewer_name VARCHAR(255),
    
    -- Usage Statistics
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Template Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),
    is_default BOOLEAN DEFAULT false,
    
    -- Version Control
    parent_template_id UUID REFERENCES public.contract_templates(id),
    changelog TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

    
    -- Long-Term Rental specific fields
    annual_rent DECIMAL(12,2) CHECK (annual_rent >= 0),
    monthly_rent DECIMAL(10,2),
    security_deposit DECIMAL(10,2) DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 2.50,
    minimum_lease_duration INTEGER DEFAULT 12,
    maximum_lease_duration INTEGER DEFAULT 24,
    lease_type VARCHAR(20) DEFAULT 'residential' CHECK (lease_type IN ('residential', 'commercial', 'mixed_use')),
    furnished_status VARCHAR(20) DEFAULT 'unfurnished' CHECK (furnished_status IN ('furnished', 'semi_furnished', 'unfurnished')),
    parking_spaces INTEGER DEFAULT 0,
    balcony_count INTEGER DEFAULT 0,
    maid_room BOOLEAN DEFAULT false,
    laundry_room BOOLEAN DEFAULT false,
    storage_room BOOLEAN DEFAULT false,
    building_name VARCHAR(255),
    building_year INTEGER CHECK (building_year >= 1970 AND building_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    total_floors INTEGER CHECK (total_floors > 0),
    property_floor INTEGER CHECK (property_floor >= 0),
    elevator_access BOOLEAN DEFAULT false,
    service_charges DECIMAL(10,2) DEFAULT 0,
    dewa_inclusive BOOLEAN DEFAULT false,
    internet_inclusive BOOLEAN DEFAULT false,
    maintenance_included BOOLEAN DEFAULT true,
    available_from DATE DEFAULT CURRENT_DATE,
    current_tenant_name VARCHAR(255),
    lease_expiry_date DATE,
    agent_id UUID,  -- Will add FK constraint after agencies table is created
    agency_id UUID  -- Will add FK constraint after agencies table is created
);

-- Update property_type constraint to include UAE-specific types
ALTER TABLE public.properties 
ADD CONSTRAINT properties_property_type_check 
CHECK (property_type IN ('apartment', 'villa', 'townhouse', 'penthouse', 'studio', 'duplex', 'compound', 'office', 'retail', 'warehouse', 'land', 'other'));

-- Add foreign key constraints for agent and agency (after tables are created)
-- These will be added later in the migration after agencies and agents tables are created

-- =====================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- =====================================================================

-- Agencies indexes
CREATE INDEX IF NOT EXISTS idx_agencies_license_number ON public.agencies(license_number);
CREATE INDEX IF NOT EXISTS idx_agencies_emirates ON public.agencies(emirates);
CREATE INDEX IF NOT EXISTS idx_agencies_status ON public.agencies(status);

-- Agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_agency_id ON public.agents(agency_id);
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON public.agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_email ON public.agents(email);
CREATE INDEX IF NOT EXISTS idx_agents_status ON public.agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_territories ON public.agents USING GIN(assigned_territories);

-- Properties indexes (new)
CREATE INDEX IF NOT EXISTS idx_properties_agent_id ON public.properties(agent_id);
CREATE INDEX IF NOT EXISTS idx_properties_agency_id ON public.properties(agency_id);
CREATE INDEX IF NOT EXISTS idx_properties_lease_type ON public.properties(lease_type);
CREATE INDEX IF NOT EXISTS idx_properties_available_from ON public.properties(available_from);
CREATE INDEX IF NOT EXISTS idx_properties_annual_rent ON public.properties(annual_rent);
CREATE INDEX IF NOT EXISTS idx_properties_furnished_status ON public.properties(furnished_status);

-- Applications indexes
CREATE INDEX IF NOT EXISTS idx_applications_property_id ON public.tenant_applications(property_id);
CREATE INDEX IF NOT EXISTS idx_applications_agent_id ON public.tenant_applications(agent_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON public.tenant_applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_submitted_at ON public.tenant_applications(submitted_at);
CREATE INDEX IF NOT EXISTS idx_applications_email ON public.tenant_applications(primary_applicant_email);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_application_id ON public.application_documents(application_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON public.application_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_verification_status ON public.application_documents(verification_status);

-- Viewings indexes
CREATE INDEX IF NOT EXISTS idx_viewings_property_id ON public.property_viewings(property_id);
CREATE INDEX IF NOT EXISTS idx_viewings_agent_id ON public.property_viewings(agent_id);
CREATE INDEX IF NOT EXISTS idx_viewings_scheduled_date ON public.property_viewings(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_viewings_status ON public.property_viewings(status);
CREATE INDEX IF NOT EXISTS idx_viewings_applicant_email ON public.property_viewings(applicant_email);

-- Availability indexes
CREATE INDEX IF NOT EXISTS idx_availability_agent_id ON public.agent_availability(agent_id);
CREATE INDEX IF NOT EXISTS idx_availability_date ON public.agent_availability(date);
CREATE INDEX IF NOT EXISTS idx_availability_is_available ON public.agent_availability(is_available);

-- Lease agreements indexes
CREATE INDEX IF NOT EXISTS idx_leases_property_id ON public.lease_agreements(property_id);
CREATE INDEX IF NOT EXISTS idx_leases_agent_id ON public.lease_agreements(agent_id);
CREATE INDEX IF NOT EXISTS idx_leases_agency_id ON public.lease_agreements(agency_id);
CREATE INDEX IF NOT EXISTS idx_leases_status ON public.lease_agreements(status);
CREATE INDEX IF NOT EXISTS idx_leases_lease_start_date ON public.lease_agreements(lease_start_date);
CREATE INDEX IF NOT EXISTS idx_leases_lease_end_date ON public.lease_agreements(lease_end_date);

-- Contract templates indexes
CREATE INDEX IF NOT EXISTS idx_templates_agency_id ON public.contract_templates(agency_id);
CREATE INDEX IF NOT EXISTS idx_templates_property_type ON public.contract_templates(property_type);
CREATE INDEX IF NOT EXISTS idx_templates_status ON public.contract_templates(status);

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

-- Enable RLS on all tables
ALTER TABLE public.agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_viewings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lease_agreements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contract_templates ENABLE ROW LEVEL SECURITY;

-- Agencies policies
CREATE POLICY "Agencies can view own data" ON public.agencies
    FOR ALL USING (id IN (
        SELECT agency_id FROM public.agents WHERE user_id = auth.uid()
    ));

-- Agents policies
CREATE POLICY "Agents can view own agency data" ON public.agents
    FOR ALL USING (
        user_id = auth.uid() OR 
        agency_id IN (
            SELECT agency_id FROM public.agents WHERE user_id = auth.uid()
        )
    );

-- Properties policies (updated)
DROP POLICY IF EXISTS "Users can view own properties" ON public.properties;
CREATE POLICY "Agents can view agency properties" ON public.properties
    FOR ALL USING (
        agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid()) OR
        agency_id IN (SELECT agency_id FROM public.agents WHERE user_id = auth.uid()) OR
        user_id = auth.uid() -- Keep backward compatibility
    );

-- Applications policies
CREATE POLICY "Agents can view applications for their properties" ON public.tenant_applications
    FOR ALL USING (
        agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid()) OR
        property_id IN (
            SELECT id FROM public.properties WHERE 
            agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid()) OR
            agency_id IN (SELECT agency_id FROM public.agents WHERE user_id = auth.uid())
        )
    );

-- Documents policies
CREATE POLICY "Agents can view documents for their applications" ON public.application_documents
    FOR ALL USING (
        application_id IN (
            SELECT id FROM public.tenant_applications WHERE
            agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid())
        )
    );

-- Viewings policies
CREATE POLICY "Agents can view their viewings" ON public.property_viewings
    FOR ALL USING (
        agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid())
    );

-- Availability policies
CREATE POLICY "Agents can manage their availability" ON public.agent_availability
    FOR ALL USING (
        agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid())
    );

-- Lease agreements policies
CREATE POLICY "Agents can view their lease agreements" ON public.lease_agreements
    FOR ALL USING (
        agent_id IN (SELECT id FROM public.agents WHERE user_id = auth.uid()) OR
        agency_id IN (SELECT agency_id FROM public.agents WHERE user_id = auth.uid())
    );

-- Contract templates policies
CREATE POLICY "Agencies can manage their templates" ON public.contract_templates
    FOR ALL USING (
        agency_id IN (SELECT agency_id FROM public.agents WHERE user_id = auth.uid())
    );

-- =====================================================================
-- TRIGGERS FOR AUTO-GENERATION AND UPDATES
-- =====================================================================

-- Function to generate application numbers
CREATE OR REPLACE FUNCTION generate_application_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.application_number := 'APP-' || TO_CHAR(NOW(), 'YYYY') || '-' || 
                             LPAD(NEXTVAL('application_number_seq')::text, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create sequence for application numbers
CREATE SEQUENCE IF NOT EXISTS application_number_seq START 1;

-- Create trigger for application numbers
DROP TRIGGER IF EXISTS trigger_generate_application_number ON public.tenant_applications;
CREATE TRIGGER trigger_generate_application_number
    BEFORE INSERT ON public.tenant_applications
    FOR EACH ROW
    EXECUTE FUNCTION generate_application_number();

-- Function to generate viewing numbers
CREATE OR REPLACE FUNCTION generate_viewing_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.viewing_number := 'VIEW-' || TO_CHAR(NOW(), 'YYYY') || '-' || 
                         LPAD(NEXTVAL('viewing_number_seq')::text, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create sequence for viewing numbers
CREATE SEQUENCE IF NOT EXISTS viewing_number_seq START 1;

-- Create trigger for viewing numbers
DROP TRIGGER IF EXISTS trigger_generate_viewing_number ON public.property_viewings;
CREATE TRIGGER trigger_generate_viewing_number
    BEFORE INSERT ON public.property_viewings
    FOR EACH ROW
    EXECUTE FUNCTION generate_viewing_number();

-- Function to generate lease numbers
CREATE OR REPLACE FUNCTION generate_lease_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.lease_number := 'LEASE-' || TO_CHAR(NOW(), 'YYYY') || '-' || 
                       LPAD(NEXTVAL('lease_number_seq')::text, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create sequence for lease numbers
CREATE SEQUENCE IF NOT EXISTS lease_number_seq START 1;

-- Create trigger for lease numbers
DROP TRIGGER IF EXISTS trigger_generate_lease_number ON public.lease_agreements;
CREATE TRIGGER trigger_generate_lease_number
    BEFORE INSERT ON public.lease_agreements
    FOR EACH ROW
    EXECUTE FUNCTION generate_lease_number();

-- Function to update agency agent count
CREATE OR REPLACE FUNCTION update_agency_agent_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.agencies 
        SET total_agents = total_agents + 1 
        WHERE id = NEW.agency_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.agencies 
        SET total_agents = total_agents - 1 
        WHERE id = OLD.agency_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for agency agent count
DROP TRIGGER IF EXISTS trigger_update_agency_agent_count ON public.agents;
CREATE TRIGGER trigger_update_agency_agent_count
    AFTER INSERT OR DELETE ON public.agents
    FOR EACH ROW
    EXECUTE FUNCTION update_agency_agent_count();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create update triggers for all tables
CREATE TRIGGER trigger_agencies_updated_at
    BEFORE UPDATE ON public.agencies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_agents_updated_at
    BEFORE UPDATE ON public.agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_applications_updated_at
    BEFORE UPDATE ON public.tenant_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON public.application_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_viewings_updated_at
    BEFORE UPDATE ON public.property_viewings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_availability_updated_at
    BEFORE UPDATE ON public.agent_availability
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_leases_updated_at
    BEFORE UPDATE ON public.lease_agreements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_templates_updated_at
    BEFORE UPDATE ON public.contract_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Also update the properties table trigger
DROP TRIGGER IF EXISTS trigger_properties_updated_at ON public.properties;
CREATE TRIGGER trigger_properties_updated_at
    BEFORE UPDATE ON public.properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate lease and financial fields
CREATE OR REPLACE FUNCTION calculate_lease_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate monthly rent from annual rent
    IF NEW.annual_rent IS NOT NULL THEN
        NEW.monthly_rent = NEW.annual_rent / 12;
    END IF;
    
    -- Calculate lease duration in months
    IF NEW.lease_start_date IS NOT NULL AND NEW.lease_end_date IS NOT NULL THEN
        NEW.lease_duration_months = (
            EXTRACT(YEAR FROM AGE(NEW.lease_end_date, NEW.lease_start_date)) * 12 + 
            EXTRACT(MONTH FROM AGE(NEW.lease_end_date, NEW.lease_start_date))
        );
    END IF;
    
    -- Calculate commission percentage
    IF NEW.annual_rent IS NOT NULL AND NEW.annual_rent > 0 AND NEW.broker_commission IS NOT NULL THEN
        NEW.commission_percentage = (NEW.broker_commission / NEW.annual_rent) * 100;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for lease agreements
CREATE TRIGGER trigger_calculate_lease_fields
    BEFORE INSERT OR UPDATE ON public.lease_agreements
    FOR EACH ROW
    EXECUTE FUNCTION calculate_lease_fields();

-- Function to calculate property monthly rent
CREATE OR REPLACE FUNCTION calculate_property_rent()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate monthly rent from annual rent or price per night
    IF NEW.annual_rent IS NOT NULL THEN
        NEW.monthly_rent = NEW.annual_rent / 12;
    ELSIF NEW.price_per_night IS NOT NULL THEN
        NEW.monthly_rent = NEW.price_per_night * 30;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for properties
CREATE TRIGGER trigger_calculate_property_rent
    BEFORE INSERT OR UPDATE ON public.properties
    FOR EACH ROW
    EXECUTE FUNCTION calculate_property_rent();

-- =====================================================================
-- ADD FOREIGN KEY CONSTRAINTS
-- =====================================================================

-- Add foreign key constraints for properties table
ALTER TABLE public.properties 
ADD CONSTRAINT fk_properties_agent_id 
FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;

ALTER TABLE public.properties 
ADD CONSTRAINT fk_properties_agency_id 
FOREIGN KEY (agency_id) REFERENCES public.agencies(id) ON DELETE CASCADE;

-- =====================================================================
-- SAMPLE DATA INSERT
-- =====================================================================

-- Insert sample agency
INSERT INTO public.agencies (
    name, license_number, license_expiry_date, head_office_address, 
    emirates, phone, email, establishment_year
) VALUES (
    'Krib Real Estate', 'RERA-2024-001', '2025-12-31', 
    'Business Bay, Dubai, UAE', 'Dubai', '+971-4-123-4567', 
    'info@kribrealestate.ae', 2024
) ON CONFLICT DO NOTHING;

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

-- Add comment to track migration
COMMENT ON SCHEMA public IS 'Long-term rental platform - Migration completed on 2025-01-25';
