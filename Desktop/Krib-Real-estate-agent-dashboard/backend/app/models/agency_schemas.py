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
    establishment_year: Optional[int] = Field(None, ge=1970, le=2025)
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
    user_id: Optional[UUID]
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

# =====================================================================
# VIEWING MANAGEMENT MODELS
# =====================================================================

class ViewingType(str, Enum):
    in_person = "in_person"
    virtual = "virtual"
    self_guided = "self_guided"

class ViewingStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"

class ConfirmationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"

class InterestLevel(str, Enum):
    very_interested = "very_interested"
    interested = "interested"
    neutral = "neutral"
    not_interested = "not_interested"

class ViewingCreate(BaseModel):
    property_id: UUID
    agent_id: Optional[UUID] = None
    application_id: Optional[UUID] = None
    
    # Viewing Details
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = Field(30, ge=15, le=180)
    
    # Applicant Information
    applicant_name: str = Field(..., min_length=2, max_length=255)
    applicant_email: EmailStr
    applicant_phone: str = Field(..., regex="^\\+971[0-9]{8,9}$")
    number_of_attendees: int = Field(1, ge=1, le=10)
    
    # Viewing Type
    viewing_type: ViewingType = ViewingType.in_person
    meeting_platform: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_password: Optional[str] = None

    @validator('scheduled_date')
    def validate_future_date(cls, v):
        if v < date.today():
            raise ValueError('Viewing date cannot be in the past')
        return v

    class Config:
        use_enum_values = True

class ViewingUpdate(BaseModel):
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    viewing_type: Optional[ViewingType] = None
    status: Optional[ViewingStatus] = None
    confirmation_status: Optional[ConfirmationStatus] = None
    agent_pre_notes: Optional[str] = None
    agent_post_notes: Optional[str] = None
    applicant_feedback: Optional[str] = None
    property_condition_notes: Optional[str] = None
    interest_level: Optional[InterestLevel] = None
    follow_up_actions: Optional[List[str]] = None
    next_steps: Optional[str] = None
    application_submitted: Optional[bool] = None
    meeting_platform: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_password: Optional[str] = None

class ViewingResponse(BaseModel):
    id: UUID
    property_id: UUID
    agent_id: Optional[UUID]
    application_id: Optional[UUID]
    viewing_number: str
    
    # Viewing Details
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    
    # Applicant Information
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    number_of_attendees: int
    
    # Viewing Type & Method
    viewing_type: ViewingType
    meeting_platform: Optional[str]
    meeting_link: Optional[str]
    meeting_password: Optional[str]
    
    # Status Tracking
    status: ViewingStatus
    confirmation_status: ConfirmationStatus
    
    # Communication
    confirmation_sent_at: Optional[datetime]
    reminder_sent_at: Optional[datetime]
    follow_up_required: bool
    
    # Notes & Feedback
    agent_pre_notes: Optional[str]
    agent_post_notes: Optional[str]
    applicant_feedback: Optional[str]
    property_condition_notes: Optional[str]
    interest_level: Optional[InterestLevel]
    
    # Follow-up Actions
    follow_up_actions: List[str]
    next_steps: Optional[str]
    application_submitted: bool
    
    # Integration
    google_calendar_event_id: Optional[str]
    whatsapp_group_id: Optional[str]
    
    # Cancellation Information
    cancelled_by: Optional[str]
    cancellation_reason: Optional[str]
    cancelled_at: Optional[datetime]
    
    # Rescheduling
    original_viewing_id: Optional[UUID]
    rescheduled_from_date: Optional[date]
    rescheduled_from_time: Optional[time]
    reschedule_reason: Optional[str]
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# AGENT AVAILABILITY MODELS
# =====================================================================

class SlotType(str, Enum):
    regular = "regular"
    extended = "extended"
    emergency = "emergency"
    blocked = "blocked"

class RecurringPattern(str, Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

class AvailabilityCreate(BaseModel):
    agent_id: UUID
    date: date
    start_time: time
    end_time: time
    max_viewings: int = Field(3, ge=1, le=10)
    slot_type: SlotType = SlotType.regular
    recurring_pattern: RecurringPattern = RecurringPattern.none
    preferred_areas: List[str] = []
    travel_buffer_minutes: int = Field(30, ge=0, le=120)
    notes: Optional[str] = None

    @validator('end_time')
    def validate_time_order(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('date')
    def validate_future_date(cls, v):
        if v < date.today():
            raise ValueError('Availability date cannot be in the past')
        return v

    class Config:
        use_enum_values = True

class AvailabilityUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None
    max_viewings: Optional[int] = Field(None, ge=1, le=10)
    slot_type: Optional[SlotType] = None
    preferred_areas: Optional[List[str]] = None
    travel_buffer_minutes: Optional[int] = Field(None, ge=0, le=120)
    notes: Optional[str] = None
    blocked_reason: Optional[str] = None

class AvailabilityResponse(BaseModel):
    id: UUID
    agent_id: UUID
    date: date
    start_time: time
    end_time: time
    is_available: bool
    max_viewings: int
    current_bookings: int
    slot_type: SlotType
    recurring_pattern: RecurringPattern
    preferred_areas: List[str]
    travel_buffer_minutes: int
    notes: Optional[str]
    blocked_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# BULK OPERATIONS
# =====================================================================

class BulkAgentUpdate(BaseModel):
    agent_ids: List[UUID]
    role: Optional[AgentRole] = None
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=10)
    assigned_territories: Optional[List[str]] = None
    status: Optional[AgentStatus] = None

class BulkAvailabilityCreate(BaseModel):
    agent_id: UUID
    start_date: date
    end_date: date
    days_of_week: List[int] = Field(..., min_items=1, max_items=7)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    max_viewings: int = Field(3, ge=1, le=10)
    slot_type: SlotType = SlotType.regular
    preferred_areas: List[str] = []
    travel_buffer_minutes: int = Field(30, ge=0, le=120)

    @validator('days_of_week')
    def validate_days(cls, v):
        if not all(0 <= day <= 6 for day in v):
            raise ValueError('Days of week must be between 0 (Monday) and 6 (Sunday)')
        return list(set(v))  # Remove duplicates

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    class Config:
        use_enum_values = True
