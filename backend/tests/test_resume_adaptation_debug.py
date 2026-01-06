
import sys
import os
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add backend directory to sys.path so we can import modules
# Assuming this script is in d:\p2\ai-copilot\backend\tests
# and we want to import from d:\p2\ai-copilot\backend
# Add backend directory to sys.path so we can import modules
# We need both root (for backend.x imports) AND backend/ (for internal imports like 'from database import...')
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, backend_dir)

# Now we can import as if we were at the root
from backend.modules.resume.variant_generator import VariantGenerator
from backend.database.models import Job, JobSource, ATSType
from backend.modules.resume.llm_adapter import LLMAdapter

# Mock classes
class MockLLMRouter:
    class MockConfig:
        ollama_base_url = "http://localhost:11434"
        ollama_model = "llama3.1:8b"
    config = MockConfig()

def test_debug_generation():
    print("🚀 Starting Debug Test...")
    
    # 1. Create Mock Job with Requirements
    job = Job(
        source=JobSource.TEXT,
        cargo="Engenheiro de Software Java",
        empresa="Banco Itaú",
        requisitos_tecnicos=["Java", "Spring Boot", "AWS", "Microserviços", "Kafka"],
        requisitos_comportamentais=["Liderança"],
        ats_detectado=ATSType.GUPY
    )
    
    # 2. Create Mock Profile
    base_resume = {
        "nome": "Leonardo Teste",
        "experiencias": [
            {
                "empresa": "Empresa Antiga",
                "cargo": "Dev Junior",
                "descricao": "Fiz manutenção de sistemas legados.",
                "bullets": ["Corrigi bugs em PHP.", "Atendi chamados de suporte."]
            }
        ],
        "habilidades": ["PHP", "MySQL"]
    }
    
    # 3. Initialize Generator
    llm_router = MockLLMRouter()
    adapter = LLMAdapter(llm_router)
    
    generator = VariantGenerator(
        llm_router=adapter,
        knowledge_base=None,
        ats_simulator=None,
        config={} # Config dict
    )
    
    # 4. Generate Content (calls LLM)
    print("\n⏳ Calling _generate_content (check logs for DEBUG)...")
    try:
        result = generator._generate_content(
            job=job,
            base_resume=base_resume,
            rag_context="",
            temperature=0.7,
            seed=42
        )
        print("\n✅ Generation Result Keys:", result.keys())
        print("📄 Generated Experiences:", result.get('experiencias'))
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_debug_generation()
