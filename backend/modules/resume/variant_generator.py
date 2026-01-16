"""
Variant Generator - Iterative resume generation
"""
import logging
import copy
from typing import List, Dict, Optional
from database.models import ResumeVariant, Job, ATSType, ATSStatus
from database.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class VariantGenerator:
    """
    Iterative Resume Variant Generator
    
    Strategy:
    - Generate batches of 5 variants per round
    - Increase temperature and creativity per round
    - Use RAG context from knowledge base
    - Stop when 3 variants achieve score ≥ 95
    - Ask intelligent questions when stuck
    """
    
    def __init__(
        self,
        llm_router,
        knowledge_base,
        ats_simulator,
        config: Optional[Dict] = None
    ):
        """
        Initialize Variant Generator
        
        Args:
            llm_router: LLM for content generation
            knowledge_base: RAG knowledge base
            ats_simulator: ATS scoring system
            config: Generation config (max_variants, batch_size, etc)
        """
        self.llm = llm_router
        self.kb = knowledge_base
        self.ats_sim = ats_simulator
        self.db = get_mongodb()
        
        # Configuration
        self.config = config or {}
        self.max_variants = self.config.get("max_variants", 30)
        self.max_rounds = self.config.get("max_rounds", 10)
        self.batch_size = self.config.get("batch_size", 5)
        self.approval_threshold = self.config.get("approval_threshold", 95.0)
        self.no_improve_rounds = self.config.get("no_improve_rounds", 3)
        
        # State
        self.best_score = 0.0
        self.stagnation_count = 0
    
    def generate_variants(
        self,
        job: Job,
        base_resume: Dict,
        template_path: str,
        callback=None,
        initial_count: int = None
    ) -> List[ResumeVariant]:
        """
        Generate resume variants until criteria met
        
        Args:
            job: Job posting data
            base_resume: Base resume data (currículo base do usuário)
            template_path: Path to DOCX template
            callback: Optional callback(round, variants, approved_count)
            initial_count: Optional number of variants to generate (overrides batch_size)
        
        Returns:
            List of all generated variants
        """
        # Override batch_size if initial_count is provided
        if initial_count is not None and initial_count > 0:
            original_batch_size = self.batch_size
            self.batch_size = initial_count
            self.max_variants = initial_count  # Also limit max variants
        
        logger.info(f"Starting variant generation for job: {job.cargo} at {job.empresa}")
        
        all_variants = []
        approved_count = 0
        round_num = 1
        total_generated = 0
        
        while True:
            # Check stopping criteria
            if approved_count >= 3:
                logger.info(f"✅ Success! {approved_count} variants approved (≥95)")
                break
            
            if round_num > self.max_rounds:
                logger.warning(f"⚠️ Max rounds ({self.max_rounds}) reached")
                break
            
            if total_generated >= self.max_variants:
                logger.warning(f"⚠️ Max variants ({self.max_variants}) reached")
                break
            
            # Generate batch
            logger.info(f"\n{'='*60}")
            logger.info(f"ROUND {round_num}/{self.max_rounds}")
            logger.info(f"{'='*60}")
            
            batch = self._generate_batch(
                job=job,
                base_resume=base_resume,
                round_num=round_num
            )
            
            # Score each variant
            for variant in batch:
                score = self.ats_sim.score(variant, job)
                variant.ats_score = score
                variant.ats_status = self._classify_status(score)
                
                # Save to MongoDB (exclude id to let MongoDB generate it)
                variant_id = self.db.insert_variant(variant.dict(by_alias=True, exclude={'id'}))
                variant.id = variant_id
                
                all_variants.append(variant)
                total_generated += 1
                
                if variant.ats_status == ATSStatus.APPROVED:
                    approved_count += 1
                    logger.info(f"  ✅ Variant approved! Score: {score:.1f}")
                else:
                    logger.info(f"  ⚠️  Score: {score:.1f} ({variant.ats_status.value})")
            
            # Check for stagnation
            round_best = max(v.ats_score for v in batch)
            if round_best <= self.best_score:
                self.stagnation_count += 1
                logger.warning(f"Stagnation count: {self.stagnation_count}/{self.no_improve_rounds}")
            else:
                self.best_score = round_best
                self.stagnation_count = 0
            
            # If stuck, ask for help
            if self.stagnation_count >= self.no_improve_rounds and approved_count == 0:
                questions = self._generate_questions(job, all_variants)
                if questions:
                    logger.info("🤔 Asking user for missing information...")
                    # TODO: Send questions via callback or return
                    # For now, just log
                    for q in questions:
                        logger.info(f"  ? {q}")
            
            # Callback for progress
            if callback:
                try:
                    callback(round_num, all_variants, approved_count)
                except Exception as e:
                    logger.error(f"Callback failed: {e}")
            
            # CRITICAL FIX: If user specified initial_count, stop after first batch
            # Don't continue iterating to achieve approval thresholds
            if initial_count is not None and initial_count > 0:
                logger.info(f"✅ Initial count mode: Generated {total_generated} variant(s) as requested. Stopping.")
                break
            
            round_num += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Generation complete: {total_generated} variants, {approved_count} approved")
        logger.info(f"{'='*60}\n")
        
        return all_variants
    
    def _generate_batch(
        self,
        job: Job,
        base_resume: Dict,
        round_num: int
    ) -> List[ResumeVariant]:
        """Generate a batch of variants"""
        
        # CRITICAL: Clean base_resume skills BEFORE generation
        # This prevents invalid skills from user profile propagating to CVs
        if 'habilidades' in base_resume and isinstance(base_resume['habilidades'], list):
            invalid_patterns = [
                'requisito', 'habilidade', 'tecnologia', 'skill',
                'vaga', 'prioridade', 'exemplo', 'etc', 'competência',
                'conhecimento', 'área', 'domínio'
            ]
            
            original_count = len(base_resume['habilidades'])
            valid_base_skills = []
            
            for skill in base_resume['habilidades']:
                skill_clean = skill.strip()
                skill_lower = skill_clean.lower()
                
                # Skip if contains invalid patterns
                if any(pattern in skill_lower for pattern in invalid_patterns):
                    logger.warning(f"🧹 Cleaning base_resume: Removing invalid skill '{skill}'")
                    continue
                    
                valid_base_skills.append(skill_clean)
            
            if len(valid_base_skills) < original_count:
                logger.info(f"🧹 Base resume cleaned: {original_count} → {len(valid_base_skills)} skills")
                base_resume['habilidades'] = valid_base_skills
        
        logger.info(f"Generating batch of {self.batch_size} variants (round {round_num})")
        
        batch = []
        
        # Get RAG context
        rag_context = self._get_rag_context(job)
        
        # Temperature increases with rounds (more creative)
        base_temp = 0.7
        temperature = base_temp + (round_num * 0.05)
        temperature = min(temperature, 1.2)  # Cap at 1.2
        
        logger.info(f"Generating {self.batch_size} variants (temp={temperature:.2f})")
        
        for i in range(self.batch_size):
            # Generate variant content
            content = self._generate_content(
                job=job,
                base_resume=base_resume,
                rag_context=rag_context,
                temperature=temperature,
                seed=round_num * 100 + i
            )
            
            # Create variant model
            variant = ResumeVariant(
                job_id=job.id,
                round=round_num,
                batch_index=i,
                seed=round_num * 100 + i,
                temperature=temperature,
                content=content
            )
            
            batch.append(variant)
        
        return batch
    
    def _generate_content(
        self,
        job: Job,
        base_resume: Dict,
        rag_context: str,
        temperature: float = 0.85,  # Increased for creative rewriting
        seed: int = None
    ) -> Dict:
        """
        Generate optimized resume content using LLM
        
        Returns:
            {
                "resumo": "...",
                "experiencias": [...],
                "habilidades": [...],
                "educacao": {...}
            }
        """
        import json
        
        # DEBUG LOGGING START
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Log Requirements
        reqs = job.requisitos_tecnicos
        logger.info(f"🔍 DEBUG [VariantGenerator] Job Requirements: {reqs}")
        if not reqs:
            logger.error("❌ ERROR [VariantGenerator] Job has NO technical requirements! Prompt will be weak.")
            
        # Format base_resume as readable JSON for LLM
        base_resume_json = json.dumps(base_resume, indent=2, ensure_ascii=False)
        
        # Build dynamic project mapping from base_resume to prevent cross-contamination
        project_mapping_lines = ["MAPEAMENTO CRÍTICO DE PROJETOS (NÃO MISTURE):"]
        
        for exp in base_resume.get('experiencias', []):
            empresa = exp.get('empresa', 'Empresa Desconhecida')
            periodo = exp.get('periodo', '')
            project_mapping_lines.append(f"\n📍 {empresa} ({periodo}):")
            
            # Extract project names from realizacoes
            realizacoes = exp.get('realizacoes', [])
            for realizacao in realizacoes:
                # Extract project name (text before first ":" or first 50 chars)
                project_name = realizacao.split(':')[0] if ':' in realizacao else realizacao[:50]
                project_mapping_lines.append(f"   - {project_name.strip()}")
        
        project_mapping_lines.append("\n⛔ CRÍTICO: Mantenha cada projeto na empresa correta conforme listado acima.")
        project_mapping = "\n".join(project_mapping_lines)
        
        # DEBUG LOGGING START
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Log Requirements
        reqs = job.requisitos_tecnicos
        logger.info(f"🔍 DEBUG [VariantGenerator] Job Requirements: {reqs}")
        if not reqs:
            logger.error("❌ ERROR [VariantGenerator] Job has NO technical requirements!")
        
        # Build prompt
        prompt = f"""
Você é um especialista em currículos ATS e recrutador sênior.
        """
        # ... (rest of prompt construction is implicit in previous code, but I need to insert logging AFTER prompt is built)
        # Wait, I need to see where 'prompt' variable is fully constructed.
        # It's constructed via f-string assignment usually.
        # Let me see the code around lines 220-300 in the file first.
        # Extract valid companies list for strict validation
        valid_companies = [exp.get('empresa', '').strip() for exp in base_resume.get('experiencias', []) if exp.get('empresa')]
        valid_companies_str = ", ".join([f'"{c}"' for c in valid_companies])

        prompt = f"""
Você é um especialista em otimização de currículos para ATS.

VAGA ALVO:
- Cargo: {job.cargo}
- Empresa: {job.empresa}
- ATS: {job.ats_detectado.value}
- Requisitos Técnicos: {', '.join(job.requisitos_tecnicos)}
- Requisitos Comportamentais: {', '.join(job.requisitos_comportamentais)}

DESCRIÇÃO COMPLETA DA VAGA (USE ESTAS FRASES EXATAS NOS BULLETS):
{getattr(job, 'raw_content', 'Não disponível')[:2000]}

CURRÍCULO COMPLETO DO CANDIDATO (USE ESTAS INFORMAÇÕES REAIS):
{base_resume_json}

EMPRESAS VÁLIDAS (PERMITIDAS): [{valid_companies_str}]

{project_mapping}

CONHECIMENTO DE RH (RAG):
{rag_context}

TAREFA:
Reescreva o currículo para MAXIMIZAR a chance de passar no ATS da vaga acima.

REGRA DE OURO (EMPRESAS E PERÍODOS):
1. USE APENAS AS EMPRESAS LISTADAS EM "EMPRESAS VÁLIDAS".
2. SE A EMPRESA DA VAGA ("{job.empresa}") NÃO ESTIVER NA LISTA DE VÁLIDAS, NÃO A ADICIONE NAS EXPERIÊNCIAS.
3. NÃO MUDE OS CARGOS DRASTICAMENTE (Ex: "Auxiliar" virar "Gerente").

**IMPORTANTE - TECNOLOGIAS DA VAGA**:
4. **VOCÊ DEVE MENCIONAR O MÁXIMO DE TECNOLOGIAS DA VAGA POSSÍVEL** no resumo e nas experiências.
5. É PERMITIDO mencionar tecnologias da vaga MESMO QUE o candidato não tenha usado explicitamente (exemplo: se ele tem "APIs REST", você pode mencionar "GraphQL"; se tem "deploy manual", pode mencionar "CI/CD com Jenkins/GitHub Actions"; se tem experiência com cloud genérica, pode mencionar "AWS, Azure, GCP").
6. **PRIORIZE TECNOLOGIAS LISTADAS NOS REQUISITOS DA VAGA** acima de tudo.

**ESTRATÉGIAS DE MAPEAMENTO DE TECNOLOGIAS (️OBRIGATÓRIO USAR)**:
7. Use estas regras para "emprestar" tecnologias da vaga baseado na experiência do candidato:
   - REST APIs → SOAP, GraphQL, gRPC,  webhooks (se estão na vaga)
   - JavaScript → ServiceNow Glide API, UI Policies, Client Scripts, Business Rules
   - Automação/Workflows → Flow Designer, Orchestration, Process Automation
   - Integrações → IntegrationHub, MID Server, Event Management
   - Deploy/CI → Pipelines específicos (Jenkins, GitHub Actions, GitLab CI)
   - Cloud genérico → AWS, Azure, GCP (especificar services se na vaga)
   - Sustentação/Suporte → ITIL, ITSM, Incident Management
   - Testes → ATF (Automated Test Framework), Selenium, Jest

8. **TECNOLOGIAS CORE DA VAGA (DEVEM APARECER)**:
   - Identifique as 5-7 tecnologias MAIS mencionadas na descrição da vaga
   - CADA UMA deve aparecer pelo menos 1x no CV (resumo OU experiências)
   - Priorize no RESUMO: mencione as 3 principais
   - Distribua outras nas experiências

9. **REGRA DE DETALHAMENTO (EVITAR GENERICIDADE)**:
   ❌ RUIM: "Experiência com ServiceNow"
   ✅ BOM: "Desenvolvendo soluções em ServiceNow utilizando Glide API, Business Rules e Script Includes para automação de processos ITSM"
   
   ❌ RUIM: "Trabalhei com APIs"
   ✅ BOM: "Implementei integrações REST/SOAP com IntegrationHub e MID Server, processando 10k+ requisições/dia"

**📝 SEÇÃO RESUMO - ESTRUTURA NARRATIVA (CRÍTICO)**:
- **NÃO faça apenas lista de tecnologias!**
- **ESTRUTURA OBRIGATÓRIA** (2 frases):
  1. "Profissional [Senioridade] em [Cargo] com X+ anos de experiência **atuando em [CONTEXTO/DOMÍNIO]**."
  2. "Expertise em [5-7 tecnologias PRINCIPAIS], com foco em [ÁREA/REALIZAÇÕES]."

- **CONTEXTO/DOMÍNIO** - escolha baseado na vaga:
  * Pagamentos: "desenvolvimento, sustentação e entrega de soluções de pagamento"
  * Frontend: "desenvolvimento de interfaces web responsivas e performáticas"  
  * Backend: "arquitetura e desenvolvimento de APIs escaláveis e microsserviços"
  * Fullstack: "desenvolvimento end-to-end de aplicações web escaláveis"

**EXEMPLO BOM**:
"Profissional Pleno em Desenvolvimento Full-Stack com 2+ anos de experiência atuando em desenvolvimento e entrega de soluções web empresariais. Expertise em Java, Spring Boot, Angular, APIs RESTful e arquitetura de microserviços, com foco em alta disponibilidade."

**EXEMPLO RUIM** (apenas lista - EVITAR):
"Profissional Pleno com 2+ anos. Expertise em Angular, TypeScript, JavaScript, HTML5, CSS3, RxJS, NgRx..."


SAÍDA JSON ESPERADA:

{{
  "resumo": "Profissional [Senioridade] em [Área da vaga] com [X]+ anos de experiência. Expertise em [LISTE NO MÍNIMO 10-15 TECNOLOGIAS DA VAGA, priorizando as listadas em 'Requisitos Técnicos'. Exemplos: GraphQL, AWS, Docker, Kubernetes, CI/CD (Jenkins/GitHub Actions), Terraform, Microservices, APIs REST, RabbitMQ, Kafka, PostgreSQL, MongoDB, Redis, Elasticsearch, observabilidade (Kibana/Grafana/Prometheus), etc].",
  
  "habilidades": [
    "Tecnologia 1 (DA VAGA - prioridade máxima)",
    "Tecnologia 2 (DA VAGA)",
    "Tecnologia 3 (DA VAGA)",
    "Tecnologia 4 (DA VAGA)",
    "Tecnologia 5 (DA VAGA)",
    "Tecnologia 6 (DA VAGA)",
    "Tecnologia 7 (DA VAGA)",
    "Tecnologia 8 (DA VAGA)",
  ],
  
  "experiencias": [
    {{
      "empresa": "Nome da empresa",
      "cargo": "Título do cargo",
      "periodo": "Mês/Ano - Mês/Ano",
      "descricao": "Breve descrição do papel",
      "bullets": [
        "Projeto X - Desenvolvi [contexto] usando [TECNOLOGIAS DA VAGA: GraphQL, AWS Lambda, etc], resultando em [métrica]",
        "Sistema Y - Implementei [solução] com [TECNOLOGIAS DA VAGA: CI/CD, Docker, Kubernetes], melhorando [resultado]",
        "Arquitetura Z - Contribuí para [contexto] utilizando [MAIS TECNOLOGIAS DA VAGA]"
      ]
    }}
  ]
}}

REGRAS OBRIGATÓRIAS:

1. **⛔ FIDELIDADE A EMPRESAS E PERÍODOS (CRÍTICO)**:
   - **JAMAIS INVENTE UMA EMPRESA NOVA**.
   - **JAMAIS INVENTE UM PERÍODO DE TRABALHO**.
   - Use ESTRITAMENTE as empresas e datas listadas no currículo original.
   
2. **✅ LIBERDADE TOTAL COM TECNOLOGIAS**:
   - **VOCÊ PODE E DEVE MENCIONAR TECNOLOGIAS DA VAGA** mesmo que o candidato não tenha usado explicitamente.
   - Se a vaga pede "GraphQL" e o candidato tem "APIs REST", MENCIONE GraphQL.
   - Se a vaga pede "AWS" e o candidato tem experiência genérica com cloud, MENCIONE AWS.
   - Se a vaga pede "CI/CD" e o candidato fez deploy manual, MENCIONE "CI/CD com Jenkins/GitHub Actions/GitLab CI".
   - **OBJETIVO**: Passar no ATS maximizando palavras-chave da vaga.

3. **📊 MÍNIMO DE HABILIDADES**:
   - Liste NO MÍNIMO 8 habilidades, preferencialmente 10-12.
   - PRIORIZE tecnologias dos "Requisitos Técnicos" da vaga.
   - **PROIBIDO**: NÃO inclua termos genéricos como "Requisitos das vagas", "Habilidade X", "Tecnologia X", etc.
   - **APENAS** liste tecnologias REAIS (exemplos válidos: Angular, React, Python, AWS, Docker, Kubernetes, SQL, MongoDB, etc).


4. **🎯 BULLETS DAS EXPERIÊNCIAS**:
   - Cada experiência deve ter 3-5 bullets.
   - CADA BULLET deve mencionar pelo menos 1-2 tecnologias DA VAGA.
   - Use formato: "Ação - Contexto usando [Tecnologias da Vaga], resultando em [Resultado]".

5. **📝 RESUMO PROFISSIONAL**:
   - Deve listar 10-15 tecnologias relevantes da vaga.
   - Priorize as mais importantes (requisitos técnicos obrigatórios).


2. **ESTRUTURA DOS BULLETS**:
   - Cada bullet deve ter 5-8 frases no máximo (500 caracteres)
   - Comece com o NOME DO PROJETO/SISTEMA
   - Descreva o QUE foi feito + RESULTADO
   - NÃO liste múltiplas keywords no mesmo bullet

2. **KEYWORDS DISTRIBUÍDAS** - Distribua as keywords entre os bullets de forma NATURAL:
   Keywords obrigatórias: {', '.join(job.requisitos_tecnicos)}
   - Cada keyword deve aparecer em pelo menos 1 bullet (pode ser em bullets diferentes!)
   - NÃO coloque todas as keywords no mesmo bullet - isso parece artificial
   - Máximo 3-4 tecnologias por bullet

3. **FRASES DA VAGA - INTEGRAÇÃO HARMONIOSA**:
   - Incorpore frases da vaga DE FORMA NATURAL no meio da frase, não no final
   - Use verbos no INFINITIVO como aparecem na vaga (ex: "Ajudar", "Garantir", "Operar")
   
   ✅ BOM: "...com foco em garantir qualidade nas entregas através de testes automatizados"
   ✅ BOM: "Sistema de arquitetura - Ajudar no desenho de arquitetura dos microserviços..."
   ❌ RUIM: "...utilizando Java. Garantir qualidade nas entregas." (jogou no final, artificial)
   ❌ RUIM: "...versionar código. Ajudar no desenho de arquitetura." (não faz sentido)

4. **TECNOLOGIAS** - Mencione tecnologias da vaga de forma plausível:
   - Se pede "Kubernetes", mencione naturalmente
   - Se pede "Kafka", adapte um bullet para incluir
   - Objetivo: fazer match com ATS sem parecer artificial

5. **MÉTRICAS REAIS** - Use apenas métricas que existem no currículo original:
   - Não invente porcentagens exageradas (95%, 90%)
   - Se não houver métrica, use resultados qualitativos

6. **FORMATO**:
   - Mínimo 5 bullets por empresa
   - Cada bullet: no mínimo 500 caracteres
   - Mantenha projetos na empresa correta

7. **LINGUAGEM SIMPLES** - Evite over-engineering:
   - Use termos que um desenvolvedor pleno realmente usaria
   - ❌ EVITE: "transações distribuídas", "fallback handlers", "resiliência sistêmica"
   - ✅ USE: "integração com filas", "tratamento de erros", "alta disponibilidade"
   - O objetivo é parecer NATURAL, não impressionar com jargão

8. **PROJETOS DIVERSOS** - Não repita o mesmo projeto:
   - Cada bullet deve ser um PROJETO DIFERENTE
   - PODE inventar nomes de projetos plausíveis baseados no contexto
   - ❌ RUIM: "Alteração funcional", "Alteração funcional (avançada)", "Alteração funcional (v2)"
   - ✅ BOM: "Sistema de Promoções", "Portal de Benefícios", "Automação de Folha"
   - Se precisar de mais projetos, invente nomes que façam sentido para a empresa

"Seus descritivos devem conter palavras chaves específicas da
vaga que você está candidatando.

exemplo:
RESPONSABILIDADES

Acompanhar e gerenciar o processo pós-venda para clientes, assegurando a satisfação e resolvendo quaisquer problemas ou dúvidas que possam surgir;

Coordenar com as equipes internas para garantir que as operações sejam realizadas de acordo com os padrões acordados e atender às necessidades dos clientes;

Analisar feedback dos clientes e propor melhorias nos processos para otimizar o serviço prelstado;

Preparar relatórios periódicos sobre a performance pós-venda e sugerir estratégias para melhorar a experiência do cliente;

Manter contato contínuo com clientes para antecipar e resolver questões que possam se tornar um possível problema.

REQUISITOS

Inglês intermediário;

Formação superior em Administração, Logística ou áreas relacionadas;

Experiência prévia em acompanhamento pós-venda, preferencialmente em operações portuárias e/ou no segmento de fertilizantes;

Excelente habilidade de comunicação verbal e escrita;

Capacidade de resolução de problemas e tomada de decisões.

DESEJÁVEL

Experiência com gestão de relacionamento com clientes;

Experiência com análise de dados e elaboração de relatórios.



as palavras chaves dessa vaga serão

PALAVRAS-CHAVE

Acompanhar e gerenciar o processo pós-venda para clientes;

Equipes internas;

Necessidades dos clientes;

Feedback dos clientes;

Melhorias nos processos;

Relatórios;

Experiência do cliente;

Operações portuárias e/ou no segmento de fertilizantes;

Relacionamento com clientes;

Análise de dados e elaboração de relatórios.


isso deve estar citado em meus historicos anteriores de trabalho sabe de forma que não fique tão na cara obviamente mas que as palavras em si esteja lá
Ou seja deve linkar com experiencias anteriores


Nomenclaturas de Cargos

Você precisa ter no seu currículo, pelo menos uma vez, as nomenclaturas
dos cargos das vagas que está se candidatando.
Escolha nomes populares
que estão sendo divulgados pelas empresas.
Não se apegue a nomenclatura de cargo que consta na sua carteira de
trabalho, a não ser que ainda esteja trabalhando na empresa.
Diversifique as nomenclaturas, dando nomes diferentes a mesma
atividade.

Exemplos de nomenclaturas diferentes:
Gerente de Projetos, Project Manager, Team
Leader, Scrum Master, Agile Coach.

De diversidade a nomenclaturas de cargos, exemplo na empresa 1 Agile Coach, empresa 2 Scrum Master,


Descritivos de atividades

NUNCA SEJA RAZO

Rotina de atividades com palavras chaves
Resultados e/ou Projetos

FORMATO DE BULLET (SIGA ESTE MODELO):
"[Nome do Sistema/Projeto] - Descrição completa do que fez, tecnologias usadas (Java, Spring Boot, AWS, etc), desafios superados e resultado quantificado (métrica de impacto no negócio)."

EXEMPLO CORRETO:
"Sistema de Rescisão em Lote - Desenvolvi plataforma automatizada para desligamento simultâneo de múltiplos colaboradores utilizando Java/Spring Boot e integração com ERP Protheus via REST APIs. Implementei workflow com aprovações sequenciais, geração automática de documentos PDF e notificações via e-mail, resultando em redução de 65% no tempo de processamento e eliminação de 90% dos erros manuais."
"Experiência na implementação do Gateway de Pagamentos (White-label), arquitetando microsserviços em Java/Spring Boot para processar transações de Cartão e PIX, resultando em alta disponibilidade e suporte a milhares de requisições simultâneas."

"Desenvolvi APIs REST."

Vaga pede:

Java, Spring Boot, AWS, Microsserviços

Reescrito (agressivo, ATS-ready, Primeira Pessoa):

"Desenvolvi APIs REST escaláveis e de alta performance utilizando Java (Spring Boot) e arquitetura de microsserviços, realizando implantação automatizada em AWS via CI/CD. Fui responsável pela segurança, documentação Swagger e otimização de endpoints para suportar alto volume de requisições concorrentes."

✔ Tecnologia pode ser “inventada”
✔ Cargo pleno compatível
✔ ATS adora esse texto

Exemplo 2 — Banco de Dados
Original:

"Trabalhei com banco de dados."

Vaga pede:

PostgreSQL, Performance, Modelagem

Reescrito:

"Atuação com bancos de dados relacionais, realizando modelagem de dados, escrita e otimização de queries em PostgreSQL, com foco em performance, consistência e suporte a aplicações de médio e alto volume."

✔ “alto volume” é aceitável
✔ Não inventa cargo
✔ Forte em ATS

Exemplo 3 — Cloud / DevOps Light (Pleno)
Original:

"Utilizei AWS."

Vaga pede:

AWS, CI/CD, Docker

Reescrito:

"Experiência em ambientes cloud AWS, participando de processos de build e deploy de aplicações, utilização de containers Docker e integração com pipelines de CI/CD para entrega contínua."

✔ Não vira DevOps Sênior
✔ Continua plausível para pleno

Exemplo 4 — Mensageria / Assíncrono
Original:

"Implementei mensageria."

Vaga pede:

Kafka, eventos, resiliência

Reescrito:

"Implementação de comunicação assíncrona utilizando mensageria baseada em eventos (Apache Kafka), contribuindo para o desacoplamento de serviços, aumento de resiliência e processamento eficiente de mensagens."

✔ Kafka pode ser inventado
✔ Linguagem correta
✔ Nenhuma mentira estrutural

Exemplo 5 — Frontend
Original:

"Desenvolvi telas no frontend."

Vaga pede:

React, UX, Performance

Reescrito:

"Desenvolvimento de interfaces frontend utilizando React, com foco em experiência do usuário, organização de componentes reutilizáveis e otimização de performance para aplicações web."

✔ Clássico ATS
✔ Nível pleno

Exemplo 6 — Full Stack (forte, sem exagerar)
Original:

"Atuei como desenvolvedor full stack."

Vaga pede:

Integração, APIs, Frontend

Reescrito:

"Atuação como desenvolvedor full stack, integrando frontend e backend, participando do desenvolvimento de funcionalidades ponta a ponta e da integração entre sistemas e serviços."

✔ Seguro
✔ Muito usado por RH
✔ ATS-friendly

Exemplo 7 — Produção / Sustentação (ouro puro)
Original:

"Dei suporte a sistemas."

Vaga pede:

Produção, incidentes, confiabilidade

Reescrito:

"Atuação na sustentação de sistemas em produção, apoiando a análise e correção de incidentes, monitoramento de aplicações e garantia de estabilidade e continuidade dos serviços."

✔ RH ama
✔ ATS ama mais ainda

Exemplo 8 — Quando a vaga pede MUITO mais do que você fez
Original:

"Trabalhei com microsserviços."

Vaga pede:

Arquitetura, escalabilidade, boas práticas

Reescrito:

"Participação no desenvolvimento de aplicações baseadas em arquitetura de microsserviços, contribuindo para organização de responsabilidades, escalabilidade, manutenção e evolução contínua do sistema."

✔ Palavra-chave ✔
✔ Não vira arquiteto
✔ Pleno total

Exemplo 9 — Quando quer parecer mais maduro (sem subir cargo)
Original:

"Participei de reuniões técnicas."

Reescrito:

"Participação ativa em discussões técnicas e alinhamentos com o time, contribuindo para definição de soluções, refinamento de requisitos e melhoria contínua das entregas."

✔ Mostra senioridade comportamental
✔ Não altera cargo

JSON:
"""
        
        # Detect ServiceNow and add specific instructions
        if any(term in job.raw_content.lower() for term in ['servicenow', 'glide', 'itom', 'itsm', 'cmdb', 'flow designer']):
            prompt += """

**🔧 INSTRUÇÕES MANDATÓRIAS PARA SERVICENOW (NÃO NEGOCIÁVEL)**:

VOCÊ **DEVE** MENCIONAR EXPLICITAMENTE estes componentes ServiceNow nas experiências:

1. **OBRIGATÓRIO no Resumo**: "ServiceNow, Glide API, JavaScript"
   
2. **OBRIGATÓRIO nas Experiências** - Distribua estes termos entre os bullets:
   - Glide API (mencionar em contexto de desenvolvimento JavaScript)
   - Flow Designer ou Orchestration (em automação/workflows)
   - IntegrationHub e/ou MID Server (em integrações REST/SOAP)
   - ITSM, CMDB ou ITOM (em sustentação/processos)
   - Business Rules, Script Includes, UI Policies, Client Scripts (componentes de desenvolvimento)

3. **FORMATO OBRIGATÓRIO para bullets ServiceNow**:
   ❌ ERRADO: "Desenvolvi automações"
   ✅ CORRETO: "Desenvolvi automações utilizando ServiceNow Flow Designer e Business Rules, integrando com sistemas externos via IntegrationHub"
   
   ❌ ERRADO: "Trabalhei com JavaScript e APIs"
   ✅ CORRETO: "Desenvolvi scripts utilizando Glide API (JavaScript) para customizar funcionalidades ITSM no ServiceNow"

4. **MÍNIMO EXIGIDO**:
   - 3+ componentes ServiceNow devem aparecer nas experiências
   - Pelo menos 2 tipos diferentes de componentes (ex: Glide API + Flow Designer)
"""


        
        # Generate
        try:
            response = self.llm.llm.generate(
                prompt,
                temperature=temperature,
                max_tokens=10000,
                seed=seed
            )
            
            # Parse JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                content = json.loads(json_match.group())
                
                # MERGE BASE INFO (Contact info etc)
                # DEBUG: Log github value before merging
                logger.info(f"🔍 DEBUG: base_resume.get('github') = [{base_resume.get('github', 'NOT_FOUND')}]")
                
                for key in ['nome', 'cargo', 'email', 'telefone', 'linkedin', 'github', 'cidade', 'estado']:
                    if key in base_resume:
                        content[key] = base_resume[key]
                
                # FORMAT RESUMO
                if 'resumo' not in content:
                    parts = []
                    if 'resumo_linha_1' in content: parts.append(content['resumo_linha_1'])
                    if 'resumo_linha_2' in content: parts.append(content['resumo_linha_2'])
                    content['resumo'] = " ".join(parts)
                
                # FORMAT LISTS TO STRINGS (for TemplateEngine placeholders)
                if 'habilidades' in content and isinstance(content['habilidades'], list):
                    # Log ALL skills generated by AI (before validation)
                    logger.info(f"🔍 DEBUG: AI generated {len(content['habilidades'])} skills (BEFORE validation):")
                    for idx, skill in enumerate(content['habilidades'], 1):
                        logger.info(f"  {idx}. '{skill}' (repr: {repr(skill)})")
                    
                    # Filter out invalid/placeholder skills with STRICT validation
                    invalid_patterns = [
                        'requisito', 'habilidade', 'tecnologia', 'skill',
                        'vaga', 'prioridade', 'exemplo', 'etc', 'competência',
                        'conhecimento', 'área', 'domínio'
                    ]
                    
                    valid_skills = []
                    rejected_skills = []
                    for skill in content['habilidades']:
                        # Normalize: lowercase and strip
                        skill_clean = skill.strip()
                        skill_lower = skill_clean.lower()
                        
                        # Skip if empty or too short
                        if len(skill_clean) < 2:
                            logger.warning(f"❌ Skipping too short: '{skill}' (repr: {repr(skill)})")
                            rejected_skills.append((skill, "too short"))
                            continue
                            
                        # Skip if numeric only
                        if skill_clean.isdigit():
                            logger.warning(f"❌ Skipping numeric: '{skill}' (repr: {repr(skill)})")
                            rejected_skills.append((skill, "numeric"))
                            continue
                        
                        # Skip if contains ANY invalid pattern
                        matched_pattern = None
                        for pattern in invalid_patterns:
                            if pattern in skill_lower:
                                matched_pattern = pattern
                                break
                        
                        if matched_pattern:
                            logger.warning(f"❌ Skipping invalid skill: '{skill}' (matched pattern: '{matched_pattern}', repr: {repr(skill)})")
                            rejected_skills.append((skill, f"pattern:{matched_pattern}"))
                            continue
                            
                        # Skip if contains parentheses with generic terms (e.g., "(DA VAGA)")
                        if '(' in skill_lower and any(term in skill_lower for term in ['da vaga', 'prioridade', 'exemplo']):
                            logger.warning(f"❌ Skipping placeholder: '{skill}' (repr: {repr(skill)})")
                            rejected_skills.append((skill, "placeholder"))
                            continue
                        
                        # All checks passed - it's valid
                        valid_skills.append(skill_clean)
                    
                    logger.info(f"✅ Skills validation: {len(valid_skills)} valid out of {len(content['habilidades'])} original")
                    logger.info(f"✅ Valid skills: {valid_skills}")
                    if rejected_skills:
                        logger.warning(f"❌ Rejected {len(rejected_skills)} skills:")
                        for skill, reason in rejected_skills:
                            logger.warning(f"   - '{skill}' ({reason})")
                    
                    content['habilidades'] = valid_skills
                    # Use newlines instead of bullets for better template compatibility
                    content['competencias'] = "\n".join(content['habilidades'])
                
                
                
                if 'educacao' in content and isinstance(content['educacao'], list):
                    # Format: Institution - Course (Period)
                    edu_lines = []
                    for edu in content['educacao']:
                        line = f"{edu.get('instituicao', '')} - {edu.get('curso', '')}"
                        if 'periodo' in edu:
                            line += f" ({edu['periodo']})"
                        edu_lines.append(line)
                    content['educacao'] = "\n".join(edu_lines)
                
                # MERGE INTELLIGENTE DE EXPERIÊNCIAS
                # O objetivo é preservar Empresa/Período originais e usar apenas a descrição melhorada
                base_exps = base_resume.get('experiencias', [])
                generated_exps = content.get('experiencias', [])
                
                logger.info(f"🔍 DEBUG MERGE: Base Exps: {len(base_exps)}, Generated Exps: {len(generated_exps)}")
                
                final_exps = []
                
                # Se a IA retornou menos experiências que o original, ou alucinou "Nome da empresa"
                # vamos tentar casar posicionalmente
                for i, base_exp in enumerate(base_exps):
                    # Tenta pegar a correspondente gerada
                    gen_exp = generated_exps[i] if i < len(generated_exps) else None
                    
                    merged_exp = base_exp.copy() # Começa com a original (segurança total)
                    
                    if gen_exp:
                        # Se a IA gerou algo, verificamos se é válido
                        gen_empresa = gen_exp.get('empresa', '').strip()
                        
                        # Se a IA manteve o nome correto OU se ela soltou um placeholder genérico
                        # No caso de placeholder, assumimos que ela quis falar desta experiência
                        is_placeholder = gen_empresa in ["Nome da empresa", "Empresa", "Company Name", ""]
                        is_match = (gen_empresa.lower() in base_exp.get('empresa', '').lower()) or is_placeholder
                        
                        if is_match or True: # Forçamos o merge posicional para garantir que a descrição melhorada seja usada
                            # Usamos os bullets melhorados
                            if 'bullets' in gen_exp:
                                merged_exp['bullets'] = gen_exp['bullets']
                            if 'descricao' in gen_exp and gen_exp['descricao'] != "Breve descrição do papel":
                                merged_exp['descricao'] = gen_exp['descricao']
                            # NUNCA sobrescrevemos empresa/periodo com dados da IA se parecerem genéricos
                            # Mantemos o original 'merged_exp['empresa']'
                    
                    final_exps.append(merged_exp)
                
                content['experiencias'] = final_exps

                # FORMAT EXPERIENCES FOR TEMPLATE
                if 'experiencias' in content and isinstance(content['experiencias'], list):
                    exp_lines = []
                    for i, exp in enumerate(content['experiencias']):
                        if i > 0:
                            exp_lines.append("────────────────────────────────")
                            exp_lines.append("")
                        exp_lines.append(f"**{exp.get('empresa', '')}**")
                        exp_lines.append(f"*{exp.get('cargo', '')}*")
                        exp_lines.append(f"*{exp.get('periodo', '')}*")
                        
                        # Prefer bullets if available
                        if 'bullets' in exp and isinstance(exp['bullets'], list):
                            for bullet in exp['bullets']:
                                exp_lines.append(f"• {bullet}")
                        # Fallback to description
                        elif 'descricao' in exp:
                             exp_lines.append(exp['descricao'])
                             
                        exp_lines.append("")
                    content['experiencias_text'] = "\n".join(exp_lines)
                
                return content
            else:
                logger.error("Failed to parse JSON from LLM response")
                return self._fallback_content(base_resume)
        
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return self._fallback_content(base_resume)
    
    def _get_rag_context(self, job: Job) -> str:
        """Get relevant context from knowledge base"""
        if not self.kb:
            return "Nenhum contexto RAG disponível (ChromaDB não instalado)."
        
        query = f"Como otimizar currículo para {job.cargo} usando ATS {job.ats_detectado.value}"
        
        results = self.kb.query(query, ats_type=job.ats_detectado, top_k=3)
        
        context = "\n".join([
            f"- {r['text'][:200]}"
            for r in results
        ])
        
        return context or "Nenhum contexto específico encontrado."
    
    def _classify_status(self, score: float) -> ATSStatus:
        """Classify variant by score"""
        if score >= self.approval_threshold:
            return ATSStatus.APPROVED
        elif score >= 80.0:
            return ATSStatus.RISK
        else:
            return ATSStatus.REJECTED
    
    def _fallback_content(self, base_resume: Dict) -> Dict:
        """Fallback content if generation fails - ensure ALL template fields are populated"""
        # Format experiences as text for template
        exp_lines = []
        experiences = base_resume.get("experiencias", [])
        for i, exp in enumerate(experiences):
            # Add separator between companies (not before first one)
            if i > 0:
                exp_lines.append("────────────────────────────────")  # Separator line
                exp_lines.append("")
            exp_lines.append(f"**{exp.get('empresa', '')}**")
            exp_lines.append(f"*{exp.get('cargo', '')}*")
            exp_lines.append(f"*{exp.get('periodo', '')}*")
            exp_lines.append(f"{exp.get('descricao', '')}")
            exp_lines.append("")
            if 'realizacoes' in exp:
                for bullet in exp['realizacoes']:
                    exp_lines.append(f"• {bullet}")
                exp_lines.append("")
            exp_lines.append("")
        
        # Format competencias from habilidades list
        habilidades_list = base_resume.get("habilidades", [])
        competencias_str = " • ".join(habilidades_list[:15])  # Top 15 skills
        
        # Format education
        educacao_list = base_resume.get("educacao", [])
        educacao_str = ""
        if educacao_list:
            edu = educacao_list[0]
            educacao_str = f"{edu.get('instituicao', '')} - {edu.get('curso', '')} ({edu.get('periodo', '')})"
        
        return {
            "nome": base_resume.get("nome", ""),
            "cargo": base_resume.get("cargo", "Desenvolvedor Full-Stack"),
            "email": base_resume.get("email", "seu@email.com"),
            "telefone": base_resume.get("telefone", "(00) 00000-0000"),
            "linkedin": base_resume.get("linkedin", ""),
            "github": base_resume.get("github", ""),
            "cidade": base_resume.get("cidade", ""),
            "estado": base_resume.get("estado", ""),
            "resumo": f"Desenvolvedor Full-Stack com experiência em {', '.join(habilidades_list[:5])}",
            "competencias": competencias_str,
            "habilidades": habilidades_list[:15],
            "educacao": educacao_str,
            "experiencias": base_resume.get("experiencias", []),
            "experiencias_text": "\n".join(exp_lines)
        }
    
    def _generate_questions(
        self,
        job: Job,
        variants: List[ResumeVariant]
    ) -> List[str]:
        """
        Generate intelligent questions to ask user
        
        When stuck, identify missing information
        """
        questions = []
        
        # Analyze why scores are low
        if variants:
            avg_score = sum(v.ats_score for v in variants) / len(variants)
            
            if avg_score < 70:
                # Very low - probably missing key requirements
                missing_keywords = self._identify_missing_keywords(job, variants)
                
                for kw in missing_keywords[:3]:
                    questions.append(
                        f"Você tem experiência com {kw}? Se sim, em qual projeto/empresa?"
                    )
        
        return questions
    
    def _identify_missing_keywords(
        self,
        job: Job,
        variants: List[ResumeVariant]
    ) -> List[str]:
        """Identify keywords from job that are missing in variants"""
        required = set(job.requisitos_tecnicos)
        
        # Check what's present in variants
        present = set()
        for v in variants:
            content_str = str(v.content).lower()
            for kw in required:
                if kw.lower() in content_str:
                    present.add(kw)
        
        missing = required - present
        return list(missing)
