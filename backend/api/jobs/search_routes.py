"""
Job Search API - Profile Management Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from modules.jobs.models import (
    SearchProfile, CreateProfileRequest, UpdateProfileRequest,
    ProfileResponse, RunSearchRequest, CrawlRunResponse,
    SearchFilters, ScheduleConfig
)
from modules.jobs.database import JobsDatabase
from modules.jobs.search_engine import create_search_engine
from database.mongodb import get_mongodb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["job-search"])

# Global instances
jobs_db: Optional[JobsDatabase] = None
search_engine = None


def init_search_system():
    """Initialize search profile system"""
    global jobs_db, search_engine
    
    from modules.resume.llm_adapter import create_llm_for_resume
    
    mongodb = get_mongodb()
    jobs_db = JobsDatabase(mongodb)
    
    # Create search engine
    llm_router = create_llm_for_resume()
    search_engine = create_search_engine(jobs_db, llm_router)
    
    logger.info("✅ Job search profiles system initialized")


# ==================== SEARCH PROFILES ====================

@router.post("/profiles", response_model=ProfileResponse)
async def create_search_profile(request: CreateProfileRequest):
    """Create a new search profile"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        # Create profile
        profile = SearchProfile(
            name=request.name,
            filters=request.filters,
            schedule=request.schedule,
            maxJobsPerRun=request.maxJobsPerRun
        )
        
        profile_id = jobs_db.create_profile(profile)
        created = jobs_db.get_profile(profile_id)
        
        return ProfileResponse(
            id=profile_id,
            name=created["name"],
            filters=SearchFilters(**created["filters"]),
            schedule=ScheduleConfig(**created.get("schedule", {})) if created.get("schedule") else None,
            maxJobsPerRun=created["maxJobsPerRun"],
            isActive=created["isActive"],
            createdAt=created["createdAt"],
            updatedAt=created["updatedAt"]
        )
    
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=List[ProfileResponse])
async def list_search_profiles(
    active_only: bool = Query(False, description="Filter active profiles only")
):
    """List all search profiles"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        profiles = jobs_db.list_profiles(active_only=active_only)
        
        return [
            ProfileResponse(
                id=p["_id"],
                name=p["name"],
                filters=SearchFilters(**p["filters"]),
                schedule=ScheduleConfig(**p.get("schedule", {})) if p.get("schedule") else None,
                maxJobsPerRun=p["maxJobsPerRun"],
                isActive=p["isActive"],
                createdAt=p["createdAt"],
                updatedAt=p["updatedAt"]
            )
            for p in profiles
        ]
    
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_search_profile(profile_id: str):
    """Get profile by ID"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        profile = jobs_db.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return ProfileResponse(
            id=profile["_id"],
            name=profile["name"],
            filters=SearchFilters(**profile["filters"]),
            schedule=ScheduleConfig(**profile.get("schedule", {})) if profile.get("schedule") else None,
            maxJobsPerRun=profile["maxJobsPerRun"],
            isActive=profile["isActive"],
            createdAt=profile["createdAt"],
            updatedAt=profile["updatedAt"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_search_profile(profile_id: str, request: UpdateProfileRequest):
    """Update search profile"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        # Build updates dict
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.filters is not None:
            updates["filters"] = request.filters.dict()
        if request.schedule is not None:
            updates["schedule"] = request.schedule.dict()
        if request.maxJobsPerRun is not None:
            updates["maxJobsPerRun"] = request.maxJobsPerRun
        if request.isActive is not None:
            updates["isActive"] = request.isActive
        
        # Update
        updated = jobs_db.update_profile(profile_id, updates)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get updated profile
        profile = jobs_db.get_profile(profile_id)
        
        return ProfileResponse(
            id=profile["_id"],
            name=profile["name"],
            filters=SearchFilters(**profile["filters"]),
            schedule=ScheduleConfig(**profile.get("schedule", {})) if profile.get("schedule") else None,
            maxJobsPerRun=profile["maxJobsPerRun"],
            isActive=profile["isActive"],
            createdAt=profile["createdAt"],
            updatedAt=profile["updatedAt"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{profile_id}")
async def delete_search_profile(profile_id: str):
    """Delete search profile"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        deleted = jobs_db.delete_profile(profile_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"status": "deleted", "profile_id": profile_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEARCH EXECUTION ====================

@router.post("/search/run", response_model=CrawlRunResponse)
async def run_search(request: RunSearchRequest):
    """Execute search for a profile"""
    try:
        if not jobs_db or not search_engine:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        # Get profile
        profile_dict = jobs_db.get_profile(request.profileId)
        
        if not profile_dict:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Convert to SearchProfile
        profile = SearchProfile(
            name=profile_dict["name"],
            filters=SearchFilters(**profile_dict["filters"]),
            schedule=ScheduleConfig(**profile_dict.get("schedule", {})) if profile_dict.get("schedule") else None,
            maxJobsPerRun=profile_dict["maxJobsPerRun"]
        )
        
        # Execute search
        run_id = search_engine.execute_search(profile, request.sources)
        
        # Get run details
        run = jobs_db.get_crawl_run(run_id)
        
        return CrawlRunResponse(
            id=run_id,
            profileName=run["profileName"],
            status=run["status"],
            stats=run["stats"],
            startedAt=run["startedAt"],
            finishedAt=run.get("finishedAt"),
            errors=run.get("errors", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/runs", response_model=List[CrawlRunResponse])
async def list_crawl_runs(
    profile_id: Optional[str] = Query(None, description="Filter by profile ID"),
    limit: int = Query(20, le=100)
):
    """List crawl runs"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        runs = jobs_db.list_crawl_runs(profile_id=profile_id, limit=limit)
        
        return [
            CrawlRunResponse(
                id=r["_id"],
                profileName=r["profileName"],
                status=r["status"],
                stats=r["stats"],
                startedAt=r["startedAt"],
                finishedAt=r.get("finishedAt"),
                errors=r.get("errors", [])
            )
            for r in runs
        ]
    
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/runs/{run_id}", response_model=CrawlRunResponse)
async def get_crawl_run(run_id: str):
    """Get crawl run details"""
    try:
        if not jobs_db:
            raise HTTPException(status_code=503, detail="Search system not initialized")
        
        run = jobs_db.get_crawl_run(run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail="Crawl run not found")
        
        return CrawlRunResponse(
            id=run["_id"],
            profileName=run["profileName"],
            status=run["status"],
            stats=run["stats"],
            startedAt=run["startedAt"],
            finishedAt=run.get("finishedAt"),
            errors=run.get("errors", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
