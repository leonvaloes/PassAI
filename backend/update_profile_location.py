"""
Update existing profile with proper location
"""
from database.mongodb import MongoDB

db = MongoDB()
db.connect()

profiles_collection = db.db['job_search_profiles']

# Update the existing profile
result = profiles_collection.update_one(
    {},  # First profile
    {
        '$set': {
            'filters.location': {
                'city': None,
                'state': None,
                'country': 'Brazil',
                'remote': True
            }
        }
    }
)

print(f"✅ Updated {result.modified_count} profile(s)")

# Verify
profile = profiles_collection.find_one()
print(f"\nUpdated profile location: {profile['filters']['location']}")
