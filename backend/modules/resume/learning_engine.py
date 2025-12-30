"""
Learning Engine - Continuous improvement from user feedback
"""
import logging
from typing import Dict, List
from database.models import ResumeVariant
from database.mongodb import get_mongodb
from datetime import datetime

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Learning Engine for Resume Generator
    
    Learns from:
    - User choosing variants
    - User approving/rejecting variants
    - User correcting ATS detection
    
    Adapts:
    - Ranking weights
    - Generation parameters
    - Content preferences
    """
    
    def __init__(self, ranker):
        """
        Initialize Learning Engine
        
        Args:
            ranker: Ranker instance (to update weights)
        """
        self.ranker = ranker
        self.db = get_mongodb()
    
    def record_decision(
        self,
        variant_id: str,
        action: str,
        feedback: str = None
    ):
        """
        Record user decision on a variant
        
        Args:
            variant_id: Variant ObjectId
            action: "chosen" | "approved" | "rejected"
            feedback: Optional user feedback text
        """
        logger.info(f"Recording decision: {action} for variant {variant_id}")
        
        # Save to MongoDB
        self.db.record_decision(variant_id, action, feedback)
        
        # Learn from decision
        if action == "chosen":
            self._learn_from_chosen(variant_id)
        elif action == "approved":
            self._learn_from_approved(variant_id)
        elif action == "rejected":
            self._learn_from_rejected(variant_id)
    
    def _learn_from_chosen(self, variant_id: str):
        """
        Learn from a variant being chosen
        
        Analyze characteristics of chosen variants to adjust weights
        """
        # Get variant
        variant_data = self.db.variants.find_one({"_id": variant_id})
        
        if not variant_data:
            return
        
        # Analyze what made this variant good
        # Get all chosen variants
        all_chosen = list(self.db.decisions.find({"action": "chosen"}))
        
        if len(all_chosen) < 5:
            logger.info("Not enough data to learn (need 5+ decisions)")
            return
        
        # Analyze patterns
        # TODO: More sophisticated learning
        # For MVP, just log
        logger.info(f"Learning from chosen variant. Total chosen: {len(all_chosen)}")
    
    def _learn_from_approved(self, variant_id: str):
        """Learn from approval"""
        # Positive signal - variant was good
        logger.info(f"Variant {variant_id} approved")
    
    def _learn_from_rejected(self, variant_id: str):
        """Learn from rejection"""
        # Negative signal - avoid similar patterns
        logger.info(f"Variant {variant_id} rejected")
    
    def get_insights(self) -> Dict:
        """
        Get learning insights
        
        Returns statistics about user preferences
        """
        total_decisions = self.db.decisions.count_documents({})
        
        if total_decisions == 0:
            return {"message": "No decisions yet"}
        
        # Count by action
        chosen_count = self.db.decisions.count_documents({"action": "chosen"})
        approved_count = self.db.decisions.count_documents({"action": "approved"})
        rejected_count = self.db.decisions.count_documents({"action": "rejected"})
        
        # Analyze chosen variants
        chosen_variants = []
        for decision in self.db.decisions.find({"action": "chosen"}):
            variant = self.db.variants.find_one({"_id": decision["variant_id"]})
            if variant:
                chosen_variants.append(variant)
        
        # Calculate averages
        if chosen_variants:
            avg_ats_score = sum(v.get("ats_score", 0) for v in chosen_variants) / len(chosen_variants)
            avg_ranking_score = sum(v.get("ranking_score", 0) for v in chosen_variants) / len(chosen_variants)
        else:
            avg_ats_score = 0
            avg_ranking_score = 0
        
        return {
            "total_decisions": total_decisions,
            "chosen": chosen_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "chosen_avg_ats_score": avg_ats_score,
            "chosen_avg_ranking_score": avg_ranking_score
        }
    
    def suggest_adjustments(self) -> List[str]:
        """
        Suggest adjustments based on learning
        
        Returns list of suggestions
        """
        insights = self.get_insights()
        suggestions = []
        
        if insights.get("total_decisions", 0) < 5:
            suggestions.append("Precisa de mais decisões (mínimo 5) para sugerir ajustes")
            return suggestions
        
        # Analyze patterns
        rejection_rate = insights.get("rejected", 0) / insights.get("total_decisions", 1)
        
        if rejection_rate > 0.5:
            suggestions.append("Alta taxa de rejeição - considere ajustar geração de conteúdo")
        
        avg_ats = insights.get("chosen_avg_ats_score", 0)
        if avg_ats < 90:
            suggestions.append("Scores ATS abaixo do ideal - focar em keywords")
        
        return suggestions or ["Sistema funcionando bem, sem ajustes necessários"]
