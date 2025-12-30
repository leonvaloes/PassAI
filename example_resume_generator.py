"""
Resume Generator - Exemplo de Uso End-to-End

Este script demonstra o fluxo completo do sistema
"""
import sys
sys.path.append('backend')

from modules.resume.job_extractor import JobExtractor
from modules.resume.ats_detector import ATSDetector
from modules.resume.variant_generator import VariantGenerator
from modules.resume.ats_simulator import ATSSimulator
from modules.resume.ranker import Ranker
# from modules.resume.knowledge_base import KnowledgeBase  # Disabled - ChromaDB not installed
from modules.resume.template_engine import TemplateEngine
from modules.resume.learning_engine import LearningEngine
from modules.resume.llm_adapter import create_llm_for_resume  # Adapter
from core.ai.vision_processor import VisionProcessor
from database.mongodb import get_mongodb
import yaml


def main():
    print("="*60)
    print("🚀 PassAI Resume Generator - Exemplo de Uso")
    print("="*60)
    
    # ====================================
    # 1. SETUP
    # ====================================
    print("\n📦 Inicializando componentes...")
    
    # Load config
    with open('backend/config/resume_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)['resume']
    
    # Initialize components
    llm_router = create_llm_for_resume()  # Adapter for compatibility
    vision_processor = VisionProcessor()
    db = get_mongodb()
    
    ats_detector = ATSDetector()
    
    # KnowledgeBase disabled (ChromaDB not installed - Python 3.14 incompatible)
    # knowledge_base = KnowledgeBase(
    #     chroma_path=config['chroma_path'],
    #     embedding_model=config['embedding_model']
    # )
    knowledge_base = None  # System works without RAG
    
    ats_simulator = ATSSimulator(ats_detector)
    ranker = Ranker(config)
    template_engine = TemplateEngine(config['template_path'])
    learning_engine = LearningEngine(ranker)
    
    job_extractor = JobExtractor(
        vision_processor=vision_processor,
        llm_router=llm_router
    )
    
    variant_generator = VariantGenerator(
        llm_router=llm_router,
        knowledge_base=knowledge_base,  # Can be None
        ats_simulator=ats_simulator,
        config=config
    )
    
    print("✅ Componentes inicializados!")
    
    # ====================================
    # 2. EXTRAIR VAGA
    # ====================================
    print("\n" + "="*60)
    print("📋 PASSO 1: Extrair Dados da Vaga")
    print("="*60)
    
    # Exemplo com texto
    vaga_texto = """
    Backend Developer - Nubank
    
    Estamos buscando um(a) Desenvolvedor(a) Backend Sênior para 
    integrar nosso time de Payments.
    
    Requisitos:
    - Python (Django/FastAPI)
    - PostgreSQL
    - AWS
    - Docker
    - 5+ anos de experiência
    
    Local: São Paulo - SP (Remoto)
    Salário: R$ 15.000 - R$ 20.000
    """
    
    job = job_extractor.extract({
        "type": "text",
        "content": vaga_texto
    })
    
    # Save job to MongoDB to get ID
    job_id = db.insert_job(job.dict(by_alias=True, exclude={'id'}))
    job.id = job_id
    
    print(f"✅ Vaga extraída:")
    print(f"   Cargo: {job.cargo}")
    print(f"   Empresa: {job.empresa}")
    print(f"   ATS: {job.ats_detectado.value}")
    print(f"   Requisitos: {', '.join(job.requisitos_tecnicos[:5])}")
    
    # ====================================
    # 3. CURRÍCULO BASE
    # ====================================
    print("\n" + "="*60)
    print("👤 PASSO 2: Currículo Base do Candidato")
    print("="*60)
    
    base_resume = {
        "nome": "Leonardo Valões",
        "email": "leo@passai.dev",
        "telefone": "(18) 99745-0885",
        "linkedin": "linkedin.com/leonardo-valoes",
        "github": "github.com/leonvaloes",
        "resumo": "Desenvolvedor Backend com experiência em Python e AWS",
        "experiencias": [
            {
                "empresa": "Tech Corp",
                "cargo": "Backend Developer",
                "periodo": "2020 - 2023",
                "descricao": "Desenvolvimento de APIs"
            }
        ],
        "habilidades": ["Python", "Django", "PostgreSQL", "Docker", "AWS"],
        "educacao": {
            "curso": "Sistemas de Informação",
            "instituicao": "Unoeste",
            "periodo": "2022 - 2026"
        }
    }
    
    print(f"✅ Currículo base carregado: {base_resume['nome']}")
    
    # ====================================
    # 4. GERAR VARIANTES
    # ====================================
    print("\n" + "="*60)
    print("🔄 PASSO 3: Gerar Variantes Otimizadas")
    print("="*60)
    
    # Callback para progresso
    def progress_callback(round_num, variants, approved):
        print(f"  Round {round_num}: {len(variants)} geradas, {approved} aprovadas")
    
    variants = variant_generator.generate_variants(
        job=job,
        base_resume=base_resume,
        template_path=config['template_path'],
        callback=progress_callback
    )
    
    print(f"\n✅ {len(variants)} variantes geradas!")
    
    # ====================================
    # 5. RANKEAR
    # ====================================
    print("\n" + "="*60)
    print("📊 PASSO 4: Rankear Variantes")
    print("="*60)
    
    ranked = ranker.rank(variants, job)
    top3 = ranked[:3]
    
    print("\n🏆 TOP 3 CURRÍCULOS:")
    for i, variant in enumerate(top3):
        print(f"\n  #{i+1}")
        print(f"    ATS Score:     {variant.ats_score:.1f}/100")
        print(f"    Ranking Score: {variant.ranking_score:.1f}/100")
        print(f"    Status:        {variant.ats_status.value}")
        print(f"    Motivos:       {', '.join(variant.motivos[:2])}")
    
    # ====================================
    # 6. PREENCHER TEMPLATE
    # ====================================
    print("\n" + "="*60)
    print("📝 PASSO 5: Preencher Template DOCX")
    print("="*60)
    
    best_variant = top3[0]
    
    output_path = "output/curriculo_otimizado.docx"
    result = template_engine.fill_template(
        content=best_variant.content,
        output_path=output_path
    )
    
    if result['success']:
        print(f"✅ Template preenchido: {output_path}")
        print(f"   Layout preservado: {result['layout_preserved']}")
        if result['warnings']:
            print(f"   Avisos: {', '.join(result['warnings'])}")
    else:
        print(f"❌ Erro: {result.get('error')}")
    
    # ====================================
    # 7. LEARNING
    # ====================================
    print("\n" + "="*60)
    print("🧠 PASSO 6: Learning (Simulado)")
    print("="*60)
    
    # Simular que usuário escolheu o melhor
    learning_engine.record_decision(
        variant_id=str(best_variant.id),
        action="chosen",
        feedback="Perfeito para a vaga!"
    )
    
    insights = learning_engine.get_insights()
    print(f"✅ Decisão registrada")
    print(f"   Total de decisões: {insights['total_decisions']}")
    
    # ====================================
    # RESUMO FINAL
    # ====================================
    print("\n" + "="*60)
    print("✅ PROCESSO COMPLETO!")
    print("="*60)
    
    print(f"""
    📊 Resumo:
    - Vaga: {job.cargo} @ {job.empresa}
    - ATS: {job.ats_detectado.value}
    - Variantes geradas: {len(variants)}
    - Aprovadas (≥95): {len([v for v in variants if v.ats_status.value == 'APPROVED'])}
    - Melhor score: {best_variant.ats_score:.1f}
    - Output: {output_path}
    
    🎉 Sistema funcionando perfeitamente!
    """)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
