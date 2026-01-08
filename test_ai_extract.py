import requests
import json

# Read CV text
with open('test_cv.txt', 'r', encoding='utf-8') as f:
    cv_text = f.read()

print(f"Testing AI extraction with {len(cv_text)} characters...")
print("=" * 60)

# Call API
response = requests.post(
    'http://localhost:8000/api/users/ai-extract',
    json={'text': cv_text},
    timeout=60
)

print(f"Status: {response.status_code}")
print("=" * 60)

if response.status_code == 200:
    data = response.json()
    print("✅ SUCCESS!")
    print(f"\nExperiências: {len(data.get('experiencias', []))}")
    for exp in data.get('experiencias', []):
        print(f"  - {exp.get('empresa')} ({exp.get('periodo')})")
    
    print(f"\nEducação: {len(data.get('educacao', []))}")
    for edu in data.get('educacao', []):
        print(f"  - {edu.get('curso')} - {edu.get('instituicao')}")
    
    print(f"\nHabilidades: {len(data.get('habilidades', []))}")
    print(f"  {', '.join(data.get('habilidades', [])[:10])}")
    
    print(f"\nIdiomas: {len(data.get('idiomas', []))}")
else:
    print("❌ ERROR!")
    print(response.text)
