"""
Resume API Routes - FastAPI endpoints for Resume Generator UI
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
import asyncio
import logging
from datetime import datetime

from .schemas import (
    JobCreateRequest,
    JobResponse,
    GenerateRequest,
    VariantResponse,
    ProgressUpdate
)
from modules.resume.job_extractor import JobExtractor
from modules.resume.variant_generator import VariantGenerator
from modules.resume.ats_simulator import ATSSimulator
from modules.resume.ranker import Ranker
from modules.resume.template_engine import TemplateEngine
from modules.resume.ats_detector import ATSDetector
from modules.resume.learning_engine import LearningEngine
from modules.resume.llm_adapter import create_llm_for_resume
from core.ai.vision_processor import VisionProcessor
from database.mongodb import get_mongodb
import yaml

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume", tags=["resume"])

# Global instances (initialized on startup)
job_extractor = None
variant_generator = None
ranker = None
template_engine = None
learning_engine = None
db = None

# Active WebSocket connections
active_connections: dict = {}


def init_resume_system():
    """Initialize resume system components"""
    global job_extractor, variant_generator, ranker, template_engine, learning_engine, db
    
    # Load config
    with open('backend/config/resume_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)['resume']
    
    # Initialize components
    llm_router = create_llm_for_resume()
    vision_processor = VisionProcessor()
    db = get_mongodb()
    
    ats_detector = ATSDetector()
    ats_simulator = ATSSimulator(ats_detector)
    
    job_extractor = JobExtractor(
        vision_processor=vision_processor,
        llm_router=llm_router
    )
    
    variant_generator = VariantGenerator(
        llm_router=llm_router,
        knowledge_base=None,  # Optional RAG
        ats_simulator=ats_simulator,
        config=config
    )
    
    ranker = Ranker(config)
    template_engine = TemplateEngine(config['template_path'])
    learning_engine = LearningEngine(ranker)
    
    logger.info("✅ Resume system initialized")


@router.post("/jobs", response_model=JobResponse)
async def create_job(request: JobCreateRequest):
    """Create a new job from user input"""
    try:
        # Extract job data
        job = job_extractor.extract({
            "type": request.input_type,
            "content": request.content
        })
        
        # Save to MongoDB
        job_id = db.insert_job(job.dict(by_alias=True, exclude={'id'}))
        job.id = job_id
        
        return JobResponse(
            id=str(job_id),
            cargo=job.cargo,
            empresa=job.empresa,
            ats_detectado=job.ats_detectado.value,
            requisitos_tecnicos=job.requisitos_tecnicos,
            requisitos_comportamentais=job.requisitos_comportamentais,
            local=job.local,
            modalidade=job.modalidade
        )
    
    except Exception as e:
        logger.error(f"Job extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job details"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(**job)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    try:
        db.delete_job(job_id)
        return {"message": "Job deleted successfully"}
    
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/generate")
async def start_generation(job_id: str, request: GenerateRequest):
    """Start variant generation (returns immediately, sends updates via WebSocket)"""
    try:
        # Get job
        job_data = db.get_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Start generation in background
        asyncio.create_task(generate_variants_task(job_id, job_data, request.base_resume))
        
        return {"message": "Generation started", "job_id": job_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_variants_task(job_id: str, job_data: dict, base_resume: dict):
    """Background task for generating variants"""
    try:
        from database.models import Job
        job = Job(**job_data)
        
        # Progress callback
        def progress_callback(round_num, variants, approved):
            # Send WebSocket update
            if job_id in active_connections:
                asyncio.create_task(
                    active_connections[job_id].send_json({
                        "type": "progress",
                        "round": round_num,
                        "variants_total": len(variants),
                        "variants_approved": approved,
                        "best_score": max([v.ats_score for v in variants]) if variants else 0
                    })
                )
        
        # Generate variants
        variants = variant_generator.generate_variants(
            job=job,
            base_resume=base_resume,
            template_path=template_engine.template_path,
            callback=progress_callback
        )
        
        # Rank variants
        ranked = ranker.rank(variants, job)
        
        # Send completion
        if job_id in active_connections:
            await active_connections[job_id].send_json({
                "type": "complete",
                "total_variants": len(ranked),
                "approved_count": len([v for v in ranked if v.ats_status.value == 'APPROVED'])
            })
    
    except Exception as e:
        logger.error(f"Generation task failed: {e}")
        if job_id in active_connections:
            await active_connections[job_id].send_json({
                "type": "error",
                "message": str(e)
            })


@router.get("/jobs/{job_id}/variants", response_model=List[VariantResponse])
async def list_variants(job_id: str):
    """List all variants for a job"""
    try:
        variants = db.list_variants(job_id)
        return [VariantResponse(**v) for v in variants]
    
    except Exception as e:
        logger.error(f"Failed to list variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variants/{variant_id}", response_model=VariantResponse)
async def get_variant(variant_id: str):
    """Get variant details"""
    try:
        variant = db.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        return VariantResponse(**variant)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variants/{variant_id}/download")
async def download_variant(variant_id: str):
    """Download variant as DOCX"""
    try:
        variant = db.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        # Generate DOCX
        output_path = f"output/variant_{variant_id}.docx"
        result = template_engine.fill_template(
            content=variant['content'],
            output_path=output_path
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Template filling failed'))
        
        return FileResponse(
            path=output_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=f"resume_{variant_id}.docx"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time generation updates"""
    await websocket.accept()
    active_connections[job_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {job_id}")
    
    finally:
        if job_id in active_connections:
            del active_connections[job_id]
