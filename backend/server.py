from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app_models import (  # noqa: E402
    GenerateRequest,
    HistoryResponse,
    JobCreateRequest,
    JobResponse,
    SetActiveUserRequest,
    UserProfileCreate,
    UserProfileList,
    UserProfileResponse,
    UserProfileUpdate,
    VariantResponse,
)
from backend.app_store import JsonStore  # noqa: E402
from backend.cv_service import ResumeService  # noqa: E402


def create_app(
    data_file: str | None = None,
    output_dir: str | None = None,
    enable_llm: bool | None = None,
) -> FastAPI:
    resolved_data_file = data_file or os.getenv(
        "PASSAI_DATA_FILE", str(PROJECT_ROOT / "data" / "passai_state.json")
    )
    resolved_output_dir = output_dir or os.getenv("PASSAI_OUTPUT_DIR", str(PROJECT_ROOT / "output" / "generated"))
    resolved_enable_llm = enable_llm if enable_llm is not None else (data_file is None and output_dir is None)

    store = JsonStore(resolved_data_file)
    resume_service = ResumeService(resolved_output_dir, enable_llm=resolved_enable_llm)

    app = FastAPI(title="PassAI", version="3.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def serialize_user(user: dict) -> UserProfileResponse:
        return UserProfileResponse(**user)

    def serialize_job(job: dict) -> JobResponse:
        return JobResponse(
            id=job["id"],
            cargo=job["cargo"],
            empresa=job["empresa"],
            ats_detectado=job["ats_detectado"],
            requisitos_tecnicos=job["requisitos_tecnicos"],
            requisitos_comportamentais=job["requisitos_comportamentais"],
            local=job.get("local"),
            modalidade=job.get("modalidade"),
        )

    def serialize_variant(variant: dict) -> VariantResponse:
        return VariantResponse(
            id=variant["id"],
            job_id=variant["job_id"],
            round=variant["round"],
            ats_score=variant["ats_score"],
            ats_status=variant["ats_status"],
            ranking_score=variant["ranking_score"],
            motivos=variant["motivos"],
            content=variant["content"],
            created_at=variant["created_at"],
        )

    @app.get("/health")
    async def health() -> dict:
        state = store.snapshot()
        return {
            "status": "ok",
            "users": len(state["users"]),
            "jobs": len(state["jobs"]),
            "variants": len(state["variants"]),
            "features": ["resume_generation", "user_management"],
        }

    @app.get("/api/users", response_model=UserProfileList)
    async def list_users() -> UserProfileList:
        users = [serialize_user(user) for user in store.list_users()]
        return UserProfileList(users=users, total=len(users), active_user_id=store.get_active_user_id())

    @app.post("/api/users", response_model=UserProfileResponse, status_code=201)
    async def create_user(payload: UserProfileCreate) -> UserProfileResponse:
        try:
            user = store.create_user(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return serialize_user(user)

    @app.get("/api/users/{user_id}", response_model=UserProfileResponse)
    async def get_user(user_id: str) -> UserProfileResponse:
        user = store.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return serialize_user(user)

    @app.put("/api/users/{user_id}", response_model=UserProfileResponse)
    async def update_user(user_id: str, payload: UserProfileUpdate) -> UserProfileResponse:
        update_data = {key: value for key, value in payload.model_dump().items() if value is not None}
        try:
            user = store.update_user(user_id, update_data)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return serialize_user(user)

    @app.delete("/api/users/{user_id}", status_code=204)
    async def delete_user(user_id: str) -> None:
        if not store.get_user(user_id):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        store.delete_user(user_id)

    @app.get("/api/users/active/current", response_model=UserProfileResponse)
    async def get_active_user() -> UserProfileResponse:
        active_user_id = store.get_active_user_id()
        if not active_user_id:
            raise HTTPException(status_code=404, detail="No active user set. Please create or select a user first.")
        user = store.get_user(active_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Active user not found")
        return serialize_user(user)

    @app.put("/api/users/active/set")
    async def set_active_user(payload: SetActiveUserRequest) -> dict:
        user = store.get_user(payload.user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {payload.user_id} not found")
        store.set_active_user_id(payload.user_id)
        return {
            "success": True,
            "active_user_id": payload.user_id,
            "message": f"Active user set to: {user['nome']}",
        }

    @app.post("/api/resume/jobs", response_model=JobResponse)
    async def create_job(payload: JobCreateRequest) -> JobResponse:
        parsed_job = resume_service.parse_job(payload.content, payload.input_type)
        job = store.create_job(parsed_job)
        return serialize_job(job)

    @app.get("/api/resume/jobs/{job_id}", response_model=JobResponse)
    async def get_job(job_id: str) -> JobResponse:
        job = store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return serialize_job(job)

    @app.delete("/api/resume/jobs/{job_id}")
    async def delete_job(job_id: str) -> dict:
        if not store.get_job(job_id):
            raise HTTPException(status_code=404, detail="Job not found")
        store.delete_job(job_id)
        return {"message": "Job deleted successfully"}

    def create_variants_for_job(job_id: str, count: int, replace: bool = False) -> dict:
        job = store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        active_user_id = store.get_active_user_id()
        if not active_user_id:
            raise HTTPException(status_code=400, detail="No active user set. Please create or select a user first.")

        user = store.get_user(active_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Active user not found")

        existing_variants = store.list_variants(job_id)
        variants = resume_service.generate_variants(
            user=user,
            job=job,
            count=count,
            existing_count=0 if replace else len(existing_variants),
        )
        store.save_variants(job_id, variants, replace=replace)
        return {
            "message": "Generation completed",
            "job_id": job_id,
            "generated_variants": len(variants),
            "total_variants": len(store.list_variants(job_id)),
        }

    @app.post("/api/resume/jobs/{job_id}/generate")
    async def generate_variants(job_id: str, payload: GenerateRequest) -> dict:
        count = payload.count or 3
        return create_variants_for_job(job_id, count=count, replace=True)

    @app.post("/api/resume/jobs/{job_id}/generate-more")
    async def generate_more_variants(job_id: str, count: int = 3) -> dict:
        return create_variants_for_job(job_id, count=count, replace=False)

    @app.get("/api/resume/jobs/{job_id}/variants", response_model=list[VariantResponse])
    async def list_variants(job_id: str) -> list[VariantResponse]:
        if not store.get_job(job_id):
            raise HTTPException(status_code=404, detail="Job not found")
        return [serialize_variant(variant) for variant in store.list_variants(job_id)]

    @app.get("/api/resume/variants/{variant_id}", response_model=VariantResponse)
    async def get_variant(variant_id: str) -> VariantResponse:
        variant = store.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        return serialize_variant(variant)

    @app.delete("/api/resume/variants/{variant_id}")
    async def delete_variant(variant_id: str) -> dict:
        variant = store.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        output_path = Path(variant["output_path"])
        if output_path.exists():
            output_path.unlink()
        store.delete_variant(variant_id)
        return {"message": "Variant deleted successfully"}

    @app.get("/api/resume/variants/{variant_id}/download")
    async def download_variant(variant_id: str) -> FileResponse:
        variant = store.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        output_path = resume_service.ensure_docx(variant)
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"cv_{variant_id}.docx",
        )

    @app.get("/api/resume/history", response_model=list[HistoryResponse])
    async def history() -> list[HistoryResponse]:
        jobs = store.list_jobs()
        history_items = []
        for job in jobs:
            variants = store.list_variants(job["id"])
            best_score = max((variant["ats_score"] for variant in variants), default=0.0)
            history_items.append(
                HistoryResponse(
                    job_id=job["id"],
                    job_title=job["cargo"],
                    company=job["empresa"],
                    created_at=job["created_at"],
                    variants_count=len(variants),
                    best_score=round(best_score, 1),
                    status="completed" if variants else "no_cvs",
                    has_cvs=bool(variants),
                    source=job["input_type"],
                )
            )
        return sorted(history_items, key=lambda item: item.created_at, reverse=True)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
