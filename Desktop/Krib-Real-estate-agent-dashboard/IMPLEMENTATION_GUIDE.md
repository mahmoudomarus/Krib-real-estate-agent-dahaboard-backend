# 🚀 Long-Term Rental Platform - Implementation Guide

## 📋 Development Checklist

This guide provides step-by-step instructions for transforming the short-term rental system into a long-term rental platform. Each task includes specific file changes, code snippets, and implementation details.

---

## 🎯 **PHASE 1: Database Schema & Backend Foundation (Week 1-2)**

### **Task 1.1: Create New Database Migration**

#### **File**: `supabase/migrations/20240125000001_long_term_rental_transformation.sql`

```sql
-- =====================================================================
-- LONG-TERM RENTAL PLATFORM TRANSFORMATION
-- Migration: Convert short-term to long-term rental system
-- =====================================================================

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
    lease_duration_months INTEGER GENERATED ALWAYS AS (
        EXTRACT(YEAR FROM AGE(lease_end_date, lease_start_date)) * 12 + 
        EXTRACT(MONTH FROM AGE(lease_end_date, lease_start_date))
    ) STORED,
    
    -- Financial Terms
    annual_rent DECIMAL(12,2) NOT NULL CHECK (annual_rent > 0),
    monthly_rent DECIMAL(10,2) GENERATED ALWAYS AS (annual_rent / 12) STORED,
    security_deposit DECIMAL(10,2) NOT NULL CHECK (security_deposit >= 0),
    broker_commission DECIMAL(10,2) NOT NULL CHECK (broker_commission >= 0),
    commission_percentage DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN annual_rent > 0 THEN (broker_commission / annual_rent) * 100 ELSE 0 END
    ) STORED,
    
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

-- =====================================================================
-- ALTER EXISTING PROPERTIES TABLE
-- =====================================================================

-- Add Long-Term Rental specific columns
ALTER TABLE public.properties 
ADD COLUMN IF NOT EXISTS annual_rent DECIMAL(12,2) CHECK (annual_rent >= 0),
ADD COLUMN IF NOT EXISTS monthly_rent DECIMAL(10,2) GENERATED ALWAYS AS (COALESCE(annual_rent / 12, price_per_night * 30)) STORED,
ADD COLUMN IF NOT EXISTS security_deposit DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(5,2) DEFAULT 2.50,
ADD COLUMN IF NOT EXISTS minimum_lease_duration INTEGER DEFAULT 12,
ADD COLUMN IF NOT EXISTS maximum_lease_duration INTEGER DEFAULT 24,
ADD COLUMN IF NOT EXISTS lease_type VARCHAR(20) DEFAULT 'residential' CHECK (lease_type IN ('residential', 'commercial', 'mixed_use')),
ADD COLUMN IF NOT EXISTS furnished_status VARCHAR(20) DEFAULT 'unfurnished' CHECK (furnished_status IN ('furnished', 'semi_furnished', 'unfurnished')),
ADD COLUMN IF NOT EXISTS parking_spaces INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS balcony_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS maid_room BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS laundry_room BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS storage_room BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS building_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS building_year INTEGER CHECK (building_year >= 1970 AND building_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
ADD COLUMN IF NOT EXISTS total_floors INTEGER CHECK (total_floors > 0),
ADD COLUMN IF NOT EXISTS property_floor INTEGER CHECK (property_floor >= 0),
ADD COLUMN IF NOT EXISTS elevator_access BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS service_charges DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS dewa_inclusive BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS internet_inclusive BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS maintenance_included BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS available_from DATE DEFAULT CURRENT_DATE,
ADD COLUMN IF NOT EXISTS current_tenant_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS lease_expiry_date DATE,
ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES public.agents(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS agency_id UUID REFERENCES public.agencies(id) ON DELETE CASCADE;

-- Update property_type enum to include UAE-specific types
ALTER TABLE public.properties 
DROP CONSTRAINT IF EXISTS properties_property_type_check;

ALTER TABLE public.properties 
ADD CONSTRAINT properties_property_type_check 
CHECK (property_type IN ('apartment', 'villa', 'townhouse', 'penthouse', 'studio', 'duplex', 'compound', 'office', 'retail', 'warehouse', 'land', 'other'));

-- =====================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- =====================================================================

-- Agencies indexes
CREATE INDEX IF NOT EXISTS idx_agencies_license_number ON public.agencies(license_number);
CREATE INDEX IF NOT EXISTS idx_agencies_emirates ON public.agencies(emirates);
CREATE INDEX IF NOT EXISTS idx_agencies_status ON public.agencies(status);

-- Agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_agency_id ON public.agents(agency_id);
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
        agency_id IN (SELECT agency_id FROM public.agents WHERE user_id = auth.uid())
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
CREATE TRIGGER trigger_properties_updated_at
    BEFORE UPDATE ON public.properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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
COMMENT ON SCHEMA public IS 'Long-term rental platform - Migration completed on ' || NOW()::date;
```

### **Task 1.2: Update Backend Dependencies**

#### **File**: `backend/requirements.txt`

Add these new dependencies:
```txt
# Existing dependencies (keep all current ones)

# DocuSign Integration
docusign-esign==3.20.0
python-jose[cryptography]==3.3.0

# Calendar Integration  
google-api-python-client==2.109.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0

# PDF Generation for Contracts
reportlab==4.0.4
PyPDF2==3.0.1

# Enhanced Email Templates
jinja2==3.1.2

# Image Processing for Document Verification
Pillow==10.1.0
pytesseract==0.3.10  # OCR for document reading

# Phone Number Validation
phonenumbers==8.13.25

# Additional Validation
email-validator==2.1.0
```

### **Task 1.3: Create New Pydantic Models**

#### **File**: `backend/app/models/agency_schemas.py`

```python
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

# =====================================================================
# AGENCY MODELS
# =====================================================================

class SubscriptionPlan(str, Enum):
    basic = "basic"
    premium = "premium" 
    enterprise = "enterprise"

class SubscriptionStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    cancelled = "cancelled"

class BillingCycle(str, Enum):
    monthly = "monthly"
    annual = "annual"

class AgencyStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class AgencyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    license_number: str = Field(..., min_length=5, max_length=100)
    license_expiry_date: date
    head_office_address: str = Field(..., min_length=10)
    emirates: str = Field(..., regex="^(Dubai|Abu Dhabi|Sharjah|Ajman|Ras Al Khaimah|Fujairah|Umm Al Quwain)$")
    phone: str = Field(..., regex="^\\+971[0-9]{8,9}$")
    email: EmailStr
    website_url: Optional[str] = None
    establishment_year: Optional[int] = Field(None, ge=1970, le=2024)
    default_commission_rate: Optional[Decimal] = Field(Decimal("2.50"), ge=0, le=10)
    subscription_plan: SubscriptionPlan = SubscriptionPlan.basic

    class Config:
        use_enum_values = True

class AgencyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    head_office_address: Optional[str] = None
    phone: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    default_commission_rate: Optional[Decimal] = Field(None, ge=0, le=10)
    subscription_plan: Optional[SubscriptionPlan] = None
    status: Optional[AgencyStatus] = None

class AgencyResponse(BaseModel):
    id: UUID
    name: str
    license_number: str
    license_expiry_date: date
    head_office_address: str
    emirates: str
    phone: str
    email: str
    website_url: Optional[str]
    establishment_year: Optional[int]
    total_agents: int
    subscription_plan: SubscriptionPlan
    subscription_status: SubscriptionStatus
    default_commission_rate: Decimal
    status: AgencyStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# AGENT MODELS
# =====================================================================

class AgentRole(str, Enum):
    agent = "agent"
    senior_agent = "senior_agent"
    team_lead = "team_lead"
    manager = "manager"
    admin = "admin"

class ContactMethod(str, Enum):
    phone = "phone"
    email = "email"
    whatsapp = "whatsapp"

class AgentStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class WorkingHours(BaseModel):
    start: str = Field("09:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end: str = Field("18:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

class AgentCreate(BaseModel):
    agency_id: UUID
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., regex="^\\+971[0-9]{8,9}$")
    nationality: Optional[str] = None
    languages_spoken: List[str] = ["English"]
    license_number: Optional[str] = None
    license_expiry_date: Optional[date] = None
    years_experience: int = Field(0, ge=0, le=50)
    role: AgentRole = AgentRole.agent
    permissions: List[str] = []
    assigned_territories: List[str] = []
    property_specializations: List[str] = []
    commission_rate: Decimal = Field(Decimal("2.50"), ge=0, le=10)
    monthly_target: Decimal = Field(Decimal("0"), ge=0)
    annual_target: Decimal = Field(Decimal("0"), ge=0)
    whatsapp_number: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    preferred_contact_method: ContactMethod = ContactMethod.phone
    timezone: str = "Asia/Dubai"
    working_hours: WorkingHours = WorkingHours()

    class Config:
        use_enum_values = True

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    nationality: Optional[str] = None
    languages_spoken: Optional[List[str]] = None
    license_number: Optional[str] = None
    license_expiry_date: Optional[date] = None
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    role: Optional[AgentRole] = None
    permissions: Optional[List[str]] = None
    assigned_territories: Optional[List[str]] = None
    property_specializations: Optional[List[str]] = None
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=10)
    monthly_target: Optional[Decimal] = Field(None, ge=0)
    annual_target: Optional[Decimal] = Field(None, ge=0)
    whatsapp_number: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    preferred_contact_method: Optional[ContactMethod] = None
    working_hours: Optional[WorkingHours] = None
    status: Optional[AgentStatus] = None

class AgentResponse(BaseModel):
    id: UUID
    agency_id: UUID
    user_id: UUID
    name: str
    email: str
    phone: str
    nationality: Optional[str]
    languages_spoken: List[str]
    license_number: Optional[str]
    license_expiry_date: Optional[date]
    years_experience: int
    role: AgentRole
    permissions: List[str]
    assigned_territories: List[str]
    property_specializations: List[str]
    commission_rate: Decimal
    monthly_target: Decimal
    annual_target: Decimal
    total_deals_closed: int
    total_commission_earned: Decimal
    whatsapp_number: Optional[str]
    preferred_contact_method: ContactMethod
    timezone: str
    working_hours: Dict[str, Any]
    status: AgentStatus
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentPerformance(BaseModel):
    agent_id: UUID
    agent_name: str
    deals_this_month: int
    deals_this_quarter: int
    commission_this_month: Decimal
    commission_this_quarter: Decimal
    target_achievement_percentage: Decimal
    average_deal_size: Decimal
    conversion_rate: Decimal
    properties_managed: int
    active_applications: int
    scheduled_viewings: int

# =====================================================================
# DASHBOARD MODELS
# =====================================================================

class AgencyDashboardStats(BaseModel):
    total_properties: int
    total_active_leases: int
    pending_applications: int
    monthly_commissions: Decimal
    total_agents: int
    applications_this_month: int
    application_conversion_rate: Decimal
    average_processing_time: float  # in days
    monthly_target_progress: Decimal
    quarterly_revenue: Decimal

class AgentDashboardStats(BaseModel):
    properties_assigned: int
    active_applications: int
    scheduled_viewings: int
    completed_deals_this_month: int
    commission_this_month: Decimal
    target_progress: Decimal
    viewings_this_week: int
    pending_document_reviews: int
    contracts_awaiting_signature: int
```

### **Task 1.4: Create Application Management Models**

#### **File**: `backend/app/models/application_schemas.py`

```python
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

# =====================================================================
# TENANT APPLICATION MODELS
# =====================================================================

class ApplicationStatus(str, Enum):
    submitted = "submitted"
    documents_pending = "documents_pending"
    under_review = "under_review"
    credit_check = "credit_check"
    approved = "approved"
    rejected = "rejected"
    withdrawn = "withdrawn"

class EmploymentType(str, Enum):
    permanent = "permanent"
    contract = "contract"
    freelancer = "freelancer"
    self_employed = "self_employed"

class FurnishedPreference(str, Enum):
    furnished = "furnished"
    unfurnished = "unfurnished"
    semi_furnished = "semi_furnished"
    no_preference = "no_preference"

class CreditCheckStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    not_required = "not_required"

class BackgroundCheckStatus(str, Enum):
    pending = "pending"
    clear = "clear"
    flagged = "flagged"
    not_required = "not_required"

class TenantApplicationCreate(BaseModel):
    property_id: UUID
    agent_id: Optional[UUID] = None
    
    # Primary Applicant
    primary_applicant_name: str = Field(..., min_length=2, max_length=255)
    primary_applicant_email: EmailStr
    primary_applicant_phone: str = Field(..., regex="^\\+971[0-9]{8,9}$")
    primary_applicant_nationality: Optional[str] = None
    primary_applicant_passport: Optional[str] = None
    primary_applicant_emirates_id: Optional[str] = Field(None, regex="^[0-9]{3}-[0-9]{4}-[0-9]{7}-[0-9]{1}$")
    
    # Employment Information
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    monthly_income: Optional[Decimal] = Field(None, ge=0)
    employment_type: Optional[EmploymentType] = None
    work_permit_expiry: Optional[date] = None
    
    # Lease Preferences
    desired_move_in_date: date
    lease_duration_months: int = Field(..., ge=6, le=60)
    maximum_budget: Decimal = Field(..., ge=0)
    furnished_preference: FurnishedPreference = FurnishedPreference.no_preference
    
    # Current Housing
    current_address: Optional[str] = None
    current_monthly_rent: Optional[Decimal] = Field(None, ge=0)
    reason_for_moving: Optional[str] = None
    notice_period_days: Optional[int] = Field(None, ge=0, le=365)
    
    # Family Information
    family_size: int = Field(1, ge=1, le=20)
    children_count: int = Field(0, ge=0, le=10)
    pet_ownership: bool = False
    pet_details: Optional[str] = None
    
    # References
    previous_landlord_name: Optional[str] = None
    previous_landlord_phone: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    employer_reference_name: Optional[str] = None
    employer_reference_phone: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")

    @validator('desired_move_in_date')
    def validate_move_in_date(cls, v):
        if v < date.today():
            raise ValueError('Move-in date cannot be in the past')
        return v

    @validator('maximum_budget')
    def validate_budget_with_income(cls, v, values):
        if 'monthly_income' in values and values['monthly_income']:
            if v > values['monthly_income'] * Decimal('0.4'):
                raise ValueError('Maximum budget should not exceed 40% of monthly income')
        return v

    class Config:
        use_enum_values = True

class TenantApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    agent_id: Optional[UUID] = None
    review_notes: Optional[List[str]] = None
    rejection_reason: Optional[str] = None
    approval_conditions: Optional[List[str]] = None
    credit_check_status: Optional[CreditCheckStatus] = None
    background_check_status: Optional[BackgroundCheckStatus] = None
    identity_verified: Optional[bool] = None
    income_verified: Optional[bool] = None
    reference_verified: Optional[bool] = None

class TenantApplicationResponse(BaseModel):
    id: UUID
    property_id: UUID
    agent_id: Optional[UUID]
    application_number: str
    status: ApplicationStatus
    
    # Primary Applicant
    primary_applicant_name: str
    primary_applicant_email: str
    primary_applicant_phone: str
    primary_applicant_nationality: Optional[str]
    primary_applicant_passport: Optional[str]
    primary_applicant_emirates_id: Optional[str]
    
    # Employment Information
    employer_name: Optional[str]
    job_title: Optional[str]
    monthly_income: Optional[Decimal]
    employment_type: Optional[EmploymentType]
    work_permit_expiry: Optional[date]
    
    # Lease Preferences
    desired_move_in_date: date
    lease_duration_months: int
    maximum_budget: Decimal
    furnished_preference: FurnishedPreference
    
    # Current Housing
    current_address: Optional[str]
    current_monthly_rent: Optional[Decimal]
    reason_for_moving: Optional[str]
    notice_period_days: Optional[int]
    
    # Family Information
    family_size: int
    children_count: int
    pet_ownership: bool
    pet_details: Optional[str]
    
    # References
    previous_landlord_name: Optional[str]
    previous_landlord_phone: Optional[str]
    employer_reference_name: Optional[str]
    employer_reference_phone: Optional[str]
    
    # Financial Information
    bank_statements_provided: bool
    salary_certificate_provided: bool
    credit_score: Optional[int]
    credit_check_date: Optional[date]
    credit_check_status: CreditCheckStatus
    
    # Application Processing
    review_notes: List[str]
    rejection_reason: Optional[str]
    approval_conditions: List[str]
    
    # Security & Compliance
    identity_verified: bool
    income_verified: bool
    reference_verified: bool
    background_check_status: BackgroundCheckStatus
    
    # Timestamps
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# DOCUMENT MODELS
# =====================================================================

class DocumentType(str, Enum):
    passport = "passport"
    emirates_id = "emirates_id"
    visa_page = "visa_page"
    salary_certificate = "salary_certificate"
    bank_statement = "bank_statement"
    employment_contract = "employment_contract"
    noc_letter = "noc_letter"
    previous_lease_agreement = "previous_lease_agreement"
    utility_bill = "utility_bill"
    other = "other"

class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    expired = "expired"

class UploadedBy(str, Enum):
    applicant = "applicant"
    agent = "agent"
    system = "system"

class ApplicationDocumentCreate(BaseModel):
    application_id: UUID
    document_type: DocumentType
    document_name: str = Field(..., min_length=1, max_length=255)
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    expiry_date: Optional[date] = None
    issued_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    uploaded_by: UploadedBy = UploadedBy.applicant

    class Config:
        use_enum_values = True

class ApplicationDocumentUpdate(BaseModel):
    verification_status: Optional[VerificationStatus] = None
    verification_notes: Optional[str] = None
    verified_by_agent_id: Optional[UUID] = None

class ApplicationDocumentResponse(BaseModel):
    id: UUID
    application_id: UUID
    document_type: DocumentType
    document_name: str
    file_url: str
    file_size: Optional[int]
    mime_type: Optional[str]
    verification_status: VerificationStatus
    verified_by_agent_id: Optional[UUID]
    verification_notes: Optional[str]
    verified_at: Optional[datetime]
    expiry_date: Optional[date]
    issued_date: Optional[date]
    issuing_authority: Optional[str]
    uploaded_by: UploadedBy
    upload_ip_address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# APPLICATION PIPELINE MODELS
# =====================================================================

class ApplicationPipelineStats(BaseModel):
    total_applications: int
    submitted: int
    documents_pending: int
    under_review: int
    credit_check: int
    approved: int
    rejected: int
    withdrawn: int
    conversion_rate: Decimal
    average_processing_time: float  # in days

class ApplicationsFilter(BaseModel):
    status: Optional[ApplicationStatus] = None
    agent_id: Optional[UUID] = None
    property_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search_term: Optional[str] = None  # Search in applicant name, email, phone
    minimum_budget: Optional[Decimal] = None
    maximum_budget: Optional[Decimal] = None
    verification_status: Optional[bool] = None  # All documents verified

class BulkApplicationUpdate(BaseModel):
    application_ids: List[UUID]
    status: Optional[ApplicationStatus] = None
    agent_id: Optional[UUID] = None
    review_notes: Optional[str] = None
```

I'll continue with the implementation guide, but as you can see, this is becoming quite extensive. 

**The answer to your question**: No, the original document I created would NOT be sufficient for Cursor to work with effectively. It was more of a **business analysis** rather than a **development guide**.

This new implementation guide I'm creating will provide:

1. **Exact SQL migration files** with complete schema
2. **Complete Pydantic models** with all validations
3. **Step-by-step file creation** instructions
4. **Specific code snippets** to implement
5. **API endpoint implementations** with full code
6. **Frontend component transformations** with exact changes needed

Would you like me to continue with the remaining parts of the implementation guide (API routes, frontend components, etc.) or would you prefer to focus on specific sections first?
