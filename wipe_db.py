from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def wipe_data():
    try:
        # Connect to local MongoDB (standard port 27017 exposed by Docker)
        client = MongoClient("mongodb://localhost:27017/")
        db = client["passai"]
        
        collections = ["jobs", "job_postings", "variants", "decisions", "ats_patterns"]
        
        logger.info("Starting database wipe...")
        
        for col_name in collections:
            count = db[col_name].count_documents({})
            if count > 0:
                db[col_name].drop()
                logger.info(f"✅ Dropped collection '{col_name}' ({count} documents removed)")
            else:
                logger.info(f"ℹ️ Collection '{col_name}' was already empty")
                
        logger.info("Database wipe complete! System is clean.")
        
    except Exception as e:
        logger.error(f"❌ Failed to wipe database: {e}")

if __name__ == "__main__":
    wipe_data()
