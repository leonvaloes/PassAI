"""
Resume API Routes - FastAPI endpoints for Resume Generator UI
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
import asyncio
import logging
from datetime import datetime
from bson import ObjectId

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
    
    # Load config (robust path)
    import os
    # Get absolute path to backend directory (d:\p2\ai-copilot\backend)
    current_file = os.path.abspath(__file__)
    api_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # backend/api/resume -> backend
    config_path = os.path.join(api_dir, 'config', 'resume_config.yaml')
    
    logger.info(f"Loading resume config from: {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Config NOT found at: {config_path}")
        # Final fallback - assume CWD
        config_path = os.path.abspath('backend/config/resume_config.yaml')
        logger.info(f"Fallback config path: {config_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Resume config not found at {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
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
    
    # Resolve template path to absolute
    template_path = config['template_path']
    if not os.path.isabs(template_path):
        # __file__ is backend/api/resume/routes.py
        # Go up 3 levels: routes.py -> resume -> api -> backend -> project_root
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(backend_dir)  # One more level up from backend/
        template_path = os.path.join(project_root, template_path)
    
    logger.info(f"Resolved template path: {template_path}")
    
    if not os.path.exists(template_path):
        logger.error(f"Template file not found at: {template_path}")
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    template_engine = TemplateEngine(template_path)
    learning_engine = LearningEngine(ranker)
    
    logger.info(f"✅ Resume system initialized. JobExtractor ID: {id(job_extractor)}")


@router.post("/jobs", response_model=JobResponse)
async def create_job(request: JobCreateRequest):
    """Create a new job from user input"""
    logger.info(f"create_job called. input_type={request.input_type}")
    logger.info(f"Global job_extractor ID: {id(job_extractor) if job_extractor else 'None'}")
    
    try:
        if job_extractor is None:
            logger.error("job_extractor is None!")
            raise HTTPException(status_code=503, detail="Resume system not initialized")

        # Extract job data
        job = job_extractor.extract({
            "type": request.input_type,
            "content": request.content
        })
        
        # Save to MongoDB
        job_id = db.insert_job(job.dict(by_alias=True, exclude={'id'}))
        logger.info(f"Job inserted. ID: {job_id} (type: {type(job_id)})")
        
        # Verify immediately
        verify = db.get_job(job_id)
        logger.info(f"Immediate verification: {'Found' if verify else 'NOT FOUND'}")
        
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
        logger.error(f"Job extraction failed: {e}", exc_info=True)
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
    logger.info(f"start_generation called for job_id: '{job_id}' (len={len(job_id)})")
    
    try:
        if db is None:
            logger.error("CRITICAL: db instance is None in start_generation!")
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Debug existence
        count = db.jobs.count_documents({"_id": ObjectId(job_id)}) if len(job_id) == 24 else -1
        logger.info(f"Direct count for ID {job_id}: {count}")

        # Get job
        job_data = db.get_job(job_id)
        logger.info(f"db.get_job retrieved: {type(job_data)} - {job_data.keys() if job_data else 'None'}")
        
        if not job_data:
            # Fallback: Check if it exists in job_postings (from Scraper)
            try:
                job_data = db.db.job_postings.find_one({"_id": ObjectId(job_id)})
                if job_data:
                    logger.info(f"Job found in job_postings (Scraper DB). Adapting to Resume format...")
                    
                    # Adapt JobPosting to Job format
                    adapted_job = {
                        "_id": job_data["_id"],
                        "source": "url",
                        "url": job_data.get("url"),
                        "raw_content": job_data.get("description") or job_data.get("rawText") or "",
                        "cargo": job_data.get("title", "Unknown Role"),
                        "empresa": job_data.get("company", "Unknown Company"),
                        "local": job_data.get("location", {}).get("city", "") if isinstance(job_data.get("location"), dict) else str(job_data.get("location", "")),
                        "modalidade": "remoto" if job_data.get("location", {}).get("remote") else "presencial",
                        "senioridade": job_data.get("seniority"),
                        "salario": str(job_data.get("salaryExplicit", "")) if job_data.get("salaryExplicit") else None,
                        "requisitos_tecnicos": job_data.get("techKeywords", []) + job_data.get("mustHave", []),
                        "requisitos_comportamentais": job_data.get("niceToHave", []),
                        "ats_detectado": "unknown",
                        "status": "CREATED"
                    }
                    job_data = adapted_job
                    
            except Exception as e:
                logger.error(f"Failed to check job_postings fallback: {e}")

        if not job_data:
            logger.error(f"Job not found for ID: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
            
        # Validate/Enrich Data if missing requirements
        reqs = job_data.get('requisitos_tecnicos', [])
        if not reqs:
            logger.warning(f"Job {job_id} has NO requirements. Triggering On-Demand Enrichment...")
            
            # Use AI Enricher from jobs module
            from modules.jobs.enricher import enrich_job_with_ai
            from core.llm.router import LLMRouter
            
            # Prepare data for enricher
            enrich_payload = {
                'rawText': job_data.get('raw_content') or job_data.get('description', ''),
                'description': job_data.get('raw_content') or job_data.get('description', '')
            }
            
            # Enrich
            llm_router_instance = LLMRouter() # Create fresh instance
            enriched = enrich_job_with_ai(enrich_payload, llm_router_instance)
            
            # Update job_data
            job_data['requisitos_tecnicos'] = enriched.get('techKeywords', []) + enriched.get('mustHave', [])
            job_data['requisitos_comportamentais'] = enriched.get('niceToHave', [])
            
            # Update seniority if missing
            if not job_data.get('senioridade'):
                job_data['senioridade'] = enriched.get('seniority')
                
            logger.info(f"✅ On-Demand Enrichment result: {len(job_data['requisitos_tecnicos'])} reqs found")

        # Load active user profile from MongoDB
        active_user_id = db.get_active_user_id()
        
        if not active_user_id:
            # Try auto-select if only one user exists
            users = list(db.db.user_profiles.find().limit(2))
            if len(users) == 1:
                active_user_id = str(users[0]["_id"])
                db.set_active_user_id(active_user_id)
                logger.info(f"🌟 Auto-selected only user as active: {active_user_id}")
                user_profile = users[0]
            else:
                logger.error("❌ No active user set!")
                raise HTTPException(
                    status_code=400,
                    detail="No active user set. Please select a user in the User Management section."
                )
        else:
            user_profile = db.db.user_profiles.find_one({"_id": ObjectId(active_user_id)})
            
            if not user_profile:
                logger.error(f"❌ Active user {active_user_id} not found in database!")
                raise HTTPException(
                    status_code=404,
                    detail=f"Active user profile not found in database. Please select a valid user."
                )
        
        logger.info(f"✅ Loaded profile: {user_profile['nome']} ({len(user_profile['experiencias'])} experiences, {len(user_profile['habilidades'])} skills)")
        
        # Build base_resume from profile
        base_resume = {
            'nome': user_profile['nome'],
            'cargo': user_profile.get('cargo_atual', 'Desenvolvedor Full-Stack'),
            'email': user_profile['email'],
            'telefone': user_profile['telefone'],
            'linkedin': user_profile['linkedin'],
            'cidade': user_profile['cidade'],
            'estado': user_profile['estado'],
            'experiencias': user_profile['experiencias'],  # ALL experiences for AI to choose
            'educacao': user_profile['educacao'],
            'habilidades': user_profile['habilidades']
        }
        
        # Extract count from request (if provided)
        count = request.count if request.count else None
        
        # Start generation in background
        asyncio.create_task(generate_variants_task(job_id, job_data, base_resume, count))
        
        return {"message": "Generation started", "job_id": job_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_variants_task(job_id: str, job_data: dict, base_resume: dict, count: Optional[int] = None):
    """Background task for generating variants"""
    try:
        from database.models import Job
        job = Job(**job_data)
        
        # Progress callback (must be thread-safe or schedule on loop)
        loop = asyncio.get_running_loop()
        
        def progress_callback(round_num, variants, approved):
            # Schedule WS update on the main loop
            # Schedule WS update on the main loop
            if job_id in active_connections:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        active_connections[job_id].send_json({
                            "type": "progress",
                            "round": round_num,
                            "variants_total": len(variants),
                            "variants_approved": approved,
                            "best_score": max([v.ats_score for v in variants]) if variants else 0
                        }),
                        loop
                    )
                except Exception as ex:
                    logger.error(f"Failed to schedule WS update: {ex}")
        
        # Run blocking generation in thread pool
        variants = await loop.run_in_executor(
            None,
            lambda: variant_generator.generate_variants(
                job=job,
                base_resume=base_resume,
                template_path=template_engine.template_path,
                callback=progress_callback,
                initial_count=count  # Pass user-selected count
            )
        )
        
        # Rank variants (also blocking, so offload)
        ranked = await loop.run_in_executor(
            None,
            lambda: ranker.rank(variants, job)
        )
        
        # SAVE VARIANTS TO DB (CRITICAL FIX)
        if db:
            logger.info(f"Saving {len(ranked)} variants to database...")
            for v in ranked:
                # Convert to dict and ensure job_id is ObjectId if needed
                variant_data = v.dict()
                db.insert_variant(variant_data)
        else:
            logger.error("Database connection lost! Cannot save variants.")
        
        # Send completion
        if job_id in active_connections:
            await active_connections[job_id].send_json({
                "type": "complete",
                "total_variants": len(ranked),
                "approved_count": len([v for v in ranked if v.ats_status.value == 'APPROVED'])
            })
    
    except Exception as e:
        logger.error(f"Generation task failed: {e}", exc_info=True)
        if job_id in active_connections:
            await active_connections[job_id].send_json({
                "type": "error",
                "message": str(e)
            })


@router.get("/jobs/{job_id}/variants", response_model=List[VariantResponse])
async def list_variants(job_id: str):
    """List all variants for a job"""
    try:
        variants = db.get_variants_by_job(job_id)
        # Fix IDs for Pydantic
        results = []
        for v in variants:
            v['id'] = str(v.pop('_id')) if '_id' in v else v.get('id')
            v['job_id'] = str(v['job_id'])
            
            # Handle datetime serialization
            if 'created_at' in v and hasattr(v['created_at'], 'isoformat'):
                v['created_at'] = v['created_at'].isoformat()
            
            # Handle Enums just in case
            if 'ats_status' in v and hasattr(v['ats_status'], 'value'):
                v['ats_status'] = v['ats_status'].value
                
            results.append(v)
            
        return [VariantResponse(**v) for v in results]
    
    except Exception as e:
        logger.error(f"Failed to list variants: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/variants/{variant_id}")
async def delete_variant(variant_id: str):
    """Delete a specific variant"""
    try:
        if not db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Delete the variant
        result = db.variants.delete_one({"_id": ObjectId(variant_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        logger.info(f"Deleted variant: {variant_id}")
        return {"message": "Variant deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/generate-more")
async def generate_more_variants(job_id: str, count: int = 3):
    """
    Generate additional variants for an existing job (incremental)
    Does NOT delete existing variants - appends new ones
    Limit: 1-10 variants per request
    """
    try:
        # Validate count
        if count < 1 or count > 10:
            raise HTTPException(
                status_code=400,
                detail="Count must be between 1 and 10"
            )
        
        if not variant_generator or not db:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Check if LLM is available
        if not variant_generator.llm or not hasattr(variant_generator.llm, 'llm'):
            raise HTTPException(
                status_code=503, 
                detail="Codex service not available. Please ensure Codex CLI is installed and authenticated."
            )
        
        # Verify job exists
        try:
            job_dict = db.get_job(job_id)
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")
        
        if not job_dict:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Convert dict to Job model (from database.models, not jobs.models)
        from database.models import Job
        job = Job(**job_dict)
        
        logger.info(f"Starting incremental generation: +{count} variants for job {job_id}")
        
        # Load active user profile from MongoDB
        active_user_id = db.get_active_user_id()
        
        if not active_user_id:
            # Try auto-select if only one user exists
            users = list(db.db.user_profiles.find().limit(2))
            if len(users) == 1:
                active_user_id = str(users[0]["_id"])
                db.set_active_user_id(active_user_id)
                user_profile = users[0]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No active user set. Please select a user first."
                )
        else:
            user_profile = db.db.user_profiles.find_one({"_id": ObjectId(active_user_id)})
            
            if not user_profile:
                raise HTTPException(
                    status_code=404,
                    detail="Active user profile not found in database."
                )
        
        # Build base_resume from profile
        base_resume = {
            'nome': user_profile['nome'],
            'cargo': user_profile.get('cargo_atual', 'Desenvolvedor Full-Stack'),
            'email': user_profile['email'],
            'telefone': user_profile['telefone'],
            'linkedin': user_profile['linkedin'],
            'cidade': user_profile['cidade'],
            'estado': user_profile['estado'],
            'experiencias': user_profile['experiencias'],
            'educacao': user_profile['educacao'],
            'habilidades': user_profile['habilidades']
        }
        
        # Generate exactly N variants using generate_variants() with initial_count
        try:
            generated = variant_generator.generate_variants(
                job=job,
                base_resume=base_resume,
                template_path=template_engine.template_path,
                initial_count=count  # This will stop after first batch
            )
            
            # Save each variant to database
            for i, variant in enumerate(generated, 1):
                variant_id = db.insert_variant(variant.dict(by_alias=True, exclude={'id'}))
                variant.id = variant_id
                logger.info(f"Generated variant {i}/{count}: Score {variant.ats_score:.1f}")
                
        except Exception as e:
            logger.error(f"Variant generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate variants: {str(e)}. Is Codex CLI available?"
            )
        
        logger.info(f"Incremental generation complete: +{len(generated)} new variants")
        
        # Count total variants for this job
        total = db.db.resume_variants.count_documents({"job_id": ObjectId(job_id)})
        
        return {
            "message": f"Generated {len(generated)} additional variants",
            "new_variants": len(generated),
            "total_variants": total,
            "job_id": job_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate more variants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variants/{variant_id}", response_model=VariantResponse)
async def get_variant(variant_id: str):
    """Get variant details"""
    try:
        variant = db.get_variant(variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        variant['id'] = str(variant.pop('_id')) if '_id' in variant else variant.get('id')
        variant['job_id'] = str(variant['job_id'])
        
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


@router.get("/history")
async def get_resume_history():
    """
    Get ALL ranked jobs with their CV generation status
    Returns: all jobs from 'jobs' collection + 'job_postings' collection with variant counts
    """
    try:
        # Get jobs from BOTH collections (Resume Generator 'jobs' and Aggregator 'job_postings')
        # This fixes the issue where scraped jobs (in job_postings) weren't showing up in history
        
        # 1. Get Resume Generator jobs
        resume_jobs_cursor = db.db.jobs.find()
        
        # 2. Get Aggregator jobs (Scraped)
        aggregator_jobs_cursor = db.db.job_postings.find()
        
        all_jobs_map = {}
        
        # Helper to process job doc
        def process_job(job, source_collection):
            job_id = str(job["_id"])
            
            # Skip if already processed (deduplication by ID if they share IDs, though unlikely across collections)
            if job_id in all_jobs_map:
                return

            # Count variants for this job
            variant_count = db.db.resume_variants.count_documents({"job_id": job["_id"]}) # db.db accesses pymongo db directly
            
            # Get best score if variants exist
            best_score = 0
            if variant_count > 0:
                best_variant = db.db.resume_variants.find_one(
                    {"job_id": job["_id"]},
                    sort=[("ats_score", -1)]
                )
                best_score = best_variant.get("ats_score", 0) if best_variant else 0
            
            # Normalize fields
            title = job.get("cargo") or job.get("title") or "Unknown"
            company = job.get("empresa") or job.get("company") or "Unknown"
            
            # Handle date
            created_at = job.get("createdAt") or job.get("extracted_at")
            
            # Ensure it's a datetime object
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            # If datetime, ensure timezone awareness (Assume UTC if naive)
            if isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    from datetime import timezone
                    created_at = created_at.replace(tzinfo=timezone.utc)
            
            all_jobs_map[job_id] = {
                "job_id": job_id,
                "job_title": title,
                "company": company,
                "created_at": created_at.isoformat() if created_at else None,
                "_sort_date": created_at or datetime.min.replace(tzinfo=timezone.utc), # Internal sort key
                "variants_count": variant_count,
                "best_score": round(best_score, 1) if best_score else 0,
                "status": "completed" if variant_count > 0 else "no_cvs",
                "has_cvs": variant_count > 0,
                "source": source_collection
            }

        # Process both sources
        for job in resume_jobs_cursor:
            process_job(job, "manual_resume")
            
        for job in aggregator_jobs_cursor:
            process_job(job, "aggr_scraper")
            
        # Convert to list
        history = list(all_jobs_map.values())
        
        # Sort by date descending (using the datetime object)
        history.sort(key=lambda x: x["_sort_date"], reverse=True)
        
        # Remove internal sort key
        for h in history:
            h.pop("_sort_date", None)
        
        return history
    
    except Exception as e:
        logger.error(f"Failed to fetch resume history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time generation updates"""
    logger.info(f"Checking WS connection for job_id: {job_id}")
    await websocket.accept()
    active_connections[job_id] = websocket
    logger.info(f"WS Connected. active_connections keys: {list(active_connections.keys())}")
    
    # Send test message
    await websocket.send_json({"type": "info", "message": "Connected to Resume Generator"})
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {job_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        if job_id in active_connections:
            del active_connections[job_id]
        logger.info(f"WS Cleaned up for {job_id}")
