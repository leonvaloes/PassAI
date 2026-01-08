"""
Test Multi-User API Endpoints
Run this to verify the multi-user system is working correctly
"""
import requests
import json

API_BASE = "http://localhost:8000/api/users"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_list_users():
    print_section("1. LIST ALL USERS")
    response = requests.get(API_BASE)
    data = response.json()
    
    print(f"Total users: {data['total']}")
    print(f"Active user ID: {data['active_user_id']}")
    
    for user in data['users']:
        print(f"\n  - {user['nome']} ({user['profile_name']})")
        print(f"    ID: {user['id']}")
        print(f"    Email: {user['email']}")
        print(f"    Cargo: {user['cargo_atual']}")
    
    return data

def test_create_user():
    print_section("2. CREATE NEW USER")
    
    new_user = {
        "profile_name": "maria_silva",
        "nome": "Maria Silva Santos",
        "email": "maria.silva@exemplo.com",
        "telefone": "(11) 98765-4321",
        "linkedin": "linkedin.com/maria-silva",
        "github": "github.com/mariasilva",
        "cidade": "Rio de Janeiro",
        "estado": "Rio de Janeiro",
        "cargo_atual": "Desenvolvedora Backend Pleno",
        "experiencias": [],
        "educacao": [],
        "habilidades": ["Python", "Django", "PostgreSQL", "Docker"],
        "idiomas": []
    }
    
    response = requests.post(API_BASE, json=new_user)
    
    if response.status_code == 201:
        user = response.json()
        print(f"✅ User created successfully!")
        print(f"   ID: {user['id']}")
        print(f"   Nome: {user['nome']}")
        return user['id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.json())
        return None

def test_get_user(user_id):
    print_section(f"3. GET USER BY ID")
    
    response = requests.get(f"{API_BASE}/{user_id}")
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User found:")
        print(f"   Nome: {user['nome']}")
        print(f"   Email: {user['email']}")
        print(f"   Cargo: {user['cargo_atual']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_update_user(user_id):
    print_section("4. UPDATE USER")
    
    update_data = {
        "cargo_atual": "Desenvolvedora Backend Sênior"
    }
    
    response = requests.put(f"{API_BASE}/{user_id}", json=update_data)
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User updated successfully!")
        print(f"   New cargo: {user['cargo_atual']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_set_active_user(user_id):
    print_section("5. SET ACTIVE USER")
    
    response = requests.put(f"{API_BASE}/active/set", json={"user_id": user_id})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_get_active_user():
    print_section("6. GET ACTIVE USER")
    
    response = requests.get(f"{API_BASE}/active/current")
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Active user:")
        print(f"   Nome: {user['nome']}")
        print(f"   Email: {user['email']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_delete_user(user_id):
    print_section("7. DELETE USER")
    
    response = requests.delete(f"{API_BASE}/{user_id}")
    
    if response.status_code == 204:
        print(f"✅ User deleted successfully!")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    print("\n🧪 TESTING MULTI-USER API")
    print("Make sure the backend server is running on http://localhost:8000")
    
    try:
        # 1. List existing users
        initial_data = test_list_users()
        
        # 2. Create a new user
        new_user_id = test_create_user()
        
        if new_user_id:
            # 3. Get the new user
            test_get_user(new_user_id)
            
            # 4. Update the user
            test_update_user(new_user_id)
            
            # 5. Set as active user
            test_set_active_user(new_user_id)
            
            # 6. Get active user
            test_get_active_user()
            
            # 7. Delete the user
            test_delete_user(new_user_id)
        
        # Final list
        test_list_users()
        
        print_section("✅ ALL TESTS COMPLETED")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend server!")
        print("Make sure the server is running: cd backend && python -m uvicorn server:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
