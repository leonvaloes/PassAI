"""
Test Script - Search Profiles API
Tests the job search profiles implementation
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/jobs"


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_create_profile():
    """Test: Create search profile"""
    print_section("1. Creating Search Profile")
    
    profile_data = {
        "name": "Backend Node Pleno Remote SP",
        "filters": {
            "title": "Backend Developer",
            "seniority": "pleno",
            "stack": ["Node.js", "TypeScript", "AWS", "Docker"],
            "modality": "remote",
            "location": {
                "city": "São Paulo",
                "state": "SP",
                "country": "Brazil"
            },
            "minSalary": 8000,
            "language": "PT-BR"
        },
        "maxJobsPerRun": 50
    }
    
    response = requests.post(
        f"{API_BASE}/profiles",
        json=profile_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile created!")
        print(f"   ID: {profile['id']}")
        print(f"   Name: {profile['name']}")
        print(f"   Stack: {', '.join(profile['filters']['stack'])}")
        return profile['id']
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_list_profiles():
    """Test: List all profiles"""
    print_section("2. Listing All Profiles")
    
    response = requests.get(f"{API_BASE}/profiles")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profiles = response.json()
        print(f"✅ Found {len(profiles)} profile(s)")
        
        for profile in profiles:
            print(f"\n   - {profile['name']}")
            print(f"     ID: {profile['id']}")
            print(f"     Active: {profile['isActive']}")
            print(f"     Max Jobs: {profile['maxJobsPerRun']}")
    else:
        print(f"❌ Failed: {response.text}")


def test_get_profile(profile_id):
    """Test: Get profile by ID"""
    print_section("3. Getting Profile Details")
    
    response = requests.get(f"{API_BASE}/profiles/{profile_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile retrieved!")
        print(f"   Name: {profile['name']}")
        print(f"   Filters:")
        print(f"     - Title: {profile['filters'].get('title', 'N/A')}")
        print(f"     - Seniority: {profile['filters'].get('seniority', 'N/A')}")
        print(f"     - Stack: {', '.join(profile['filters'].get('stack', []))}")
        print(f"     - Location: {profile['filters']['location'].get('city', 'N/A')}")
    else:
        print(f"❌ Failed: {response.text}")


def test_update_profile(profile_id):
    """Test: Update profile"""
    print_section("4. Updating Profile")
    
    updates = {
        "maxJobsPerRun": 100,
        "filters": {
            "title": "Senior Backend Developer",
            "seniority": "senior",
            "stack": ["Node.js", "TypeScript", "AWS", "Kubernetes"],
            "modality": "remote",
            "location": {
                "city": "São Paulo",
                "state": "SP",
                "country": "Brazil"
            },
            "minSalary": 12000
        }
    }
    
    response = requests.put(
        f"{API_BASE}/profiles/{profile_id}",
        json=updates,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile updated!")
        print(f"   Max Jobs: {profile['maxJobsPerRun']}")
        print(f"   Title: {profile['filters']['title']}")
        print(f"   Seniority: {profile['filters']['seniority']}")
    else:
        print(f"❌ Failed: {response.text}")


def test_run_search(profile_id):
    """Test: Execute search"""
    print_section("5. Running Search (This may take time)")
    
    search_request = {
        "profileId": profile_id,
        "sources": ["linkedin", "gupy"]
    }
    
    print("⏳ Executing search...")
    print("(Note: This is a placeholder - actual search not fully implemented yet)")
    
    response = requests.post(
        f"{API_BASE}/search/run",
        json=search_request,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        run = response.json()
        print(f"✅ Search executed!")
        print(f"   Run ID: {run['id']}")
        print(f"   Profile: {run['profileName']}")
        print(f"   Status: {run['status']}")
        print(f"   Jobs Found: {run['stats']['jobsFound']}")
        print(f"   Jobs New: {run['stats']['jobsNew']}")
        print(f"   Jobs Failed: {run['stats']['jobsFailed']}")
        return run['id']
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_list_runs():
    """Test: List crawl runs"""
    print_section("6. Listing Crawl Runs")
    
    response = requests.get(f"{API_BASE}/search/runs")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        runs = response.json()
        print(f"✅ Found {len(runs)} run(s)")
        
        for run in runs:
            print(f"\n   - {run['profileName']}")
            print(f"     Status: {run['status']}")
            print(f"     Jobs: {run['stats']['jobsNew']} new, {run['stats']['jobsUpdated']} updated")
            print(f"     Started: {run['startedAt']}")
    else:
        print(f"❌ Failed: {response.text}")


def test_delete_profile(profile_id):
    """Test: Delete profile"""
    print_section("7. Deleting Profile")
    
    response = requests.delete(f"{API_BASE}/profiles/{profile_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Profile deleted!")
    else:
        print(f"❌ Failed: {response.text}")


def main():
    """Run all tests"""
    print(f"\n{'#'*60}")
    print(f"#  Search Profiles API - Test Suite")
    print(f"#  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    try:
        # Test flow
        profile_id = test_create_profile()
        
        if not profile_id:
            print("\n❌ Cannot continue - profile creation failed")
            return
        
        test_list_profiles()
        test_get_profile(profile_id)
        test_update_profile(profile_id)
        
        run_id = test_run_search(profile_id)
        
        if run_id:
            test_list_runs()
        
        # Cleanup
        test_delete_profile(profile_id)
        
        print_section("✅ All Tests Completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("   Make sure the backend is running: .\\start.bat")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
