"""
Populate Leonardo's user profile with current professional history.
Run this once to store/update the profile in MongoDB.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.mongodb import get_mongodb


leonardo_profile = {
    "profile_name": "Leonardo",
    "nome": "Leonardo Valoes Novaes Ribeiro",
    "email": "leonvaloesnovaes@gmail.com",
    "telefone": "(18) 99745-0885",
    "linkedin": "linkedin.com/leonardo-valoes-ribeiro",
    "github": "github.com/leonvaloes",
    "cidade": "Presidente Prudente",
    "estado": "Sao Paulo",
    "cargo_atual": "Desenvolvedor Full-Stack",
    "experiencias": [
        {
            "empresa": "Security Seguranca e Servicos",
            "cargo": "Desenvolvedor Full-Stack",
            "periodo": "Janeiro de 2025 - Atual",
            "descricao": (
                "Recontratado para atuar novamente no desenvolvimento e manutencao "
                "de sistemas corporativos e automacoes de processos, com foco em "
                "integracoes, microsservicos, qualidade de codigo e evolucao de "
                "solucoes internas."
            ),
            "tecnologias": [
                "Java",
                "Spring Boot",
                "C#",
                "HTML5",
                "CSS3",
                "Bootstrap",
                "jQuery",
                "Fluig",
                "RabbitMQ",
                "Kafka",
                "Workers",
                "Oracle",
                "MySQL",
                "MongoDB",
                "PostgreSQL",
                "ERP Protheus",
                "Microsservicos",
                "Clean Architecture",
                "DDD",
                "SOLID",
                "GitHub Actions",
                "CI/CD",
                "Docker",
                "Kubernetes",
                "AWS",
            ],
            "realizacoes": [
                "Participacao ativa em duas auditorias, apoiando adequacoes tecnicas e operacionais para garantir conformidade com os criterios avaliados pelos auditores.",
                "Desenvolvimento de fluxos corporativos usados por diferentes areas da empresa, contribuindo para padronizacao de processos, reducao de retrabalho e ganho operacional.",
                "Desenvolvimento do fluxo de desligamento em massa de colaboradores para cenarios de encerramento de postos de servico, integrando microsservicos, ERP Protheus e sistemas internos para acelerar rotinas de RH.",
                "Evolucao de fluxos do ciclo de vida do colaborador, incluindo contratacao, admissao, alteracao de cargo, alteracao salarial, aprovacao, documentacao e integracoes com sistemas corporativos.",
                "Manutencao e melhoria de automacoes com rotas de aprovacao, notificacoes, rastreabilidade e integracoes entre sistemas.",
                "Apoio em refatoracao, analise de impacto e melhoria de qualidade usando praticas de arquitetura, SOLID e automacao de entrega.",
            ],
        },
        {
            "empresa": "iPag Pagamentos Digitais",
            "cargo": "Desenvolvedor Full-Stack",
            "periodo": "Maio de 2024 - Dezembro de 2024",
            "descricao": (
                "Experiencia no desenvolvimento e manutencao de solucoes de pagamento, "
                "atuando na criacao de um gateway de pagamento com cartao de credito, "
                "boleto e PIX, integracao com lojas virtuais, aplicativos, ERPs e outros sistemas."
            ),
            "tecnologias": [
                "Java",
                "Spring Boot",
                "Node.js",
                "React",
                "Gatsby",
                "NextJs",
                "Angular",
                "Tailwind",
                "RabbitMQ",
                "Kafka",
                "Workers",
                "MySQL",
                "MongoDB",
                "PostgreSQL",
                "DDD",
                "Microsservicos",
                "SOLID",
                "GitHub Actions",
                "CI/CD",
                "Docker",
                "AWS",
            ],
            "realizacoes": [
                "Implementacao de solucao para processamento de pagamentos em lote, substituindo uma rotina que levava horas por um processamento em minutos, com execucao assincrona e concorrente.",
                "Implementacao de solucao para calculo e cobranca escalonada baseada em regras configuraveis dinamicamente.",
                "Integracao TEF para ampliar as capacidades de pagamento e integracao do ecossistema iPag.",
                "Correcao de biblioteca open source de validacao para viabilizar o uso interno com maior confiabilidade.",
                "Implementacao de autenticacao 3DS no plugin iPag para Nuvemshop.",
                "Implementacao de esteira de CI/CD e configuracao de filas e scheduler cron na AWS para apoiar execucoes assicronas e entregas mais previsiveis.",
                "Desenvolvimento do site principal do iPag com SEO otimizado e performance 70% superior ao site anterior.",
                "Desenvolvimento de sistema multiusuario para fintechs whitelabel gerenciarem subfintechs com integridade e seguranca de dados.",
                "Participacao em levantamento de requisitos, modelagem de dados, front-end, back-end, testes, deploy e monitoramento continuo.",
                "Atuacao em APIs e integracoes para pagamentos digitais, incluindo cartao, boleto, PIX, recorrencia e conexoes com lojas virtuais, aplicativos e ERPs.",
            ],
        },
        {
            "empresa": "Security Seguranca e Servicos",
            "cargo": "Desenvolvedor Full-Stack",
            "periodo": "Maio de 2022 - Maio de 2024",
            "descricao": (
                "Primeira passagem na empresa, com experiencia no desenvolvimento e "
                "manutencao de automacoes de processos corporativos, desde o levantamento "
                "de requisitos ate entrega e melhorias continuas."
            ),
            "tecnologias": [
                "Java",
                "Spring Boot",
                "C#",
                "HTML5",
                "CSS3",
                "Bootstrap",
                "jQuery",
                "Fluig",
                "RabbitMQ",
                "Kafka",
                "Workers",
                "Oracle",
                "MySQL",
                "MongoDB",
                "PostgreSQL",
                "ERP Protheus",
                "Microsservicos",
                "Clean Architecture",
                "DDD",
                "SOLID",
                "GitHub Actions",
                "CI/CD",
                "Docker",
                "Kubernetes",
                "AWS",
            ],
            "realizacoes": [
                "Desenvolvimento de sistemas corporativos para o ciclo de vida do colaborador, cobrindo contratacao, admissao, efetivacao, alteracao de cargo, alteracao salarial e desligamento.",
                "Sistema de alteracao funcional e salarial com rotas de aprovacao, regras de negocio e integracao com ERP Protheus.",
                "Sistema de rescisao contratual em lote para desligamento simultaneo de colaboradores, apoiando cenarios operacionais de encerramento de postos de servico.",
                "Sistema de efetivacao de contratos com upload de documentos, validacao multi-area, notificacoes e trilha de aprovacao.",
                "Sistema de admissao de colaboradores com aprovacoes, geracao de documentos e integracoes com ERP Protheus e Pandape.",
                "Desenvolvimento de fluxos entre servicos, APIs e regras de negocio para reduzir trabalho manual, padronizar processos e aumentar rastreabilidade operacional.",
            ],
        },
    ],
    "educacao": [
        {
            "instituicao": "Unoeste",
            "curso": "Bacharelado em Sistemas de Informacao",
            "periodo": "Jan/2022 - Dez/2026",
        }
    ],
    "habilidades": [
        "Java",
        "Spring Boot",
        "C#",
        ".NET",
        "React",
        "Angular",
        "NextJs",
        "Gatsby",
        "Vue.js",
        "HTML5",
        "CSS3",
        "Bootstrap",
        "Tailwind",
        "jQuery",
        "JavaScript",
        "TypeScript",
        "Node.js",
        "RabbitMQ",
        "Kafka",
        "Workers",
        "MySQL",
        "MongoDB",
        "Oracle",
        "PostgreSQL",
        "Docker",
        "Kubernetes",
        "Microsservicos",
        "DDD",
        "Clean Architecture",
        "SOLID",
        "Design Patterns",
        "Git",
        "GitHub",
        "GitLab",
        "GitHub Actions",
        "CI/CD",
        "AWS",
        "Fluig",
        "ERP Protheus",
        "REST API",
        "GraphQL",
        "IA",
        "Machine Learning",
        "SEO",
        "Performance Optimization",
        "Agile",
        "Scrum",
    ],
    "idiomas": [
        {"idioma": "Portugues", "nivel": "Nativo"},
        {"idioma": "Ingles", "nivel": "Intermediario"},
    ],
}


if __name__ == "__main__":
    db = get_mongodb()

    result = db.db.user_profiles.update_one(
        {"profile_name": "Leonardo"},
        {"$set": leonardo_profile},
        upsert=True,
    )

    if result.upserted_id:
        print(f"Profile created: {result.upserted_id}")
    else:
        print(f"Profile updated: {result.matched_count} document(s)")

    profile = db.db.user_profiles.find_one({"profile_name": "Leonardo"})
    if profile:
        print("\nProfile Summary:")
        print(f"   Nome: {profile['nome']}")
        print(f"   Experiencias: {len(profile['experiencias'])}")
        print(f"   Habilidades: {len(profile['habilidades'])}")
        print(f"   Educacao: {len(profile['educacao'])}")
        print("\nProfile ready to use.")
    else:
        print("Profile not found after insert")
