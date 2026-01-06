"""
Delete San Francisco (US) jobs that were incorrectly saved as Brazil
"""
from database.mongodb import MongoDB

db = MongoDB()
db.connect()

# Delete jobs where location contains San Francisco indicators
result = db.db['job_postings'].delete_many({
    '$or': [
        {'location.city': {'$regex': 'São Francisco', '$options': 'i'}},
        {'location.city': {'$regex': 'San Francisco', '$options': 'i'}},
        {'location.city': {'$regex': 'Silicon Valley', '$options': 'i'}},
        {'location.state': {'$regex': 'California', '$options': 'i'}},
        {'location.state': {'$regex': 'Califórnia', '$options': 'i'}}
    ]
})

print(f'✅ Deleted {result.deleted_count} San Francisco/California jobs')

# Show remaining jobs with details
remaining = list(db.db['job_postings'].find())
print(f'\n📊 Remaining jobs: {len(remaining)}\n')

for job in remaining:
    loc = job.get('location', {})
    print(f"- {job.get('title')}")
    print(f"  Company: {job.get('company')}")
    print(f"  Location: {loc}")
    print()
