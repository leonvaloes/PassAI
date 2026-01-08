import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.mongodb import get_mongodb
import asyncio
from datetime import datetime

def list_jobs():
    db = get_mongodb()
    # Mocking connection since get_mongodb is synchronous but we want to use the property
    # Actually get_mongodb connects synchronously.
    
    print("--- JOBS Collection ---")
    for job in db.db.jobs.find().sort("created_at", -1).limit(5):
        print(f"ID: {job.get('_id')} | Title: {job.get('title')} | Created: {job.get('created_at')}")

    print("\n--- JOB POSTINGS Collection (Scraped) ---")
    for job in db.db.job_postings.find().sort("createdAt", -1).limit(5):
        print(f"ID: {job.get('_id')} | Title: {job.get('title')} | Created: {job.get('createdAt')}")

if __name__ == "__main__":
    list_jobs()
