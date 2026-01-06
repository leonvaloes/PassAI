"""
Pydantic schemas for Resume API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class InputType(str, Enum):
    """Job input types"""
    TEXT = "text"
    URL = "url"
    PDF = "pdf"
    SCREENSHOT = "screenshot"


class JobCreateRequest(BaseModel):
    """Request to create a job"""
    input_type: InputType = Field(..., description="Type of input")
    content: str = Field(..., description="Job content (URL, text, or base64 PDF/image)")


class JobResponse(BaseModel):
    """Job data response"""
    id: str
    cargo: str
    empresa: str
    ats_detectado: str
    requisitos_tecnicos: List[str]
    requisitos_comportamentais: List[str]
    local: Optional[str] = None
    modalidade: Optional[str] = None


class GenerateRequest(BaseModel):
    """Request to generate variants"""
    base_resume: Optional[Dict[str, Any]] = None


class VariantResponse(BaseModel):
    """Variant data response"""
    id: str
    job_id: str
    round: int
    ats_score: float
    ats_status: str
    ranking_score: float
    motivos: List[str]
    content: Dict[str, Any]
    created_at: str


class ProgressUpdate(BaseModel):
    """WebSocket progress update"""
    type: str  # progress, complete, error
    round: Optional[int] = None
    variants_total: Optional[int] = None
    variants_approved: Optional[int] = None
    best_score: Optional[float] = None
    message: Optional[str] = None
