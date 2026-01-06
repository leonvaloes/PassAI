"""
Job Aggregator - Database Operations
MongoDB CRUD for jobs system
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from modules.jobs.models import (
    JobPosting, JobSource, Connector, AuditLog,
    JobStatus, SearchProfile, CrawlRun, CrawlRunStatus
)

logger = logging.getLogger(__name__)


class JobsDatabase:
    """Database operations for job aggregator"""
    
    def __init__(self, mongodb):
        self.db = mongodb.db
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for collections"""
        # job_postings indexes
        self.db.job_postings.create_index("url", unique=True)
        self.db.job_postings.create_index("sourceId")
        self.db.job_postings.create_index("status")
        self.db.job_postings.create_index("rankingScore")
        self.db.job_postings.create_index([("createdAt", -1)])
        
        # connectors indexes
        self.db.connectors.create_index("domain", unique=True)
        self.db.connectors.create_index("isActive")
        
        # job_search_profiles indexes
        self.db.job_search_profiles.create_index("userId")
        self.db.job_search_profiles.create_index("isActive")
        self.db.job_search_profiles.create_index([("createdAt", -1)])
        
        # crawl_runs indexes
        self.db.crawl_runs.create_index("profileId")
        self.db.crawl_runs.create_index("status")
        self.db.crawl_runs.create_index([("startedAt", -1)])
        
        # audit_logs indexes
        self.db.audit_logs.create_index([("createdAt", -1)])
        self.db.audit_logs.create_index("entityType")
        
        logger.info("✅ Job aggregator indexes created")
    
    # ==================== JOB POSTINGS ====================
    
    def create_job(self, job: JobPosting) -> str:
        """Create new job posting"""
        job_dict = job.dict(by_alias=True, exclude_none=True)
        
        # Check if URL already exists (deduplication)
        existing = self.db.job_postings.find_one({"url": str(job.url)})
        
        if existing:
            # Update existing job
            logger.info(f"Job with URL {job.url} already exists, updating...")
            self.db.job_postings.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        **job_dict,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            self._log_audit(
                "job_posting",
                str(existing["_id"]),
                "info",
                f"Job updated: {job.url}",
                {"method": "deduplication"}
            )
            
            return str(existing["_id"])
        else:
            # Create new
            result = self.db.job_postings.insert_one(job_dict)
            job_id = str(result.inserted_id)
            
            self._log_audit(
                "job_posting",
                job_id,
                "info",
                f"Job created: {job.url}",
                {"method": "new"}
            )
            
            logger.info(f"✅ Job created: {job_id}")
            return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        try:
            result = self.db.job_postings.find_one({"_id": ObjectId(job_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    def get_job_by_url(self, url: str) -> Optional[Dict]:
        """Get job by URL"""
        result = self.db.job_postings.find_one({"url": url})
        if result:
            result["_id"] = str(result["_id"])
        return result
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "createdAt",
        sort_order: int = -1
    ) -> List[Dict]:
        """List jobs with filters"""
        query = {}
        if status:
            query["status"] = status.value
        
        cursor = self.db.job_postings.find(query)
        cursor = cursor.sort(sort_by, sort_order).skip(skip).limit(limit)
        
        jobs = []
        for job in cursor:
            job["_id"] = str(job["_id"])
            jobs.append(job)
        
        return jobs
    
    def update_job(self, job_id: str, updates: Dict) -> bool:
        """Update job fields"""
        try:
            updates["updatedAt"] = datetime.utcnow()
            result = self.db.job_postings.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                self._log_audit(
                    "job_posting",
                    job_id,
                    "info",
                    "Job updated",
                    {"fields": list(updates.keys())}
                )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job posting"""
        try:
            result = self.db.job_postings.delete_one({"_id": ObjectId(job_id)})
            
            if result.deleted_count > 0:
                self._log_audit(
                    "job_posting",
                    job_id,
                    "info",
                    "Job deleted",
                    {}
                )
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    # ==================== JOB SOURCES ====================
    
    def create_source(self, source: JobSource) -> str:
        """Create job source"""
        source_dict = source.dict(by_alias=True)
        result = self.db.job_sources.insert_one(source_dict)
        return str(result.inserted_id)
    
    def get_source_by_name(self, name: str) -> Optional[Dict]:
        """Get source by name"""
        result = self.db.job_sources.find_one({"name": name})
        if result:
            result["_id"] = str(result["_id"])
        return result
    
    def list_sources(self) -> List[Dict]:
        """List all job sources"""
        sources = []
        for source in self.db.job_sources.find():
            source["_id"] = str(source["_id"])
            sources.append(source)
        return sources
    
    # ==================== CONNECTORS ====================
    
    def create_connector(self, connector: Connector) -> str:
        """Create connector"""
        connector_dict = connector.dict(by_alias=True)
        
        # Check if domain already exists
        existing = self.db.connectors.find_one({"domain": connector.domain})
        if existing:
            logger.warning(f"Connector for {connector.domain} already exists")
            return str(existing["_id"])
        
        result = self.db.connectors.insert_one(connector_dict)
        connector_id = str(result.inserted_id)
        
        self._log_audit(
            "connector",
            connector_id,
            "info",
            f"Connector created for domain: {connector.domain}",
            {}
        )
        
        return connector_id
    
    def get_connector_by_domain(self, domain: str) -> Optional[Dict]:
        """Get connector by domain"""
        result = self.db.connectors.find_one({"domain": domain, "isActive": True})
        if result:
            result["_id"] = str(result["_id"])
        return result
    
    def list_connectors(self, active_only: bool = True) -> List[Dict]:
        """List connectors"""
        query = {"isActive": True} if active_only else {}
        connectors = []
        for conn in self.db.connectors.find(query):
            conn["_id"] = str(conn["_id"])
            connectors.append(conn)
        return connectors
    
    # ==================== SEARCH PROFILES ====================
    
    def create_profile(self, profile: SearchProfile) -> str:
        """Create search profile"""
        profile_dict = profile.dict(by_alias=True)
        result = self.db.job_search_profiles.insert_one(profile_dict)
        profile_id = str(result.inserted_id)
        
        self._log_audit(
            "search_profile",
            profile_id,
            "info",
            f"Profile created: {profile.name}",
            {}
        )
        
        logger.info(f"✅ Search profile created: {profile_id}")
        return profile_id
    
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Get profile by ID"""
        try:
            result = self.db.job_search_profiles.find_one({"_id": ObjectId(profile_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except Exception as e:
            logger.error(f"Error getting profile {profile_id}: {e}")
            return None
    
    def list_profiles(self, user_id: str = "leonardo", active_only: bool = False) -> List[Dict]:
        """List search profiles for user"""
        query = {"userId": user_id}
        if active_only:
            query["isActive"] = True
        
        profiles = []
        cursor = self.db.job_search_profiles.find(query).sort("createdAt", -1)
        for profile in cursor:
            profile["_id"] = str(profile["_id"])
            profiles.append(profile)
        
        return profiles
    
    def update_profile(self, profile_id: str, updates: Dict) -> bool:
        """Update profile"""
        try:
            updates["updatedAt"] = datetime.utcnow()
            result = self.db.job_search_profiles.update_one(
                {"_id": ObjectId(profile_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                self._log_audit(
                    "search_profile",
                    profile_id,
                    "info",
                    "Profile updated",
                    {"fields": list(updates.keys())}
                )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating profile {profile_id}: {e}")
            return False
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete search profile"""
        try:
            result = self.db.job_search_profiles.delete_one({"_id": ObjectId(profile_id)})
            
            if result.deleted_count > 0:
                self._log_audit(
                    "search_profile",
                    profile_id,
                    "info",
                    "Profile deleted",
                    {}
                )
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False
    
    # ==================== CRAWL RUNS ====================
    
    def create_crawl_run(self, crawl_run: CrawlRun) -> str:
        """Create crawl run record"""
        run_dict = crawl_run.dict(by_alias=True)
        result = self.db.crawl_runs.insert_one(run_dict)
        run_id = str(result.inserted_id)
        
        logger.info(f"✅ Crawl run created: {run_id}")
        return run_id
    
    def get_crawl_run(self, run_id: str) -> Optional[Dict]:
        """Get crawl run by ID"""
        try:
            result = self.db.crawl_runs.find_one({"_id": ObjectId(run_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except Exception as e:
            logger.error(f"Error getting crawl run {run_id}: {e}")
            return None
    
    def update_crawl_run(self, run_id: str, updates: Dict) -> bool:
        """Update crawl run"""
        try:
            result = self.db.crawl_runs.update_one(
                {"_id": ObjectId(run_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating crawl run {run_id}: {e}")
            return False
    
    def list_crawl_runs(
        self,
        profile_id: Optional[str] = None,
        status: Optional[CrawlRunStatus] = None,
        limit: int = 20
    ) -> List[Dict]:
        """List crawl runs"""
        query = {}
        if profile_id:
            query["profileId"] = profile_id
        if status:
            query["status"] = status.value
        
        runs = []
        cursor = self.db.crawl_runs.find(query).sort("startedAt", -1).limit(limit)
        for run in cursor:
            run["_id"] = str(run["_id"])
            runs.append(run)
        
        return runs
    
    # ==================== AUDIT LOGS ====================
    
    def _log_audit(
        self,
        entity_type: str,
        entity_id: str,
        level: str,
        message: str,
        payload: Dict[str, Any]
    ):
        """Internal audit logging"""
        log = AuditLog(
            entityType=entity_type,
            entityId=entity_id,
            level=level,
            message=message,
            payload=payload
        )
        self.db.audit_logs.insert_one(log.dict())
    
    def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit logs"""
        query = {}
        if entity_type:
            query["entityType"] = entity_type
        if entity_id:
            query["entityId"] = entity_id
        
        logs = []
        cursor = self.db.audit_logs.find(query).sort("createdAt", -1).limit(limit)
        for log in cursor:
            log["_id"] = str(log["_id"])
            logs.append(log)
        
        return logs
