
import sys
import os
from pathlib import Path
import logging
from bson import ObjectId

# Add backend to path
backend_dir = os.path.join(os.getcwd(), 'backend')
sys.path.insert(0, backend_dir)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database.mongodb import get_mongodb

def diagnose():
    logger.info("Starting DB diagnosis...")
    
    try:
        db = get_mongodb()
        logger.info(f"Connected to DB: {db.db_name}")
        
        # Test Insert
        job_data = {
            "cargo": "Test Job",
            "empresa": "Test Corp",
            "content": "Test Content",
            "source": "manual_check"
        }
        
        logger.info("Inserting test job...")
        job_id = db.insert_job(job_data)
        logger.info(f"Inserted ID: {job_id} ({type(job_id)})")
        
        if isinstance(job_id, ObjectId):
            logger.info("ID is ObjectId (Correct)")
        else:
            logger.error(f"ID is NOT ObjectId: {type(job_id)}")

        # Test Retrieval with ObjectId
        logger.info("Retrieving with ObjectId...")
        doc1 = db.get_job(job_id)
        if doc1:
            logger.info("✅ Found with ObjectId")
        else:
            logger.error("❌ Not found with ObjectId")
            
        # Test Retrieval with String
        str_id = str(job_id)
        logger.info(f"Retrieving with String: {str_id}")
        doc2 = db.get_job(str_id)
        if doc2:
            logger.info("✅ Found with String (Conversion worked)")
        else:
            logger.error("❌ Not found with String (Conversion failed)")

        # Cleanup
        db.jobs.delete_one({"_id": job_id})
        logger.info("Diagnosis complete.")
        
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}", exc_info=True)

if __name__ == "__main__":
    diagnose()
