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
# LEASE AGREEMENT MODELS
# =====================================================================

class ContractType(str, Enum):
    residential = "residential"
    commercial = "commercial"
    mixed_use = "mixed_use"

class PaymentSchedule(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    semi_annual = "semi_annual"
    annual = "annual"

class PaymentMethod(str, Enum):
    bank_transfer = "bank_transfer"
    cheque = "cheque"
    cash = "cash"
    online = "online"

class FurnishedStatus(str, Enum):
    furnished = "furnished"
    semi_furnished = "semi_furnished"
    unfurnished = "unfurnished"

class SignatureStatus(str, Enum):
    pending = "pending"
    signed = "signed"
    declined = "declined"

class LeaseStatus(str, Enum):
    draft = "draft"
    sent_for_signature = "sent_for_signature"
    partially_signed = "partially_signed"
    fully_executed = "fully_executed"
    active = "active"
    expired = "expired"
    terminated = "terminated"
    cancelled = "cancelled"

class CommissionStatus(str, Enum):
    pending = "pending"
    invoiced = "invoiced"
    paid = "paid"
    disputed = "disputed"

class LeaseAgreementCreate(BaseModel):
    property_id: UUID
    tenant_application_id: Optional[UUID] = None
    agent_id: UUID
    agency_id: UUID
    contract_type: ContractType = ContractType.residential
    
    # Parties Information
    landlord_name: str = Field(..., min_length=2, max_length=255)
    landlord_email: Optional[EmailStr] = None
    landlord_phone: Optional[str] = Field(None, regex="^\\+971[0-9]{8,9}$")
    landlord_emirates_id: Optional[str] = None
    
    tenant_name: str = Field(..., min_length=2, max_length=255)
    tenant_email: EmailStr
    tenant_phone: str = Field(..., regex="^\\+971[0-9]{8,9}$")
    tenant_emirates_id: Optional[str] = None
    tenant_passport: Optional[str] = None
    
    # Lease Terms
    lease_start_date: date
    lease_end_date: date
    
    # Financial Terms
    annual_rent: Decimal = Field(..., gt=0)
    security_deposit: Decimal = Field(..., ge=0)
    broker_commission: Decimal = Field(..., ge=0)
    
    # Payment Terms
    payment_schedule: PaymentSchedule = PaymentSchedule.annual
    payment_method: PaymentMethod = PaymentMethod.bank_transfer
    payment_due_day: int = Field(1, ge=1, le=28)
    late_payment_penalty_percentage: Decimal = Field(Decimal("5.00"), ge=0, le=50)
    
    # Additional Charges
    service_charges_annual: Decimal = Field(Decimal("0"), ge=0)
    dewa_included: bool = False
    internet_included: bool = False
    maintenance_included: bool = True
    parking_included: bool = False
    additional_charges: Optional[Dict[str, Any]] = None
    
    # Contract Terms
    auto_renewal: bool = False
    renewal_notice_period_days: int = Field(90, ge=30, le=365)
    early_termination_allowed: bool = False
    early_termination_penalty: Optional[Decimal] = Field(None, ge=0)
    
    # Property Condition
    furnished_status: Optional[FurnishedStatus] = None
    inventory_list_url: Optional[str] = None
    property_condition_report_url: Optional[str] = None
    
    # Legal Compliance
    rera_permit_number: Optional[str] = None
    ejari_registration_number: Optional[str] = None
    municipality_approval: bool = False
    
    # Document Management
    contract_template_id: Optional[UUID] = None
    
    # Notes & Special Conditions
    special_conditions: List[str] = []
    agent_notes: Optional[str] = None
    internal_notes: Optional[str] = None

    @validator('lease_end_date')
    def validate_lease_dates(cls, v, values):
        if 'lease_start_date' in values and v <= values['lease_start_date']:
            raise ValueError('Lease end date must be after start date')
        return v

    @validator('lease_start_date')
    def validate_future_start_date(cls, v):
        if v < date.today():
            raise ValueError('Lease start date cannot be in the past')
        return v

    class Config:
        use_enum_values = True

class LeaseAgreementUpdate(BaseModel):
    status: Optional[LeaseStatus] = None
    landlord_signature_status: Optional[SignatureStatus] = None
    tenant_signature_status: Optional[SignatureStatus] = None
    witness_signature_status: Optional[SignatureStatus] = None
    docusign_envelope_id: Optional[str] = None
    signed_contract_url: Optional[str] = None
    execution_date: Optional[date] = None
    registration_date: Optional[date] = None
    commission_status: Optional[CommissionStatus] = None
    commission_invoice_number: Optional[str] = None
    commission_paid_date: Optional[date] = None
    commission_payment_reference: Optional[str] = None
    special_conditions: Optional[List[str]] = None
    agent_notes: Optional[str] = None
    internal_notes: Optional[str] = None

class LeaseAgreementResponse(BaseModel):
    id: UUID
    property_id: UUID
    tenant_application_id: Optional[UUID]
    agent_id: UUID
    agency_id: UUID
    lease_number: str
    contract_type: ContractType
    
    # Parties Information
    landlord_name: str
    landlord_email: Optional[str]
    landlord_phone: Optional[str]
    landlord_emirates_id: Optional[str]
    
    tenant_name: str
    tenant_email: str
    tenant_phone: str
    tenant_emirates_id: Optional[str]
    tenant_passport: Optional[str]
    
    # Lease Terms
    lease_start_date: date
    lease_end_date: date
    lease_duration_months: int
    
    # Financial Terms
    annual_rent: Decimal
    monthly_rent: Decimal
    security_deposit: Decimal
    broker_commission: Decimal
    commission_percentage: Decimal
    
    # Payment Terms
    payment_schedule: PaymentSchedule
    payment_method: PaymentMethod
    payment_due_day: int
    late_payment_penalty_percentage: Decimal
    
    # Additional Charges
    service_charges_annual: Decimal
    dewa_included: bool
    internet_included: bool
    maintenance_included: bool
    parking_included: bool
    additional_charges: Optional[Dict[str, Any]]
    
    # Contract Terms
    auto_renewal: bool
    renewal_notice_period_days: int
    early_termination_allowed: bool
    early_termination_penalty: Optional[Decimal]
    
    # Property Condition
    furnished_status: Optional[FurnishedStatus]
    inventory_list_url: Optional[str]
    property_condition_report_url: Optional[str]
    
    # Legal Compliance
    rera_permit_number: Optional[str]
    ejari_registration_number: Optional[str]
    municipality_approval: bool
    
    # Document Management
    contract_template_id: Optional[UUID]
    docusign_envelope_id: Optional[str]
    signed_contract_url: Optional[str]
    
    # Signature Status
    landlord_signature_status: SignatureStatus
    landlord_signed_at: Optional[datetime]
    landlord_ip_address: Optional[str]
    
    tenant_signature_status: SignatureStatus
    tenant_signed_at: Optional[datetime]
    tenant_ip_address: Optional[str]
    
    witness_required: bool
    witness_signature_status: SignatureStatus
    witness_name: Optional[str]
    witness_emirates_id: Optional[str]
    witness_signed_at: Optional[datetime]
    
    # Agreement Status
    status: LeaseStatus
    execution_date: Optional[date]
    registration_date: Optional[date]
    
    # Renewal Information
    renewal_eligibility: bool
    renewal_rent_increase_percentage: Optional[Decimal]
    renewal_terms_notes: Optional[str]
    
    # Termination Information
    termination_date: Optional[date]
    termination_reason: Optional[str]
    termination_notice_served_date: Optional[date]
    termination_penalty_paid: Optional[Decimal]
    
    # Commission Tracking
    commission_status: CommissionStatus
    commission_invoice_number: Optional[str]
    commission_paid_date: Optional[date]
    commission_payment_reference: Optional[str]
    
    # Notes & Special Conditions
    special_conditions: List[str]
    agent_notes: Optional[str]
    internal_notes: Optional[str]
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =====================================================================
# CONTRACT TEMPLATE MODELS
# =====================================================================

class TemplateStatus(str, Enum):
    draft = "draft"
    active = "active"
    deprecated = "deprecated"
    archived = "archived"

class ContractLanguage(str, Enum):
    en = "en"
    ar = "ar"
    both = "both"

class ContractTemplateCreate(BaseModel):
    agency_id: UUID
    template_name: str = Field(..., min_length=3, max_length=255)
    template_version: str = Field("1.0", min_length=1, max_length=20)
    description: Optional[str] = None
    property_type: Optional[ContractType] = None
    contract_language: ContractLanguage = ContractLanguage.en
    emirates: Optional[str] = None
    template_content: Dict[str, Any]
    docusign_template_id: Optional[str] = None
    rera_compliant: bool = False
    dubai_land_department_approved: bool = False
    municipality_approved: bool = False
    legal_review_date: Optional[date] = None
    legal_reviewer_name: Optional[str] = None
    is_default: bool = False
    parent_template_id: Optional[UUID] = None
    changelog: List[str] = []

    class Config:
        use_enum_values = True

class ContractTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    template_content: Optional[Dict[str, Any]] = None
    docusign_template_id: Optional[str] = None
    status: Optional[TemplateStatus] = None
    rera_compliant: Optional[bool] = None
    dubai_land_department_approved: Optional[bool] = None
    municipality_approved: Optional[bool] = None
    legal_review_date: Optional[date] = None
    legal_reviewer_name: Optional[str] = None
    is_default: Optional[bool] = None
    changelog: Optional[List[str]] = None

class ContractTemplateResponse(BaseModel):
    id: UUID
    agency_id: UUID
    template_name: str
    template_version: str
    description: Optional[str]
    property_type: Optional[ContractType]
    contract_language: ContractLanguage
    emirates: Optional[str]
    template_content: Dict[str, Any]
    docusign_template_id: Optional[str]
    rera_compliant: bool
    dubai_land_department_approved: bool
    municipality_approved: bool
    legal_review_date: Optional[date]
    legal_reviewer_name: Optional[str]
    usage_count: int
    success_rate: Decimal
    status: TemplateStatus
    is_default: bool
    parent_template_id: Optional[UUID]
    changelog: List[str]
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

# =====================================================================
# NOTIFICATION MODELS
# =====================================================================

class NotificationType(str, Enum):
    application_submitted = "application_submitted"
    document_uploaded = "document_uploaded"
    viewing_scheduled = "viewing_scheduled"
    viewing_reminder = "viewing_reminder"
    application_approved = "application_approved"
    application_rejected = "application_rejected"
    lease_ready = "lease_ready"
    lease_signed = "lease_signed"
    payment_due = "payment_due"
    lease_expiring = "lease_expiring"

class NotificationCreate(BaseModel):
    recipient_id: UUID
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=1000)
    data: Optional[Dict[str, Any]] = None
    send_email: bool = True
    send_sms: bool = False
    send_whatsapp: bool = False

    class Config:
        use_enum_values = True

class NotificationResponse(BaseModel):
    id: UUID
    recipient_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    read: bool
    sent_email: bool
    sent_sms: bool
    sent_whatsapp: bool
    created_at: datetime

    class Config:
        from_attributes = True
