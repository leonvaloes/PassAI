"""
MongoDB Database Models for PassAI Resume Generator
"""
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class ATSType(str, Enum):
    """Supported ATS systems"""
    GUPY = "gupy"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    TALEO = "taleo"
    UNKNOWN = "unknown"


class JobSource(str, Enum):
    """Job posting source types"""
    URL = "url"
    TEXT = "text"
    PDF = "pdf"
    SCREENSHOT = "screenshot"


class ATSStatus(str, Enum):
    """ATS simulation status"""
    APPROVED = "APPROVED"
    RISK = "RISK"
    REJECTED = "REJECTED"


class Job(BaseModel):
    """Job posting model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    source: JobSource
    url: Optional[str] = None
    raw_content: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    # Extracted fields
    cargo: str
    empresa: str
    local: Optional[str] = None
    modalidade: Optional[str] = None  # remoto/hibrido/presencial
    senioridade: Optional[str] = None
    salario: Optional[str] = None
    beneficios: List[str] = Field(default_factory=list)
    requisitos_tecnicos: List[str] = Field(default_factory=list)
    requisitos_comportamentais: List[str] = Field(default_factory=list)
    
    # ATS detection
    ats_detectado: ATSType = ATSType.UNKNOWN
    ats_confirmado: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ResumeVariant(BaseModel):
    """Generated resume variant"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    job_id: PyObjectId
    round: int
    batch_index: int
    seed: int
    temperature: float
    
    # Content (structured sections)
    content: Dict[str, any]  # {resumo: str, experiencias: [...], educacao: [...]}
    
    # ATS scoring
    ats_score: float = 0.0
    ats_status: ATSStatus = ATSStatus.REJECTED
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    checklist: Dict[str, bool] = Field(default_factory=dict)
    motivos: List[str] = Field(default_factory=list)
    
    # Ranking
    ranking_score: float = 0.0
    ranking_position: Optional[int] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    layout_preserved: bool = True
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserDecision(BaseModel):
    """User decision on a variant"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    variant_id: PyObjectId
    job_id: PyObjectId
    action: str  # approved, rejected, chosen
    timestamp: datetime = Field(default_factory=datetime.now)
    feedback: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ATSPattern(BaseModel):
    """Learned ATS detection patterns"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    empresa: str
    ats_type: ATSType
    confidence: float  # 0.0 - 1.0
    confirmed_count: int = 0
    last_confirmed: Optional[datetime] = None
    
    # Detection hints
    url_patterns: List[str] = Field(default_factory=list)
    text_patterns: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class KnowledgeChunk(BaseModel):
    """RAG knowledge base chunk"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    source: str  # video filename or URL
    chunk_text: str
    chunk_index: int
    
    # Metadata
    ats_type: Optional[ATSType] = None
    extracted_rules: List[str] = Field(default_factory=list)
    
    # For vector DB reference
    vector_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
