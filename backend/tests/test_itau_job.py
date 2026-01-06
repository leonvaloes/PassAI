"""
Teste end-to-end REAL com a vaga do Itaú
Valida que o currículo gerado contém dados reais (não genéricos)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database.mongodb import get_mongodb
from modules.resume.variant_generator import VariantGenerator
from modules.resume.ats_simulator import ATSSimulator
from modules.resume.ranker import Ranker
from modules.resume.llm_adapter import create_llm_for_resume
from database.models import Job, JobSource, ATSType
import json
import yaml

def test_real_itau_job():
    """Teste com vaga real do Itaú"""
    print("\n" + "="*70)
    print("TESTE E2E: Vaga Real do Itaú - Engenheiro de Software PL")
    print("="*70)
    
    # 1. Carregar configuração
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'resume_config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)['resume']
    
    # 2. Criar job baseado na vaga real do Itaú
    job = Job(
        source=JobSource.TEXT,
        cargo="Engenheiro de Software PL",
        empresa="Itaú Unibanco",
        local="São Paulo - SP",
        modalidade="Híbrido",
        senioridade="Pleno",
        salario=None,
        beneficios=[
            "Vale-Transporte", "Vale-Refeição", "Plano médico", 
            "PLR", "Previdência privada", "Wellhub"
        ],
        requisitos_tecnicos=[
            "Java", "Go", "TypeScript", "AWS", "Design Patterns", 
            "SOLID", "12factor", "Observabilidade", "Banco de dados",
            "Back-end", "Front-end", "Microserviços", "Kafka", "RabbitMQ"
        ],
        requisitos_comportamentais=[
            "Gestão de Projetos Ágil", "Liderança", "Trabalho em equipe",
            "Inovação", "Diversidade"
        ],
        ats_detectado=ATSType.GUPY
    )
    
    print(f"✅ Job criado: {job.cargo} at {job.empresa}")
    print(f"   - Requisitos técnicos: {len(job.requisitos_tecnicos)}")
    
    # 3. Carregar perfil real do Leonardo
    db = get_mongodb()
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    
    if not profile:
        print("❌ ERRO: Perfil não encontrado!")
        return False
    
    print(f"✅ Perfil carregado: {profile['nome']}")
    print(f"   - Experiências: {len(profile['experiencias'])}")
    
    # 4. Criar base_resume
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
    
    # 5. Inicializar componentes
    print("\n📋 Inicializando componentes...")
    llm_router = create_llm_for_resume()
    ats_simulator = ATSSimulator(None)
    
    variant_generator = VariantGenerator(
        llm_router=llm_router,
        knowledge_base=None,
        ats_simulator=ats_simulator,
        config=config
    )
    
    print("✅ Componentes inicializados")
    
    # 6. Gerar UMA variante (rápido para teste)
    print("\n🚀 Gerando variante...")
    print("⏳ Isso pode demorar ~30 segundos...")
    
    try:
        content = variant_generator._generate_content(
            job=job,
            base_resume=base_resume,
            rag_context="",
            temperature=0.7,
            seed=42
        )
        
        print("\n✅ Variante gerada com sucesso!")
        
        # 7. VALIDAR CONTEÚDO
        print("\n" + "="*70)
        print("VALIDAÇÃO DO CONTEÚDO GERADO")
        print("="*70)
        
        issues = []
        
        # Verifica se tem habilidades reais
        if 'habilidades' in content:
            habilidades_str = str(content['habilidades'])
            
            # Deve ter pelo menos algumas das habilidades reais
            real_skills = ['Java', 'Spring Boot', 'React', 'MongoDB', 'RabbitMQ']
            found_skills = [skill for skill in real_skills if skill in habilidades_str]
            
            if len(found_skills) >= 3:
                print(f"✅ Habilidades reais encontradas: {found_skills}")
            else:
                issues.append(f"❌ Poucas habilidades reais encontradas: {found_skills}")
                print(issues[-1])
        else:
            issues.append("❌ Campo 'habilidades' não encontrado")
            print(issues[-1])
        
        # Verifica experiências
        if 'experiencias' in content:
            exp_str = json.dumps(content['experiencias'], ensure_ascii=False)
            
            # Verifica se menciona empresas reais
            if 'Security' in exp_str or 'iPag' in exp_str:
                print("✅ Experiências reais encontradas (Security ou iPag)")
            else:
                issues.append("❌ Experiências NÃO mencionam Security nem iPag")
                print(issues[-1])
                print(f"   Experiências geradas: {exp_str[:200]}...")
        else:
            issues.append("❌ Campo 'experiencias' não encontrado")
            print(issues[-1])
        
        # Verifica resumo
        if 'resumo_linha_1' in content or 'resumo' in content:
            resumo = content.get('resumo_linha_1', '') + content.get('resumo_linha_2', '') + content.get('resumo', '')
            
            if 'xxxx' in resumo.lower() or 'placeholder' in resumo.lower():
                issues.append("❌ Resumo contém placeholders (xxxx)")
                print(issues[-1])
            else:
                print(f"✅ Resumo parece real: {resumo[:100]}...")
        
        # Mostra conteúdo completo
        print("\n" + "="*70)
        print("CONTEÚDO COMPLETO GERADO:")
        print("="*70)
        print(json.dumps(content, indent=2, ensure_ascii=False)[:2000])
        print("...")
        
        # Resultado final
        print("\n" + "="*70)
        print("RESULTADO FINAL")
        print("="*70)
        
        if len(issues) == 0:
            print("🎉 SUCESSO! Currículo gerado com dados REAIS!")
            print("   - Habilidades reais: ✅")
            print("   - Experiências reais: ✅")
            print("   - Sem placeholders: ✅")
            return True
        else:
            print("❌ FALHOU! Problemas encontrados:")
            for issue in issues:
                print(f"   {issue}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO durante geração: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_real_itau_job()
    sys.exit(0 if success else 1)
