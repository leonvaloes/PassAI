"""
Populate Leonardo's User Profile with Real Data
Run this once to store professional history in MongoDB
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.mongodb import get_mongodb

# Leonardo's REAL professional data
leonardo_profile = {
    "profile_name": "Leonardo",
    "nome": "Leonardo Valões Novaes Ribeiro",
    "email": "leonvaloesnovaes@gmail.com",
    "telefone": "(18) 99745-0885",
    "linkedin": "linkedin.com/leonardo-valoes-ribeiro",
    "github": "github.com/leonvaloes",
    "cidade": "Presidente Prudente",
    "estado": "São Paulo",
    "cargo_atual": "Desenvolvedor Full-Stack",
    
    "experiencias": [
        {
            "empresa": "Security Segurança e Serviços",
            "cargo": "Desenvolvedor Full-Stack",
            "periodo": "Maio de 2022 - Maio de 2024",
            "descricao": "Experiência no desenvolvimento e manutenção de automação de processos corporativos. Responsável desde o levantamento de requisitos até a entrega e melhorias contínuas.",
            "tecnologias": ["Java", "Spring Boot", "C#", "HTML5", "CSS3", "Bootstrap", "jQuery", "Fluig", "RabbitMQ", "Kafka", "Workers", "Oracle", "MySQL", "MongoDB", "ERP Protheus", "Microsserviços", "Clean Architecture", "DDD", "Ollama", "Llama"],
            "realizacoes": [
                "Alteração funcional e salarial: sistema para solicitações de mudança de cargo e/ou salário. Contemplava diferentes rotas de aprovação conforme o perfil do colaborador (administrativo ou operacional), passando por instâncias como Controladoria, Gestão de Pessoas, Diretoria Financeira, Presidência e Mesa Operacional. Incluía geração automática de registros administrativos e notificações aos responsáveis em cada etapa, integração com notificações via e-mail, integração com microsserviços e ERP Protheus.",
                "Rescisão contratual em lote: sistema para desligamento de diversos colaboradores de forma simultânea, muito comum em encerramento de postos de serviço. Automatizou processos de demissão, aprovações, geração de documentos e integração com o ERP Protheus.",
                "Efetivação de contratos: sistema para controle do ciclo de efetivação contratual, com upload de documentos (planilhas de preço, propostas, minutas), validação por múltiplos departamentos (jurídico, financeiro, DHO, supply chain, etc.), gestão de aprovações/reprovações com justificativa, reenvio automático para ajustes, notificações via e-mail e integração com microsserviços.",
                "Admissão de colaboradores: sistema para gestão do processo de contratação, incluindo aprovações, geração de documentos e integrações com ERP Protheus e Pandapé."
            ]
        },
        {
            "empresa": "iPag Pagamentos Digitais",
            "cargo": "Desenvolvedor Full-Stack",
            "periodo": "Maio 2024 – Dezembro 2024",
            "descricao": "Experiência no desenvolvimento e manutenção de soluções de pagamento, atuando na criação de um Gateway de Pagamento que suportava transações via cartão de crédito, boleto e PIX, com integração a lojas virtuais, aplicativos, ERPs e outros sistemas. Implementação de funcionalidades como links de pagamento, cobranças recorrentes e suporte a empresas interessadas em se tornarem whitelabel, possuindo sua própria fintech.",
            "tecnologias": ["Java", "Spring Boot", "React", "Gatsby", "NextJs", "Angular", "Tailwind", "RabbitMQ", "Kafka", "Workers", "MySQL", "MongoDB", "DDD", "Microsserviços"],
            "realizacoes": [
                 "Desenvolvimento do site principal do iPag: criação do site principal com SEO otimizado e performance 70% superior em relação ao site anterior, aumentando visibilidade online e vendas.",
                 "Sistema de multiusuários: desenvolvimento de solução que permitia que um usuário autorizado acessasse contas de outros usuários, garantindo que fintechs whitelabel pudessem gerenciar subfintechs com integridade e segurança de dados.",
                 "Gestão de ciclo completo: participação em todo o processo, do levantamento de requisitos, modelagem de dados, desenvolvimento de front-end e back-end, até testes, deploy e monitoramento contínuo."
            ]
        }
    ],
    
    "educacao": [
        {
            "instituicao": "Sistemas de informação – Unoeste",
            "curso": "Bacharelado em Sistemas de Informação",
            "periodo": "Jan/2022 – Dez 2026"
        }
    ],
    
    "habilidades": [
        "Java", "Spring Boot", "C#", ".NET",
        "React", "Angular", "NextJs", "Gatsby", "Vue.js",
        "HTML5", "CSS3", "Bootstrap", "Tailwind", "jQuery",
        "JavaScript", "TypeScript",
        "RabbitMQ", "Kafka", "Workers",
        "MySQL", "MongoDB", "Oracle", "PostgreSQL",
        "Docker", "Kubernetes",
        "Microsserviços", "DDD", "Clean Architecture",
        "Git", "GitHub", "GitLab",
        "Fluig", "ERP Protheus",
        "REST API", "GraphQL",
        "Ollama", "Llama", "IA", "Machine Learning",
        "SEO", "Performance Optimization",
        "Agile", "Scrum"
    ],
    
    "idiomas": [
        {"idioma": "Português", "nivel": "Nativo"},
        {"idioma": "Inglês", "nivel": "Intermediário"}
    ]
}

if __name__ == "__main__":
    db = get_mongodb()
    
    # Upsert profile (create or update)
    result = db.db.user_profiles.update_one(
        {"profile_name": "Leonardo"},
        {"$set": leonardo_profile},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"✅ Profile created: {result.upserted_id}")
    else:
        print(f"✅ Profile updated: {result.matched_count} document(s)")
    
    # Verify
    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    if profile:
        print(f"\n📋 Profile Summary:")
        print(f"   Nome: {profile['nome']}")
        print(f"   Experiências: {len(profile['experiencias'])}")
        print(f"   Habilidades: {len(profile['habilidades'])}")
        print(f"   Educação: {len(profile['educacao'])}")
        print("\n✅ Profile ready to use!")
    else:
        print("❌ Profile not found after insert")
