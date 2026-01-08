from database.mongodb import get_mongodb
from bson import ObjectId

# Initialize DB
db = get_mongodb()

# Check how many variants exist
variant_count = db.db.resume_variants.count_documents({})
print(f"Total variants in DB: {variant_count}")

# Get a sample variant to see structure
sample = db.db.resume_variants.find_one()
if sample:
    print(f"\nSample variant structure:")
    print(f"  _id: {sample.get('_id')}")
    print(f"  job_id: {sample.get('job_id')} (type: {type(sample.get('job_id'))})")
    print(f"  ats_score: {sample.get('ats_score')}")
    print(f"  created_at: {sample.get('created_at')}")
    
    # Try to find the job for this variant
    job_id = sample.get('job_id')
    if job_id:
        job = db.db.jobs.find_one({"_id": job_id})
        if job:
            print(f"\n✅ Found job in 'jobs' collection:")
            print(f"  Title: {job.get('cargo') or job.get('title')}")
            print(f"  Company: {job.get('empresa') or job.get('company')}")
        else:
            print(f"\n❌ Job NOT found in 'jobs' collection, trying 'job_postings'...")
            job = db.db.job_postings.find_one({"_id": job_id})
            if job:
                print(f"  ✅ Found in 'job_postings'")
                print(f"  Title: {job.get('title')}")
                print(f"  Company: {job.get('company')}")
            else:
                print(f"  ❌ Job NOT found anywhere!")

# Test the aggregation pipeline
print("\n\nTesting aggregation pipeline:")
pipeline = [
    {
        "$group": {
            "_id": "$job_id",
            "variant_count": {"$sum": 1},
            "best_score": {"$max": "$ats_score"},
            "latest_created": {"$max": "$created_at"}
        }
    },
    {"$sort": {"latest_created": -1}}
]

results = list(db.db.resume_variants.aggregate(pipeline))
print(f"Aggregation returned {len(results)} results")
for i, r in enumerate(results[:3]):
    print(f"\n  Result {i+1}:")
    print(f"    job_id: {r.get('_id')}")
    print(f"    variant_count: {r.get('variant_count')}")
    print(f"    best_score: {r.get('best_score')}")
