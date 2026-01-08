"""
MongoDB Client for PassAI
"""
import logging
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson import ObjectId

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "passai"):
        """
        Initialize MongoDB client
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        
    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✅ MongoDB connected: {self.db_name}")
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        # Jobs
        self.db.jobs.create_index("empresa")
        self.db.jobs.create_index("extracted_at")
        
        # Variants
        self.db.variants.create_index("job_id")
        self.db.variants.create_index([("ats_score", -1)])  # Descending
        self.db.variants.create_index([("ranking_score", -1)])
        
        # Decisions
        self.db.decisions.create_index("variant_id")
        self.db.decisions.create_index("timestamp")
        
        # ATS Patterns
        self.db.ats_patterns.create_index("empresa", unique=True)
        
        # Knowledge chunks
        self.db.kb_chunks.create_index("source")
        self.db.kb_chunks.create_index("ats_type")
        
        logger.info("✅ Database indexes created")
    
    # Collection accessors
    @property
    def jobs(self) -> Collection:
        return self.db.jobs
    
    @property
    def variants(self) -> Collection:
        return self.db.variants
    
    @property
    def decisions(self) -> Collection:
        return self.db.decisions
    
    @property
    def ats_patterns(self) -> Collection:
        return self.db.ats_patterns
    
    @property
    def kb_chunks(self) -> Collection:
        return self.db.kb_chunks
    
    # Helper methods
    def insert_job(self, job: Dict[str, Any]) -> ObjectId:
        """Insert a job posting"""
        result = self.jobs.insert_one(job)
        return result.inserted_id
    
    def insert_variant(self, variant: Dict[str, Any]) -> ObjectId:
        """Insert a resume variant"""
        result = self.variants.insert_one(variant)
        return result.inserted_id
    
    def get_job(self, job_id: Any) -> Optional[Dict]:
        """Get job by ID"""
        logger.info(f"MongoDB get_job called with: {job_id} (type: {type(job_id)})")
        if isinstance(job_id, str):
            try:
                job_id = ObjectId(job_id)
            except Exception as e:
                logger.error(f"ObjectId conversion failed for {job_id}: {e}")
                return None
        
        result = self.jobs.find_one({"_id": job_id})
        logger.info(f"MongoDB get_job result for {job_id}: {'Found' if result else 'None'}")
        return result
    
    def get_variants_by_job(self, job_id: Any) -> List[Dict]:
        """Get all variants for a job"""
        if isinstance(job_id, str):
            try:
                job_id = ObjectId(job_id)
            except:
                return []
        return list(self.variants.find({"job_id": job_id}).sort("ranking_score", -1))
    
    def get_top_variants(self, job_id: Any, limit: int = 3) -> List[Dict]:
        """Get top N variants by ranking score"""
        if isinstance(job_id, str):
            try:
                job_id = ObjectId(job_id)
            except:
                return []
        return list(
            self.variants.find({"job_id": job_id, "ats_status": "APPROVED"})
            .sort("ranking_score", -1)
            .limit(limit)
        )
    
    def get_variant(self, variant_id: Any) -> Optional[Dict]:
        """Get variant by ID"""
        if isinstance(variant_id, str):
            try:
                variant_id = ObjectId(variant_id)
            except:
                return None
        return self.variants.find_one({"_id": variant_id})

    def delete_job(self, job_id: Any) -> bool:
        """
        Delete a job and all associated variants
        
        Args:
            job_id: ID of the job to delete
            
        Returns:
            bool: True if deletions occurred
        """
        if isinstance(job_id, str):
            try:
                job_id = ObjectId(job_id)
            except Exception as e:
                logger.error(f"ObjectId conversion failed for {job_id}: {e}")
                return False
                
        # 1. Delete Job
        job_result = self.jobs.delete_one({"_id": job_id})
        
        # 2. Delete Variants
        variants_result = self.variants.delete_many({"job_id": job_id})
        
        # 3. Delete Decisions (optional, if linked)
        # self.decisions.delete_many(...)
        
        logger.info(f"Deleted Job {job_id}: {job_result.deleted_count} jobs, {variants_result.deleted_count} variants")
        
        return job_result.deleted_count > 0

    def record_decision(self, variant_id: Any, action: str, feedback: Optional[str] = None):
        """Record user decision"""
        if isinstance(variant_id, str):
            variant_id = ObjectId(variant_id)
            
        self.decisions.insert_one({
            "variant_id": variant_id,
            "action": action,
            "feedback": feedback,
            "timestamp": datetime.now()
        })
    
    def get_ats_pattern(self, empresa: str) -> Optional[Dict]:
        """Get learned ATS pattern for company"""
        return self.ats_patterns.find_one({"empresa": empresa})
    
    def update_ats_pattern(self, empresa: str, ats_type: str):
        """Update/create ATS pattern for company"""
        from datetime import datetime
        
        self.ats_patterns.update_one(
            {"empresa": empresa},
            {
                "$set": {
                    "ats_type": ats_type,
                    "last_confirmed": datetime.now()
                },
                "$inc": {"confirmed_count": 1}
            },
            upsert=True
        )


# Global singleton
_mongodb_instance: Optional[MongoDB] = None


def get_mongodb() -> MongoDB:
    """Get or create MongoDB singleton instance"""
    global _mongodb_instance
    
    if _mongodb_instance is None:
        _mongodb_instance = MongoDB()
        _mongodb_instance.connect()
    
    return _mongodb_instance
