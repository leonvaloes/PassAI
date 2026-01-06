"""
Show saved jobs from MongoDB
"""
from database.mongodb import MongoDB
import json

db = MongoDB()
db.connect()

jobs = list(db.db['job_postings'].find().limit(10))

print(f"\n📋 Found {len(jobs)} jobs:\n")

for i, job in enumerate(jobs, 1):
    print(f"{i}. {job.get('title', 'No title')}")
    print(f"   Company: {job.get('company', 'Unknown')}")
    print(f"   URL: {job.get('url', 'No URL')}")
    print(f"   Location: {job.get('location', {})}")
    print()
