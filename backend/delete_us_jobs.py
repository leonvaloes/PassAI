"""
Delete US jobs from MongoDB
"""
from database.mongodb import MongoDB

db = MongoDB()
db.connect()

# Delete jobs where location.city contains "Estados Unidos"
result = db.db['job_postings'].delete_many({
    'location.city': {'$regex': 'Estados Unidos', '$options': 'i'}
})

print(f'✅ Deleted {result.deleted_count} US jobs')

# Show remaining jobs
remaining = db.db['job_postings'].count_documents({})
print(f'📊 Remaining jobs: {remaining}')

# Show Brazilian jobs
brazil_jobs = db.db['job_postings'].count_documents({
    '$or': [
        {'location.country': 'Brazil'},
        {'location.country': 'Brasil'}
    ]
})
print(f'🇧🇷 Brazilian jobs: {brazil_jobs}')
