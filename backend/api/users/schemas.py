"""
Pydantic schemas for User API
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class Experience(BaseModel):
    """Work experience entry"""
    empresa: str
    cargo: str
    periodo: str
    descricao: str
    tecnologias: List[str] = []
    realizacoes: List[str] = []


class Education(BaseModel):
    """Education entry"""
    instituicao: str
    curso: str
    periodo: str


class Language(BaseModel):
    """Language proficiency"""
    idioma: str
    nivel: str


class UserProfileCreate(BaseModel):
    """Schema for creating a new user profile"""
    profile_name: str = Field(..., min_length=2, max_length=50, description="Unique username/identifier")
    nome: str = Field(..., min_length=2, description="Full name")
    email: EmailStr
    telefone: str
    linkedin: str
    github: Optional[str] = None
    cidade: str
    estado: str
    cargo_atual: str
    experiencias: List[Experience] = []
    educacao: List[Education] = []
    habilidades: List[str] = []
    idiomas: List[Language] = []


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (all optional)"""
    profile_name: Optional[str] = None
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cargo_atual: Optional[str] = None
    experiencias: Optional[List[Experience]] = None
    educacao: Optional[List[Education]] = None
    habilidades: Optional[List[str]] = None
    idiomas: Optional[Language] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: str
    profile_name: str
    nome: str
    email: str
    telefone: str
    linkedin: str
    github: Optional[str]
    cidade: str
    estado: str
    cargo_atual: str
    experiencias: List[Experience]
    educacao: List[Education]
    habilidades: List[str]
    idiomas: List[Language]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProfileList(BaseModel):
    """Schema for list of users"""
    users: List[UserProfileResponse]
    total: int
    active_user_id: Optional[str] = None


class SetActiveUserRequest(BaseModel):
    """Schema for setting active user"""
    user_id: str


class AIExtractRequest(BaseModel):
    """Schema for AI extraction from natural language text"""
    text: str = Field(..., min_length=10, description="Natural language text describing professional background")


class AIExtractResponse(BaseModel):
    """Schema for AI extraction response"""
    experiencias: List[Experience] = []
    educacao: List[Education] = []
    habilidades: List[str] = []
    idiomas: List[Language] = []
    success: bool = True
    message: Optional[str] = None
