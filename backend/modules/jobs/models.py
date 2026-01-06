"""
Job Aggregator - Pydantic Models
Schemas for Job Search System
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class Modality(str, Enum):
    """Work modality"""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ContractType(str, Enum):
    """Contract type"""
    CLT = "CLT"
    PJ = "PJ"
    INTERN = "Intern"
    TEMPORARY = "Temporary"
    FREELANCE = "Freelance"


class Seniority(str, Enum):
    """Job seniority level"""
    INTERN = "intern"
    JUNIOR = "junior"
    PLENO = "pleno"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"


class ExtractionMethod(str, Enum):
    """How job data was extracted"""
    SCRAPE = "scrape"
    HEADLESS = "headless"
    OCR = "ocr"
    MANUAL = "manual"
    API = "api"


class JobStatus(str, Enum):
    """Job posting status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"
    REMOVED = "removed"


# Location Model
class Location(BaseModel):
    """Job location"""
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "Brazil"
    remote: bool = False


# Salary Models
class SalaryExplicit(BaseModel):
    """Explicit salary from job posting"""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "BRL"
    period: str = "monthly"  # monthly, yearly
    suspect: bool = False  # Flag if salary seems unusual


class SalaryEstimate(BaseModel):
    """Estimated salary"""
    status: str  # ok, unavailable, insufficient_data
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "BRL"
    period: str = "monthly"
    sourceOrder: List[str] = []  # Order of sources tried
    confidence: float = 0.0  # 0-1
    notes: List[str] = []


# Ranking
class RankingBreakdown(BaseModel):
    """Breakdown of ranking score"""
    cvMatch: float = 0.0  # 0-100
    salary: float = 0.0  # 0-100
    stack: float = 0.0  # 0-100


# Job Posting
class JobPosting(BaseModel):
    """Main job posting model"""
    # Identifiers
    url: str  # Changed from HttpUrl for MongoDB
    sourceId: Optional[str] = None
    connectorId: Optional[str] = None
    platformJobId: Optional[str] = None
    
    # Core fields
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[Location] = None
    modality: Optional[Modality] = None
    contractType: Optional[ContractType] = None
    workHours: Optional[str] = None
    language: str = "PT-BR"
    
    # Dates
    postedAt: Optional[datetime] = None
    expiresAt: Optional[datetime] = None
    lastCrawledAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Content
    description: Optional[str] = None
    mustHave: List[str] = []
    niceToHave: List[str] = []
    techKeywords: List[str] = []
    seniority: Optional[Seniority] = None
    
    # Salary
    salaryExplicit: Optional[SalaryExplicit] = None
    salaryEstimate: Optional[SalaryEstimate] = None
    benefits: List[str] = []
    
    # Ranking
    rankingScore: Optional[float] = None  # 0-100
    rankingBreakdown: Optional[RankingBreakdown] = None
    
    # Extraction metadata
    rawHtml: Optional[str] = None
    rawText: Optional[str] = None
    extractionConfidence: Dict[str, float] = {}  # field -> confidence
    extractionMethod: Optional[ExtractionMethod] = None
    isPartial: bool = False
    
    # Tags & status
    tags: List[str] = []
    status: JobStatus = JobStatus.ACTIVE
    
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# Job Source
class JobSource(BaseModel):
    """Job board/platform source"""
    name: str  # LinkedIn, Gupy, Indeed
    type: str  # aggregator, board, career_page
    baseUrl: Optional[HttpUrl] = None
    isPremium: bool = False
    requiresAuth: bool = False
    status: str = "active"  # active, deprecated
    metadata: Dict[str, Any] = {}
    createdAt: datetime = Field(default_factory=datetime.utcnow)


# Connector
class SelectorConfig(BaseModel):
    """Field selector configuration"""
    css: Optional[str] = None
    xpath: Optional[str] = None
    regex: Optional[str] = None
    priority: str = "css"  # css | xpath | regex


class FewShotExample(BaseModel):
    """Training example for connector"""
    url: HttpUrl
    expectedOutput: Dict[str, Any]


class DomainRules(BaseModel):
    """Domain-specific extraction rules"""
    useHeadless: bool = False
    waitForSelector: Optional[str] = None
    customHeaders: Dict[str, str] = {}
    cookieRequired: bool = False


class ConnectorPerformance(BaseModel):
    """Connector performance metrics"""
    successRate: float = 0.0
    avgExtractTime: float = 0.0
    lastTestedAt: Optional[datetime] = None


class Connector(BaseModel):
    """Site-specific scraping connector"""
    domain: str
    sourceId: Optional[str] = None
    selectors: Dict[str, SelectorConfig] = {}
    fewShotExamples: List[FewShotExample] = []
    domainRules: Optional[DomainRules] = None
    performance: Optional[ConnectorPerformance] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    createdBy: str = "system"  # system | user
    isActive: bool = True


# Audit Log
class AuditLog(BaseModel):
    """Audit trail for job operations"""
    entityType: str  # job_posting, connector, crawl_run
    entityId: str
    level: str  # info, warning, error
    message: str
    payload: Dict[str, Any] = {}
    createdAt: datetime = Field(default_factory=datetime.utcnow)


# ==================== SEARCH PROFILES ====================

class SearchFilters(BaseModel):
    """Search filters for job profiles"""
    title: Optional[str] = None
    seniority: Optional[Seniority] = None
    stack: List[str] = []
    modality: Optional[Modality] = None
    location: Optional[Location] = None
    minSalary: Optional[float] = None
    language: str = "PT-BR"


class ScheduleConfig(BaseModel):
    """Schedule configuration for automated searches"""
    type: str = "manual"  # manual, daily, weekly, monthly
    time: Optional[str] = None  # HH:MM
    daysOfWeek: List[int] = []  # [0-6] for Sun-Sat



class AuthConfig(BaseModel):
    """Authentication configuration for scraping"""
    linkedinEmail: Optional[str] = None
    linkedinPassword: Optional[str] = None
    useCustomAuth: bool = False


class SearchProfile(BaseModel):
    """Saved search profile with filters"""
    userId: str = "leonardo"  # Default user for now
    name: str
    filters: SearchFilters
    schedule: Optional[ScheduleConfig] = None
    authConfig: Optional[AuthConfig] = None
    maxJobsPerRun: int = 100
    isActive: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ==================== CRAWL RUNS ====================

class CrawlRunStats(BaseModel):
    """Statistics for a crawl run"""
    jobsFound: int = 0
    jobsNew: int = 0
    jobsUpdated: int = 0
    jobsFailed: int = 0
    avgExtractionTime: float = 0.0  # milliseconds


class CrawlError(BaseModel):
    """Error during crawl"""
    url: str
    error: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrawlRunStatus(str, Enum):
    """Crawl run status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class CrawlRun(BaseModel):
    """Record of a search execution"""
    profileId: str
    profileName: str  # Denormalized for easy display
    startedAt: datetime = Field(default_factory=datetime.utcnow)
    finishedAt: Optional[datetime] = None
    status: CrawlRunStatus = CrawlRunStatus.RUNNING
    stats: CrawlRunStats = Field(default_factory=CrawlRunStats)
    errors: List[CrawlError] = []
    sources: List[str] = []  # ["linkedin", "gupy", "indeed"]

    class Config:
        use_enum_values = True


# ==================== API REQUEST/RESPONSE MODELS ====================

# API Request/Response Models
class CreateJobRequest(BaseModel):
    """Request to create job manually"""
    url: Optional[HttpUrl] = None
    title: str
    company: str
    description: str
    location: Optional[Location] = None
    salary: Optional[SalaryExplicit] = None


class ScrapeJobRequest(BaseModel):
    """Request to scrape job from URL"""
    url: HttpUrl
    sourceHint: Optional[str] = None  # Manual hint: "linkedin", "gupy"


class JobResponse(BaseModel):
    """API response for job"""
    id: str
    url: str
    title: Optional[str]
    company: Optional[str]
    location: Optional[Location]
    salary: Optional[SalaryExplicit]
    rankingScore: Optional[float]
    createdAt: datetime


# Search Profile API Models
class CreateProfileRequest(BaseModel):
    """Request to create search profile"""
    name: str
    filters: SearchFilters
    schedule: Optional[ScheduleConfig] = None
    authConfig: Optional[AuthConfig] = None
    maxJobsPerRun: int = 50


class UpdateProfileRequest(BaseModel):
    """Request to update search profile"""
    name: Optional[str] = None
    filters: Optional[SearchFilters] = None
    schedule: Optional[ScheduleConfig] = None
    authConfig: Optional[AuthConfig] = None
    maxJobsPerRun: Optional[int] = None
    isActive: Optional[bool] = None


class ProfileResponse(BaseModel):
    """API response for search profile"""
    id: str
    name: str
    filters: SearchFilters
    schedule: Optional[ScheduleConfig]
    maxJobsPerRun: int
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class RunSearchRequest(BaseModel):
    """Request to run search"""
    profileId: str
    sources: Optional[List[str]] = None  # If None, use all sources


class CrawlRunResponse(BaseModel):
    """API response for crawl run"""
    id: str
    profileName: str
    status: str
    stats: CrawlRunStats
    startedAt: datetime
    finishedAt: Optional[datetime]
    errors: List[CrawlError]

