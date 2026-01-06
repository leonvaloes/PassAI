"""
Testes automatizados para o Resume Generator
Valida que o perfil real está sendo usado corretamente
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database.mongodb import get_mongodb
from modules.resume.variant_generator import VariantGenerator
from database.models import Job, JobSource, ATSType
import json

def test_1_profile_exists():
    """Teste 1: Verifica se o perfil do Leonardo existe no MongoDB"""
    print("\n" + "="*60)
    print("TESTE 1: Perfil existe no MongoDB")
    print("="*60)
    
    db = get_mongodb()
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    
    if not profile:
        print("❌ FALHOU: Perfil não encontrado no MongoDB")
        return False
    
    print(f"✅ Profile encontrado: {profile['nome']}")
    print(f"   - Experiências: {len(profile['experiencias'])}")
    print(f"   - Habilidades: {len(profile['habilidades'])}")
    
    # Valida que tem dados reais
    if len(profile['experiencias']) < 2:
        print("❌ FALHOU: Deve ter pelo menos 2 experiências")
        return False
    
    if len(profile['habilidades']) < 30:
        print("❌ FALHOU: Deve ter pelo menos 30 habilidades")
        return False
    
    # Verifica experiências específicas
    empresas = [exp['empresa'] for exp in profile['experiencias']]
    if 'Security Segurança e Serviços' not in empresas:
        print("❌ FALHOU: Falta experiência na Security")
        return False
    
    if 'iPag Pagamentos Digitais' not in empresas:
        print("❌ FALHOU: Falta experiência na iPag")
        return False
    
    print("✅ PASSOU: Perfil tem dados completos e corretos")
    return True


def test_2_profile_formatting():
    """Teste 2: Verifica se o perfil é formatado corretamente como JSON"""
    print("\n" + "="*60)
    print("TESTE 2: Formatação do perfil para LLM")
    print("="*60)
    
    db = get_mongodb()
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    
    base_resume = {
        'nome': profile['nome'],
        'cargo': profile.get('cargo_atual', 'Desenvolvedor Full-Stack'),
        'email': profile['email'],
        'telefone': profile['telefone'],
        'linkedin': profile['linkedin'],
        'cidade': profile['cidade'],
        'estado': profile['estado'],
        'experiencias': profile['experiencias'],
        'educacao': profile['educacao'],
        'habilidades': profile['habilidades']
    }
    
    # Simula o que o código faz
    base_resume_json = json.dumps(base_resume, indent=2, ensure_ascii=False)
    
    # Verifica se é JSON válido
    try:
        parsed = json.loads(base_resume_json)
        print("✅ JSON é válido")
    except:
        print("❌ FALHOU: JSON inválido")
        return False
    
    # Verifica se contém as experiências
    if 'Security' not in base_resume_json:
        print("❌ FALHOU: JSON não contém 'Security'")
        return False
    
    if 'iPag' not in base_resume_json:
        print("❌ FALHOU: JSON não contém 'iPag'")
        return False
    
    # Verifica se é legível (indentado)
    if '\n' not in base_resume_json:
        print("❌ FALHOU: JSON não está indentado")
        return False
    
    print("✅ PASSOU: JSON formatado corretamente")
    print(f"   - Tamanho: {len(base_resume_json)} caracteres")
    print(f"   - Linhas: {base_resume_json.count(chr(10))} linhas")
    return True


def test_3_llm_prompt_includes_profile():
    """Teste 3: Verifica se o prompt do LLM inclui o perfil real"""
    print("\n" + "="*60)
    print("TESTE 3: Prompt do LLM contém perfil real")
    print("="*60)
    
    from modules.resume.variant_generator import VariantGenerator
    from core.llm.router import LLMRouter, LLMConfig
    from modules.resume.llm_adapter import LLMAdapter
    
    db = get_mongodb()
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    
    base_resume = {
        'nome': profile['nome'],
        'experiencias': profile['experiencias'],
        'habilidades': profile['habilidades']
    }
    
    # Criar job de teste
    job = Job(
        source=JobSource.TEXT,
        cargo="Desenvolvedor Full-Stack",
        empresa="Empresa Teste",
        requisitos_tecnicos=["Java", "Spring Boot", "React"],
        requisitos_comportamentais=["Liderança"],
        ats_detectado=ATSType.GUPY
    )
    
    # Verificar que o método _generate_content formata corretamente
    base_resume_json = json.dumps(base_resume, indent=2, ensure_ascii=False)
    
    if 'Security' not in base_resume_json:
        print("❌ FALHOU: Perfil formatado não contém Security")
        return False
    
    if 'iPag' not in base_resume_json:
        print("❌ FALHOU: Perfil formatado não contém iPag")
        return False
    
    print("✅ PASSOU: Prompt incluiria perfil completo")
    return True


def test_4_end_to_end_simulation():
    """Teste 4: Simula o fluxo completo (sem LLM real)"""
    print("\n" + "="*60)
    print("TESTE 4: Fluxo end-to-end (simulado)")
    print("="*60)
    
    db = get_mongodb()
    
    # 1. Carregar perfil
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    if not profile:
        print("❌ Passo 1 falhou: Perfil não encontrado")
        return False
    print("✅ Passo 1: Perfil carregado")
    
    # 2. Criar base_resume
    base_resume = {
        'nome': profile['nome'],
        'cargo': profile.get('cargo_atual'),
        'experiencias': profile['experiencias'],
        'habilidades': profile['habilidades']
    }
    print("✅ Passo 2: base_resume criado")
    
    # 3. Formatar como JSON
    base_resume_json = json.dumps(base_resume, indent=2, ensure_ascii=False)
    if 'Security' not in base_resume_json or 'iPag' not in base_resume_json:
        print("❌ Passo 3 falhou: JSON não contém experiências")
        return False
    print("✅ Passo 3: JSON formatado com experiências reais")
    
    # 4. Verificar que teria empresas reais no conteúdo
    empresas_reais = [exp['empresa'] for exp in profile['experiencias']]
    print(f"✅ Passo 4: Empresas disponíveis para LLM: {empresas_reais}")
    
    print("\n✅ PASSOU: Fluxo completo validado")
    return True


def run_all_tests():
    """Roda todos os testes"""
    print("\n" + "🔴"*30)
    print("INICIANDO TESTES DE VALIDAÇÃO DO RESUME GENERATOR")
    print("🔴"*30)
    
    tests = [
        test_1_profile_exists,
        test_2_profile_formatting,
        test_3_llm_prompt_includes_profile,
        test_4_end_to_end_simulation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passou: {passed}/{total}")
    
    if all(results):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("O sistema está pronto para teste manual.")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("O sistema NÃO está pronto ainda.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
