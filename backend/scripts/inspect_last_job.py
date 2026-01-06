
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database.mongodb import get_mongodb
from backend.database.models import Job

def inspect_last_job():
    print("🔍 Inspecting Last Job & Variants...")
    
    db = get_mongodb()
    
    # 1. Get last job
    last_job = db.db.jobs.find_one(sort=[('extracted_at', -1)])
    
    if not last_job:
        print("❌ No jobs found in database.")
        return

    print(f"\n📄 LAST JOB: {last_job.get('cargo')} at {last_job.get('empresa')}")
    print(f"   ID: {(last_job.get('_id'))}")
    print(f"   Date: {last_job.get('extracted_at')}")
    print(f"   Requirements: {last_job.get('requisitos_tecnicos')}")
    
    # 2. Get variants for this job
    variants = list(db.db.resume_variants.find({"job_id": str(last_job.get('_id'))}))
    
    print(f"\n📦 FOUND {len(variants)} VARIANTS:")
    
    for i, v in enumerate(variants):
        print(f"\n   --- VARIANT {i+1} (Score: {v.get('score', 'N/A')}) ---")
        content = v.get('content', {})
        
        # Show experiences to check adaptation
        exps = content.get('experiencias', [])
        print(f"   Experiências ({len(exps)}):")
        for exp in exps:
            print(f"     • {exp.get('cargo')} @ {exp.get('empresa')}")
            bullets = exp.get('bullets', [])
            for b in bullets:
                print(f"       - {b}")
                
        # Check specific keywords in bullets
        reqs = last_job.get('requisitos_tecnicos', [])
        found_keywords = 0
        all_bullets = " ".join([b for exp in exps for b in exp.get('bullets', [])]).lower()
        
        for req in reqs:
            if req.lower() in all_bullets:
                found_keywords += 1
                
        print(f"   ✅ Keywords found in bullets: {found_keywords}/{len(reqs)}")

if __name__ == "__main__":
    inspect_last_job()
