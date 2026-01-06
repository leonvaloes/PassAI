"""
Fix Search Profiles - Add country field to existing profiles
"""
from database.mongodb import MongoDB

def fix_profiles():
    """Add country: Brazil to all profiles missing it"""
    
    db = MongoDB()
    db.connect()
    
    profiles_collection = db.db['job_search_profiles']
    
    # Find all profiles
    profiles = list(profiles_collection.find({}))
    
    print(f"Found {len(profiles)} profiles")
    
    fixed = 0
    for profile in profiles:
        # Check if location exists and doesn't have country
        if 'filters' in profile and 'location' in profile['filters']:
            location = profile['filters']['location']
            if location and 'country' not in location:
                # Add Brazil as default
                print(f"Fixing profile: {profile.get('name')}")
                print(f"  Before: {location}")
                
                location['country'] = 'Brazil'
                
                # Update in database
                profiles_collection.update_one(
                    {'_id': profile['_id']},
                    {'$set': {'filters.location.country': 'Brazil'}}
                )
                
                print(f"  After: {location}")
                fixed += 1
    
    print(f"\n✅ Fixed {fixed} profiles")
    
    # Show all profiles now
    print("\n--- Updated Profiles ---")
    profiles = list(profiles_collection.find({}))
    for p in profiles:
        print(f"\nProfile: {p.get('name')}")
        loc = p.get('filters', {}).get('location', {})
        print(f"  Location: {loc}")

if __name__ == '__main__':
    fix_profiles()
