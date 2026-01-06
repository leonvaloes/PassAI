"""
Job Aggregator API - Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from modules.jobs.models import (
    JobPosting, CreateJobRequest, ScrapeJobRequest, JobResponse,
    JobStatus, Location
)
from modules.jobs.database import JobsDatabase
from modules.jobs.job_scorer import JobScorer
from core.llm.router import LLMRouter
from database.mongodb import get_mongodb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Global instances
jobs_db: Optional[JobsDatabase] = None
job_scorer: Optional[JobScorer] = None


def init_jobs_system():
    """Initialize job aggregator system"""
    global jobs_db, job_scorer
    
    mongodb = get_mongodb()
    jobs_db = JobsDatabase(mongodb)
    
    # Initialize scorer with LLM
    llm_router = LLMRouter()
    job_scorer = JobScorer(llm_router)
    
    logger.info("✅ Job aggregator system initialized")


@router.post("/create", response_model=JobResponse)
async def create_job_manual(request: CreateJobRequest):
    """Create job manually from form data"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        # Create JobPosting from request
        job = JobPosting(
            url=request.url or f"manual://{request.company}/{request.title}",
            title=request.title,
            company=request.company,
            description=request.description,
            location=request.location,
            salaryExplicit=request.salary,
            extractionMethod="manual"
        )
        
        # Save to MongoDB
        job_id = jobs_db.create_job(job)
        
        # Get created job
        created_job = jobs_db.get_job(job_id)
        
        return JobResponse(
            id=job_id,
            url=created_job["url"],
            title=created_job.get("title"),
            company=created_job.get("company"),
            location=created_job.get("location"),
            salary=created_job.get("salaryExplicit"),
            rankingScore=created_job.get("rankingScore"),
            createdAt=created_job["createdAt"]
        )
    
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape", response_model=JobResponse)
async def scrape_job_from_url(request: ScrapeJobRequest):
    """Extract job data from URL"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        # Import scrapers (lazy load to register them)
        from modules.jobs.scrapers import linkedin, gupy
        from modules.jobs.scraper import ScraperRegistry
        from modules.jobs.enricher import enrich_job_with_ai
        from modules.resume.llm_adapter import create_llm_for_resume
        
        # Get appropriate scraper
        scraper = ScraperRegistry.get_scraper(str(request.url))
        
        if not scraper:
            raise HTTPException(
                status_code=400,
                detail=f"No scraper available for this URL. Supported domains: {ScraperRegistry.list_domains()}"
            )
        
        # Scrape job data
        scraped_data = scraper.extract_job_data(str(request.url))
        
        if "error" in scraped_data:
            raise HTTPException(status_code=500, detail=scraped_data["error"])
        
        # Enrich with AI
        llm_router = create_llm_for_resume()
        enriched_data = enrich_job_with_ai(scraped_data, llm_router)
        
        # Create JobPosting model
        job = JobPosting(
            url=request.url,
            title=enriched_data.get('title'),
            company=enriched_data.get('company'),
            description=enriched_data.get('description'),
            location=enriched_data.get('location'),
            salaryExplicit=enriched_data.get('salary'),
            techKeywords=enriched_data.get('techKeywords', []),
            seniority=enriched_data.get('seniority'),
            mustHave=enriched_data.get('mustHave', []),
            niceToHave=enriched_data.get('niceToHave', []),
            rawHtml=enriched_data.get('rawHtml'),
            rawText=enriched_data.get('rawText'),
            extractionMethod="scrape",
            extractionConfidence={
                "title": 0.9 if enriched_data.get('title') else 0.0,
                "company": 0.9 if enriched_data.get('company') else 0.0,
                "description": 0.8 if enriched_data.get('description') else 0.0
            }
        )
        
        # Save to MongoDB
        job_id = jobs_db.create_job(job)
        created_job = jobs_db.get_job(job_id)
        
        return JobResponse(
            id=job_id,
            url=created_job["url"],
            title=created_job.get("title"),
            company=created_job.get("company"),
            location=created_job.get("location"),
            salary=created_job.get("salaryExplicit"),
            rankingScore=created_job.get("rankingScore"),
            createdAt=created_job["createdAt"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scrape job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0)
):
    """List all jobs with pagination"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        jobs = jobs_db.list_jobs(
            status=status,
            limit=limit,
            skip=skip,
            sort_by="createdAt",
            sort_order=-1
        )
        
        return [
            JobResponse(
                id=job["_id"],
                url=job["url"],
                title=job.get("title"),
                company=job.get("company"),
                location=job.get("location"),
                salary=job.get("salaryExplicit"),
                rankingScore=job.get("rankingScore"),
                createdAt=job["createdAt"]
            )
            for job in jobs
        ]
    
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranked")
async def get_ranked_jobs(
    user_id: str = Query(default="leonardo", description="User ID for profile matching"),
    limit: int = Query(default=50, ge=1, le=500)
):
    """
    Get jobs ranked by AI compatibility score
    
    Returns jobs sorted by how well they match the user's profile,
    with scores and reasons included.
    """
    try:
        if not jobs_db or not job_scorer:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        # Get all jobs
        all_jobs = jobs_db.list_jobs(limit=limit)
        
        # Get user profile (simplified - in production would fetch from profiles DB)
        user_profile = {
            'skills': ['React', 'Node.js', 'Python', 'TypeScript', 'MongoDB', 'Docker', 'AWS'],
            'seniority': 'pleno',
            'experience_years': 3,
            'summary': 'Full-stack developer with 3 years experience in React/Node.js'
        }
        
        # Score each job
        ranked_jobs = []
        for job in all_jobs:
            try:
                # Convert job to dict if needed
                job_dict = job if isinstance(job, dict) else job.dict()
                
                # Check if job already has a stored score (from manual Analysis)
                stored_score = job_dict.get('score')
                
                if stored_score:
                    # Use stored score
                    ranked_job = {
                        **job_dict,
                        '_id': str(job_dict.get('_id', '')),
                        'score': stored_score
                    }
                else:
                    # Calculate lightweight score (NO LLM)
                    # This is fast and safe for list view
                    score = job_scorer.score_job(job_dict, user_profile, use_llm=False)
                    
                    # Add score to job data
                    ranked_job = {
                        **job_dict,
                        '_id': str(job_dict.get('_id', '')),
                        'score': {
                            'overall': score.overall_score,
                            'skill_match_pct': score.skill_match_pct,
                            'matched_skills': score.matched_skills,
                            'missing_skills': score.missing_skills,
                            'seniority_match': score.seniority_match,
                            'salary_estimate': score.salary_estimate,
                            'match_reasons': score.match_reasons,
                            'concerns': score.concerns
                        }
                    }
                
                ranked_jobs.append(ranked_job)
                
            except Exception as e:
                logger.warning(f"Failed to score job {job.get('title', 'unknown')}: {e}")
                # Add job without score
                ranked_jobs.append({
                    **job_dict,
                    '_id': str(job_dict.get('_id', '')),
                    'score': None
                })
        
        # Sort by overall score (descending)
        ranked_jobs.sort(key=lambda j: j.get('score', {}).get('overall', 0) if j.get('score') else 0, reverse=True)
        
        return ranked_jobs
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ranked jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed job information"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        job = jobs_db.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job posting"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        deleted = jobs_db.delete_job(job_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"status": "deleted", "job_id": job_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/analyze")
async def analyze_job(
    job_id: str,
    user_id: str = Query(default="leonardo", description="User ID for profile matching")
):
    """
    Trigger on-demand AI analysis for a specific job
    """
    try:
        if not jobs_db or not job_scorer:
            raise HTTPException(status_code=503, detail="Jobs system not initialized")
        
        job = jobs_db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        # Enrich with AI first (if strictly needed, but scorer does analysis too)
        # We can call enricher here explicitly if we want better extraction
        from modules.jobs.enricher import enrich_job_with_ai
        from core.llm.router import LLMRouter
        
        # Re-enrich to ensure we have good data for scoring
        # (This is the heavy step we skipped in scraping)
        logger.info(f"Triggering on-demand enrichment for job {job_id}")
        llm_router = LLMRouter()
        enriched_data = enrich_job_with_ai(job, llm_router)
        
        # Update job with enriched data
        jobs_db.update_job(job_id, enriched_data)
        
        # Now Score
        # Get user profile (simplified)
        user_profile = {
            'skills': ['React', 'Node.js', 'Python', 'TypeScript', 'MongoDB', 'Docker', 'AWS'],
            'seniority': 'pleno',
            'experience_years': 3,
            'summary': 'Full-stack developer with 3 years experience in React/Node.js'
        }
        
        score = job_scorer.score_job(enriched_data, user_profile)
        
        # Update job with score
        score_data = {
            'rankingScore': score.overall_score,
            'score': {
                'overall': score.overall_score,
                'skill_match_pct': score.skill_match_pct,
                'matched_skills': score.matched_skills,
                'missing_skills': score.missing_skills,
                'seniority_match': score.seniority_match,
                'salary_estimate': score.salary_estimate,
                'match_reasons': score.match_reasons,
                'concerns': score.concerns
            }
        }
        jobs_db.update_job(job_id, score_data)
        
        return {
            "status": "success",
            "job_id": job_id,
            "score": score_data['score']
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
