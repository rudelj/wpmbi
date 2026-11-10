from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class WorkItemSummary(BaseModel):
    wki_id: str
    doc_number: str
    doc_type: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None
    technical_body: Optional[str] = None
    tb_id: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    status: Optional[str] = None
    status_date: Optional[str] = None
    pdf_url: Optional[str] = None
    word_url: Optional[str] = None
    detail_url: Optional[str] = None
    is_finalized: bool = False
    is_stopped: bool = False
    is_favorite: bool = False

class MilestoneStep(BaseModel):
    sched_id: Optional[int] = None
    wki_id: str
    mls_code: str
    mls_name: str
    sched_position: int
    duration_days: int = 30
    original_date: Optional[str] = None
    review_date: Optional[str] = None
    target_date: Optional[str] = None
    achieved_date: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, ACHIEVED

class WorkItemDetail(BaseModel):
    wki_id: str
    doc_number: str
    doc_type: Optional[str] = "EN"
    deliv_class: Optional[str] = "Standard"
    reference: Optional[str] = None
    technical_body: Optional[str] = None
    tb_id: Optional[str] = None
    current_status: Optional[str] = None
    status_date: Optional[str] = None
    latest_version: Optional[str] = "v1.1.1"
    cover_date: Optional[str] = None
    creation_date: Optional[str] = None
    stop_date: Optional[str] = None
    is_stopped: bool = False
    standstill: Optional[str] = "NO"
    standstill_date: Optional[str] = None
    rapporteur_name: Optional[str] = None
    rapporteur_email: Optional[str] = None
    technical_officer_name: Optional[str] = None
    technical_officer_email: Optional[str] = None
    harmonised_standard: Optional[str] = "No"
    title_part1: Optional[str] = None
    title_part2: Optional[str] = None
    title_part3: Optional[str] = None
    title: str
    scope_remarks: Optional[str] = None
    lead_body: Optional[str] = None
    parent_wki_id: Optional[str] = None
    parent_reference: Optional[str] = None
    pdf_url: Optional[str] = None
    word_url: Optional[str] = None
    detail_url: Optional[str] = None
    is_favorite: bool = False
    schedule: List[MilestoneStep] = Field(default_factory=list)
    frequencies: List[Dict[str, Any]] = Field(default_factory=list)
    mandates: List[Dict[str, Any]] = Field(default_factory=list)
    remarks: List[Dict[str, Any]] = Field(default_factory=list)
    history_events: List[Dict[str, str]] = Field(default_factory=list)

class WorkItemCreate(BaseModel):
    doc_type: str = Field(..., description="ETSI Deliverable Type: EN, TS, TR, ES, EG, SR, GS")
    deliv_class: str = Field(default="Standard")
    doc_number: str = Field(..., description="Doc number e.g. 303645")
    part_nb: Optional[str] = None
    subpart_nb: Optional[str] = None
    edition_nb: Optional[str] = "1"
    version: str = Field(default="v1.1.1")
    technical_body: str = Field(..., description="Technical body code e.g. CYBER, ERM")
    title_part1: str = Field(..., description="Mandatory Part 1 of the title")
    title_part2: Optional[str] = None
    title_part3: Optional[str] = None
    rapporteur_name: str
    rapporteur_email: Optional[str] = None
    support_officer_name: str
    support_officer_email: Optional[str] = None
    standstill_status: str = "NO"
    creation_date: Optional[str] = None
    target_date: Optional[str] = None
    scope: Optional[str] = None
    harmonized_flag: bool = False
    lead_body: Optional[str] = None
    ec_mandate: Optional[str] = None
    ec_directive: Optional[str] = None

class WorkItemUpdate(BaseModel):
    title_part1: Optional[str] = None
    title_part2: Optional[str] = None
    title_part3: Optional[str] = None
    status: Optional[str] = None
    status_date: Optional[str] = None
    version: Optional[str] = None
    rapporteur_name: Optional[str] = None
    rapporteur_email: Optional[str] = None
    support_officer_name: Optional[str] = None
    support_officer_email: Optional[str] = None
    standstill_status: Optional[str] = None
    scope: Optional[str] = None
    harmonized_flag: Optional[bool] = None
    is_stopped: Optional[bool] = None
    stop_date: Optional[str] = None

class CloneWorkItemRequest(BaseModel):
    clone_type: Literal["revision", "split", "transfer", "duplicate"] = Field(
        ..., description="Type of duplication: revision stops parent, split, transfer new TB, or standard duplicate"
    )
    schedule_option: Literal["default", "original", "none"] = Field(
        default="default", description="Schedule handling for clone"
    )
    retain_comments: bool = False
    retain_stf_mandates: bool = True
    new_tb: Optional[str] = None
    new_doc_number: Optional[str] = None
    new_title_part1: Optional[str] = None
    new_serial_number: Optional[str] = None

class NextNumberRequest(BaseModel):
    doc_type: str = Field(..., description="Deliverable type e.g. EN, TS, TR, GS, ETS")
    technical_body: Optional[str] = Field(None, description="Technical Body code e.g. CYBER, ISG ENI")
    suggested_start: Optional[int] = None

class NextNumberResponse(BaseModel):
    doc_type: str
    technical_body: Optional[str] = None
    assigned_number: str
    formatted_reference: str
    rule_applied: str
    candidate_numbers: List[str]

class PerfectPlanRequest(BaseModel):
    doc_type: str
    start_date: str  # YYYY-MM-DD
    target_publication_date: Optional[str] = None

class RemarkCreate(BaseModel):
    remark_type: str = "GENERAL"
    remark_text: str
    author: str = "Secretariat Officer"

class FrequencyCreate(BaseModel):
    low_freq: float
    high_freq: float
    unit: str = "MHz"
    service_app: str

class MandateCreate(BaseModel):
    mandate_code: str
    directive_ref: Optional[str] = "RED 2014/53/EU"
    descript: Optional[str] = None

class SearchQuery(BaseModel):
    q_text: Optional[str] = None
    doc_type: Optional[str] = None
    doc_number: Optional[str] = None
    technical_body: Optional[str] = None
    milestone: Optional[str] = None
    sort_by: Optional[str] = "HIGHVERSION"
    include_sub_tb: bool = True
    all_versions: bool = False
    include_moved_on: bool = False
    display_limit: int = 50
    offset: int = 0

class SearchResponse(BaseModel):
    total_found: int
    offset: int
    limit: int
    items: List[WorkItemSummary]
    query_echo: Dict[str, Any]

class KPIStats(BaseModel):
    total_active: int
    total_published: int
    total_in_approval: int
    total_stopped: int
    total_tbs: int
    total_records: int
