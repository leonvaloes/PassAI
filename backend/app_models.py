from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Experience(BaseModel):
    empresa: str
    cargo: str
    periodo: str
    descricao: str
    tecnologias: list[str] = Field(default_factory=list)
    realizacoes: list[str] = Field(default_factory=list)


class Education(BaseModel):
    instituicao: str
    curso: str
    periodo: str


class Language(BaseModel):
    idioma: str
    nivel: str


class UserProfileBase(BaseModel):
    profile_name: str = Field(min_length=2, max_length=50)
    nome: str = Field(min_length=2)
    email: str
    telefone: str
    linkedin: str
    github: str | None = None
    cidade: str
    estado: str
    cargo_atual: str
    experiencias: list[Experience] = Field(default_factory=list)
    educacao: list[Education] = Field(default_factory=list)
    habilidades: list[str] = Field(default_factory=list)
    idiomas: list[Language] = Field(default_factory=list)


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    profile_name: str | None = None
    nome: str | None = None
    email: str | None = None
    telefone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cargo_atual: str | None = None
    experiencias: list[Experience] | None = None
    educacao: list[Education] | None = None
    habilidades: list[str] | None = None
    idiomas: list[Language] | None = None


class UserProfileResponse(UserProfileBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfileList(BaseModel):
    users: list[UserProfileResponse]
    total: int
    active_user_id: str | None = None


class SetActiveUserRequest(BaseModel):
    user_id: str


class JobCreateRequest(BaseModel):
    input_type: Literal["text", "url", "pdf", "screenshot"] = "text"
    content: str = Field(min_length=10)


class JobResponse(BaseModel):
    id: str
    cargo: str
    empresa: str
    ats_detectado: str
    requisitos_tecnicos: list[str]
    requisitos_comportamentais: list[str]
    local: str | None = None
    modalidade: str | None = None


class GenerateRequest(BaseModel):
    count: int | None = None
    base_resume: dict[str, Any] | None = None


class VariantResponse(BaseModel):
    id: str
    job_id: str
    round: int
    ats_score: float
    ats_status: str
    ranking_score: float
    motivos: list[str]
    content: dict[str, Any]
    created_at: str


class HistoryResponse(BaseModel):
    job_id: str
    job_title: str
    company: str
    created_at: str
    variants_count: int
    best_score: float
    status: str
    has_cvs: bool
    source: str
