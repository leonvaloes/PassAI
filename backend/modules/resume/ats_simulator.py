"""
ATS Simulator - Score resume variants against ATS systems
"""
import logging
import re
from typing import Dict, List
from database.models import ResumeVariant, Job, ATSType

logger = logging.getLogger(__name__)


class ATSSimulator:
    """
    ATS Scoring System
    
    Simulates how an ATS would score a resume
    
    Weights:
    - Keywords: 40%
    - Formatting: 25%
    - Structure: 20%
    - Checklist: 15%
    """
    
    # Scoring weights
    WEIGHTS = {
        "keywords": 0.40,
        "formatting": 0.25,
        "structure": 0.20,
        "checklist": 0.15
    }
    
    def __init__(self, ats_detector):
        """
        Initialize ATS Simulator
        
        Args:
            ats_detector: ATSDetector instance for rules
        """
        self.ats_detector = ats_detector
    
    def score(self, variant: ResumeVariant, job: Job) -> float:
        """
        Score a resume variant
        
        Args:
            variant: Resume variant to score
            job: Job posting
        
        Returns:
            Score 0-100
        """
        scores = {}
        
        # 1. Keywords (40%)
        scores["keywords"] = self._score_keywords(variant, job)
        
        # 2. Formatting (25%)
        scores["formatting"] = self._score_formatting(variant, job.ats_detectado)
        
        # 3. Structure (20%)
        scores["structure"] = self._score_structure(variant)
        
        # 4. Checklist (15%)
        scores["checklist"] = self._score_checklist(variant, job)
        
        # Calculate weighted average
        final_score = sum(scores[k] * self.WEIGHTS[k] for k in scores)
        
        # Store breakdown
        variant.score_breakdown = scores
        
        # Generate motivos
        variant.motivos = self._generate_motivos(scores, job)
        
        # Generate checklist results
        variant.checklist = self._generate_checklist_results(variant, job)
        
        logger.debug(f"Score breakdown: {scores} → Final: {final_score:.1f}")
        
        return final_score
    
    def _score_keywords(self, variant: ResumeVariant, job: Job) -> float:
        """
        Score keyword matching (0-100)
        
        Checks if required keywords appear in the resume
        """
        required_keywords = set(
            kw.lower() for kw in job.requisitos_tecnicos + job.requisitos_comportamentais
        )
        
        if not required_keywords:
            return 100.0  # No requirements = auto-pass
        
        # Convert variant to text
        content_text = self._variant_to_text(variant).lower()
        
        # Count matches
        present_keywords = set()
        keyword_counts = {}
        
        for kw in required_keywords:
            count = content_text.count(kw.lower())
            if count > 0:
                present_keywords.add(kw)
                keyword_counts[kw] = count
        
        # Base score: % of keywords present
        base_score = (len(present_keywords) / len(required_keywords)) * 100
        
        # Bonus for optimal repetition (2-3x)
        optimal_count = 0
        for kw, count in keyword_counts.items():
            if 2 <= count <= 3:
                optimal_count += 1
        
        if keyword_counts:
            repetition_bonus = (optimal_count / len(keyword_counts)) * 10
        else:
            repetition_bonus = 0
        
        return min(base_score + repetition_bonus, 100.0)
    
    def _score_formatting(self, variant: ResumeVariant, ats_type: ATSType) -> float:
        """
        Score formatting compliance (0-100)
        
        Based on ATS-specific rules
        """
        score = 100.0
        
        # Get ATS-specific rules
        rules = self.ats_detector.get_ats_rules(ats_type)
        
        content_text = self._variant_to_text(variant)
        
        # Check bullet length
        bullets = self._extract_bullets(variant)
        max_length = rules.get("max_bullet_length", 100)
        
        long_bullets = [b for b in bullets if len(b) > max_length]
        if long_bullets:
            penalty = (len(long_bullets) / len(bullets)) * 20 if bullets else 0
            score -= penalty
        
        # Check for special characters (if ATS requires simple formatting)
        if rules.get("avoid_special_chars"):
            special_chars = re.findall(r'[^\w\s\-.,;:()\[\]]', content_text)
            if special_chars:
                score -= min(len(special_chars) * 2, 15)
        
        return max(score, 0.0)
    
    def _score_structure(self, variant: ResumeVariant) -> float:
        """
        Score document structure (0-100)
        """
        score = 100.0
        
        content = variant.content
        
        # Must have key sections
        required_sections = ["resumo", "experiencias", "habilidades"]
        missing = [s for s in required_sections if s not in content or not content[s]]
        
        if missing:
            score -= len(missing) * 20
        
        # Experiences should have bullets
        if "experiencias" in content:
            for exp in content["experiencias"]:
                if not exp.get("bullets"):
                    score -= 10
        
        # Habilidades should have 3-5 items
        if "habilidades" in content:
            skill_count = len(content["habilidades"])
            if skill_count < 3:
                score -= 15
            elif skill_count > 7:
                score -= 10
        
        return max(score, 0.0)
    
    def _score_checklist(self, variant: ResumeVariant, job: Job) -> float:
        """
        Score against ATS-specific checklist (0-100)
        """
        checklist_items = self.ats_detector.get_ats_rules(job.ats_detectado)
        
        # Simplified scoring based on rules
        score = 100.0
        
        # Keywords check
        kw_score = self._score_keywords(variant, job)
        if kw_score < 80:
            score -= 20
        
        # Metrics check (prefers quantifiable results)
        if checklist_items.get("prefers_metrics"):
            content_text = self._variant_to_text(variant)
            # Look for numbers/percentages
            metrics = re.findall(r'\d+%|\d+\+|\d+ [a-z]+', content_text)
            if len(metrics) < 3:
                score -= 15
        
        return max(score, 0.0)
    
    def _variant_to_text(self, variant: ResumeVariant) -> str:
        """Convert variant to plain text"""
        import json
        return json.dumps(variant.content, ensure_ascii=False)
    
    def _extract_bullets(self, variant: ResumeVariant) -> List[str]:
        """Extract all bullet points from variant"""
        bullets = []
        
        if "experiencias" in variant.content:
            for exp in variant.content["experiencias"]:
                if "bullets" in exp:
                    bullets.extend(exp["bullets"])
        
        return bullets
    
    def _generate_motivos(self, scores: Dict[str, float], job: Job) -> List[str]:
        """Generate reasons for score"""
        motivos = []
        
        if scores["keywords"] < 70:
            motivos.append("Faltam keywords importantes da vaga")
        
        if scores["formatting"] < 80:
            motivos.append("Formatação não ideal para o ATS")
        
        if scores["structure"] < 80:
            motivos.append("Estrutura do documento pode ser melhorada")
        
        if scores["checklist"] < 80:
            motivos.append(f"Não atende todos os requisitos do {job.ats_detectado.value}")
        
        if not motivos:
            motivos.append("Currículo bem otimizado!")
        
        return motivos
    
    def _generate_checklist_results(self, variant: ResumeVariant, job: Job) -> Dict[str, bool]:
        """Generate checklist pass/fail"""
        content_text = self._variant_to_text(variant)
        
        # Generic checklist
        checklist = {
            "keywords_present": self._score_keywords(variant, job) >= 80,
            "has_metrics": bool(re.search(r'\d+%|\d+\+', content_text)),
            "bullets_appropriate": len(self._extract_bullets(variant)) >= 3,
            "structure_complete": all(
                k in variant.content for k in ["resumo", "experiencias", "habilidades"]
            )
        }
        
        return checklist
