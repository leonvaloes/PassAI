"""
AI Job Enricher
Uses LLM to extract structured data from raw job text
"""
import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AIJobEnricher:
    """AI-powered job data enrichment using LLM"""
    
    def __init__(self, llm_router):
        self.llm = llm_router
    
    def enrich_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich job data using AI - AUTOMATIC VERSION
        
        Extracts:
        - Tech keywords
        - Seniority level
        - Must-have vs nice-to-have requirements
        """
        # Get text to analyze
        text = raw_data.get('rawText') or raw_data.get('description') or ''
        
        if not text or len(text) < 50:
            logger.warning("Insufficient text for AI enrichment")
            return raw_data
        
        try:
            # Build enrichment prompt
            prompt = self._build_enrichment_prompt(text)
            
            # Call LLM
            response = self.llm.generate(
                prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # Parse JSON response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            enriched = json.loads(response_text)
            
            # Merge with original data
            raw_data['techKeywords'] = enriched.get('tech_keywords', [])
            raw_data['seniority'] = enriched.get('seniority')
            raw_data['mustHave'] = enriched.get('must_have', [])
            raw_data['niceToHave'] = enriched.get('nice_to_have', [])
            
            logger.info(f"✅ AI enrichment successful: {len(raw_data['techKeywords'])} keywords found")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
        except Exception as e:
            logger.error(f"AI enrichment failed: {e}")
        
        return raw_data
    
    def _build_enrichment_prompt(self, text: str) -> str:
        """Build prompt for LLM to extract structured data"""
        return f"""
Você é um especialista em RH e tecnologia. Analise esta vaga de emprego e extraia informações estruturadas.

VAGA:
{text[:3000]}

TAREFA: Retorne APENAS um JSON válido com:

{{
  "tech_keywords": ["lista", "de", "tecnologias", "encontradas"],
  "seniority": "junior" | "pleno" | "senior" | "lead",
  "must_have": ["requisitos", "obrigatórios"],
  "nice_to_have": ["requisitos", "opcionais"]
}}

REGRAS:
1. tech_keywords: Liste TODAS as tecnologias, linguagens, frameworks, ferramentas (ex: Java, React, AWS, Docker)
2. seniority: Infira o nível baseado em: anos de experiência, responsabilidades, termos como "jr", "pl", "sr"
3. must_have: Requisitos marcados como "obrigatório", "essenciais", "required"
4. nice_to_have: Requisitos marcados como "desejável", "diferencial", "plus", "nice to have"
5. Se não encontrar, use lista vazia []
6. Responda APENAS JSON válido, sem explicações

JSON:
""".strip()
    
    def extract_keywords_simple(self, text: str) -> List[str]:
        """Simple keyword extraction without LLM (fallback)"""
        # Common tech keywords
        keywords = [
            'Java', 'Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C#', 'C++', 'Ruby', 'PHP',
            'React', 'Angular', 'Vue', 'Next.js', 'Node.js', 'Express', 'Django', 'Flask', 'Spring',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Git', 'CI/CD', 'Agile', 'Scrum', 'REST', 'GraphQL', 'gRPC'
        ]
        
        text_lower = text.lower()
        found = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        return found
    
    def infer_seniority(self, text: str, title: Optional[str] = None) -> Optional[str]:
        """Infer seniority level from text (fallback)"""
        text_combined = f"{title or ''} {text}".lower()
        
        # Junior indicators
        if any(word in text_combined for word in ['junior', 'jr', 'estagiário', 'trainee', '0-2 anos']):
            return 'junior'
        
        # Senior indicators
        if any(word in text_combined for word in ['senior', 'sr', 'sênior', 'especialista', '5+ anos', 'lead']):
            return 'senior'
        
        # Lead indicators
        if any(word in text_combined for word in ['lead', 'líder', 'principal', 'staff', 'architect']):
            return 'lead'
        
        # Default to pleno
        return 'pleno'


# Integration function
def enrich_job_with_ai(job_data: Dict[str, Any], llm_router) -> Dict[str, Any]:
    """Convenience function to enrich job data"""
    enricher = AIJobEnricher(llm_router)
    return enricher.enrich_job(job_data)

def extract_basic_info(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic info without AI call"""
    enricher = AIJobEnricher(None)
    
    text = job_data.get('rawText') or job_data.get('description') or ''
    title = job_data.get('title')
    
    # Extract keywords using simple regex/list
    job_data['techKeywords'] = enricher.extract_keywords_simple(text)
    
    # Infer seniority using simple rules
    job_data['seniority'] = enricher.infer_seniority(text, title)
    
    return job_data
