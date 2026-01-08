import logging
import asyncio
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from bson import ObjectId
from backend.database.mongodb import get_mongodb
from backend.modules.jobs.database import JobsDatabase
from backend.modules.jobs.enricher import AIJobEnricher, enrich_job_with_ai
from backend.core.llm.router import LLMRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_job():
    db = get_mongodb()
    
    job_id = "695c0f3e06165c8efa0f8e8f"
    try:
        oid = ObjectId(job_id)
    except:
        print(f"Invalid ID: {job_id}")
        return

    print(f"--- Debugging Job {job_id} ---")

    # 1. Check 'jobs' collection (Resume DB)
    resume_job = db.jobs.find_one({"_id": oid})
    print(f"1. Found in 'jobs' collection? {'YES' if resume_job else 'NO'}")
    if resume_job:
        print(f"   requisitos_tecnicos: {resume_job.get('requisitos_tecnicos')}")
        # Delete it to force flush
        db.jobs.delete_one({"_id": oid})
        print("   -> DELETED from 'jobs' collection to force fresh fetch.")

    # 2. Check 'job_postings' collection (Scraper DB)
    scraper_job = db.db.job_postings.find_one({"_id": oid})
    print(f"2. Found in 'job_postings' collection? {'YES' if scraper_job else 'NO'}")
    
    if scraper_job:
        print(f"   techKeywords: {scraper_job.get('techKeywords')}")
        print(f"   mustHave: {scraper_job.get('mustHave')}")
        print(f"   description length: {len(scraper_job.get('description', '') or scraper_job.get('rawText', '') or '')}")
        
        # 3. Test Adapter Logic
        tech_kw = scraper_job.get("techKeywords", []) or []
        must_have = scraper_job.get("mustHave", []) or []
        reqs = tech_kw + must_have
        print(f"   -> Adapted Requirements Count: {len(reqs)}")
        
        # 4. Test Enrichment if empty
        if not reqs:
            print("   -> Requirements EMPTY. Testing Enrichment...")
            llm = LLMRouter()
            enricher = AIJobEnricher(llm)
            
            # Prepare payload
            payload = {
                'rawText': scraper_job.get('rawText') or scraper_job.get('description'),
                'description': scraper_job.get('description')
            }
            
            try:
                enriched = enricher.enrich_job(payload)
                print(f"   -> Enricher Result: {enriched.keys()}")
                print(f"   -> Keywords: {enriched.get('techKeywords')}")
            except Exception as e:
                print(f"   -> Enrichment FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(debug_job())
