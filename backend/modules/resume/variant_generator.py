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
        callback=None
    ) -> List[ResumeVariant]:
        """
        Generate resume variants until criteria met
        
        Args:
            job: Job posting data
            base_resume: Base resume data (currículo base do usuário)
            template_path: Path to DOCX template
            callback: Optional callback(round, variants, approved_count)
        
        Returns:
            List of all generated variants
        """
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
                callback(round_num, all_variants, approved_count)
            
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
        temperature: float,
        seed: int
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
        # Build prompt
        prompt = f"""
Você é um especialista em otimização de currículos para ATS.

VAGA:
- Cargo: {job.cargo}
- Empresa: {job.empresa}
- ATS: {job.ats_detectado.value}
- Requisitos Técnicos: {', '.join(job.requisitos_tecnicos)}
- Requisitos Comportamentais: {', '.join(job.requisitos_comportamentais)}

CURRÍCULO BASE DO CANDIDATO:
{base_resume}

CONHECIMENTO DE RH (RAG):
{rag_context}

TAREFA:
Gere um currículo otimizado para esta vaga. Retorne JSON:

{{
  "resumo_linha_1": "Profissional [senioridade] em [área] com X+ anos...",
  "resumo_linha_2": "Expertise em [tecnologias relevantes]",
  
  "habilidades": [
    "Habilidade 1 (da vaga)",
    "Habilidade 2 (da vaga)",
    "Habilidade 3",
    "Habilidade 4",
    "Habilidade 5"
  ],
  
  "experiencias": [
    {{
      "empresa": "Nome da empresa",
      "cargo": "Título do cargo",
      "periodo": "Mês/Ano - Mês/Ano",
      "descricao": "Breve descrição do papel",
      "bullets": [
        "Realizou X resultando em Y (métrica)",
        "Desenvolveu Z usando [tecnologia da vaga]"
      ]
    }}
  ]
}}

REGRAS CRÍTICAS:
1. NUNCA inventar empresas onde não trabalhou
2. PODE adaptar descrições e bullets para match keywords
3. PODE adicionar métricas quantificáveis
4. Bullets: max 80 caracteres
5. Keywords da vaga devem aparecer 2-3x ao longo do CV
6. Use verbos de ação no início dos bullets
7. Foco em resultados mensuráveis

JSON:
"""
        
        # Generate
        try:
            response = self.llm.llm.generate(
                prompt,
                temperature=temperature,
                max_tokens=1000,
                seed=seed
            )
            
            # Parse JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                content = json.loads(json_match.group())
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
        """Fallback content if generation fails"""
        return {
            "resumo_linha_1": base_resume.get("resumo", "Profissional experiente"),
            "resumo_linha_2": "Buscando novos desafios",
            "habilidades": base_resume.get("habilidades", [])[:5],
            "experiencias": base_resume.get("experiencias", [])[:3]
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
