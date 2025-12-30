"""
Ranker - Multi-criteria ranking of resume variants
"""
import logging
from typing import List, Dict
from database.models import ResumeVariant, Job

logger = logging.getLogger(__name__)


class Ranker:
    """
    Multi-criteria Resume Ranker
    
    Ranks variants by:
    - ATS score (40%)
    - Clarity (15%)
    - Impact (15%)
    - Concision (10%)
    - Seniority match (10%)
    - Naturalness (10%)
    """
    
    # Ranking weights (can be learned over time)
    WEIGHTS = {
        "ats_score": 0.40,
        "clarity": 0.15,
        "impact": 0.15,
        "concision": 0.10,
        "seniority_match": 0.10,
        "naturalness": 0.10
    }
    
    def __init__(self, config: Dict = None):
        """
        Initialize Ranker
        
        Args:
            config: Optional config with custom weights
        """
        if config and "ranking_weights" in config:
            self.WEIGHTS.update(config["ranking_weights"])
    
    def rank(self, variants: List[ResumeVariant], job: Job) -> List[ResumeVariant]:
        """
        Rank variants by overall quality
        
        Args:
            variants: List of variants to rank
            job: Job posting for context
        
        Returns:
            Sorted list (best first)
        """
        logger.info(f"Ranking {len(variants)} variants")
        
        # Calculate ranking score for each
        for variant in variants:
            variant.ranking_score = self._calculate_ranking_score(variant, job)
        
        # Sort by ranking score (descending)
        ranked = sorted(variants, key=lambda v: v.ranking_score, reverse=True)
        
        # Assign positions
        for i, variant in enumerate(ranked):
            variant.ranking_position = i + 1
        
        logger.info(f"Top 3 scores: {[v.ranking_score for v in ranked[:3]]}")
        
        return ranked
    
    def _calculate_ranking_score(self, variant: ResumeVariant, job: Job) -> float:
        """Calculate final ranking score (0-100)"""
        
        scores = {
            "ats_score": variant.ats_score / 100,  # Normalize to 0-1
            "clarity": self._score_clarity(variant),
            "impact": self._score_impact(variant),
            "concision": self._score_concision(variant),
            "seniority_match": self._score_seniority_match(variant, job),
            "naturalness": self._score_naturalness(variant)
        }
        
        # Weighted average
        final = sum(scores[k] * self.WEIGHTS[k] for k in scores) * 100
        
        return final
    
    def _score_clarity(self, variant: ResumeVariant) -> float:
        """
        Score clarity (0-1)
        
        Clear = easy to scan, well organized
        """
        score = 1.0
        
        # Check if sections are present
        content = variant.content
        
        # Resumo should be concise (not too long)
        if "resumo_linha_1" in content:
            if len(content["resumo_linha_1"]) > 150:
                score -= 0.2
        
        # Bullets should be clear and not too long
        if "experiencias" in content:
            for exp in content["experiencias"]:
                if "bullets" in exp:
                    for bullet in exp["bullets"]:
                        if len(bullet) > 100:
                            score -= 0.05
        
        return max(score, 0.0)
    
    def _score_impact(self, variant: ResumeVariant) -> float:
        """
        Score impact (0-1)
        
        High impact = quantifiable results, strong verbs
        """
        import re
        
        content_text = str(variant.content)
        
        # Count metrics (numbers, percentages)
        metrics = re.findall(r'\d+%|\d+\+|\d+ [a-z]+', content_text)
        metric_score = min(len(metrics) / 10, 0.5)  # Max 0.5 for metrics
        
        # Count action verbs (simplified)
        action_verbs = [
            "desenvolveu", "criou", "implementou", "liderou", "otimizou",
            "aumentou", "reduziu", "gerenciou", "coordenou", "projetou"
        ]
        
        verb_count = sum(1 for verb in action_verbs if verb in content_text.lower())
        verb_score = min(verb_count / 10, 0.5)  # Max 0.5 for verbs
        
        return metric_score + verb_score
    
    def _score_concision(self, variant: ResumeVariant) -> float:
        """
        Score concision (0-1)
        
        Concise = not too wordy, gets to the point
        """
        import json
        
        content_text = json.dumps(variant.content, ensure_ascii=False)
        char_count = len(content_text)
        
        # Ideal range: 2000-3500 characters
        if 2000 <= char_count <= 3500:
            return 1.0
        elif char_count < 2000:
            return 0.7  # Too short
        else:
            # Too long - penalty
            excess = char_count - 3500
            penalty = min(excess / 1000 * 0.3, 0.5)
            return max(0.5, 1.0 - penalty)
    
    def _score_seniority_match(self, variant: ResumeVariant, job: Job) -> float:
        """
        Score seniority match (0-1)
        
        Does the resume match the job's seniority level?
        """
        # Simplified: check if senioridade keywords match
        content_text = str(variant.content).lower()
        
        if not job.senioridade:
            return 1.0  # No requirement
        
        seniority_map = {
            "junior": ["júnior", "junior", "iniciante"],
            "pleno": ["pleno", "intermediário"],
            "senior": ["sênior", "senior", "especialista", "expert"],
            "especialista": ["especialista", "expert", "principal"]
        }
        
        target_keywords = seniority_map.get(job.senioridade.lower(), [])
        
        for kw in target_keywords:
            if kw in content_text:
                return 1.0
        
        return 0.5  # Neutral if not mentioned
    
    def _score_naturalness(self, variant: ResumeVariant) -> float:
        """
        Score naturalness (0-1)
        
        Natural = doesn't sound robotic or keyword-stuffed
        """
        content_text = str(variant.content).lower()
        
        # Check for keyword stuffing (same word repeated too many times)
        words = content_text.split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only count meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # If any word appears > 5 times, it's likely stuffed
        max_freq = max(word_freq.values()) if word_freq else 0
        
        if max_freq > 5:
            return 0.5
        elif max_freq > 3:
            return 0.8
        else:
            return 1.0
    
    def get_top_n(self, variants: List[ResumeVariant], n: int = 3) -> List[ResumeVariant]:
        """Get top N variants"""
        sorted_variants = sorted(variants, key=lambda v: v.ranking_score, reverse=True)
        return sorted_variants[:n]
