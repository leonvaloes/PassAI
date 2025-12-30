"""
ATS Detector - Detect ATS system with continuous learning
"""
import logging
from typing import Optional, Dict
from urllib.parse import urlparse
from database.models import ATSType
from database.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class ATSDetector:
    """
    ATS Detection System with Continuous Learning
    
    Detection hierarchy:
    1. Learned patterns (MongoDB)
    2. URL patterns
    3. Text patterns
    4. Unknown fallback
    """
    
    # Initial ATS patterns (seed data)
    URL_PATTERNS = {
        ATSType.GUPY: [
            "gupy.io",
            "vemprogupy.com",
            "gupy.com.br"
        ],
        ATSType.GREENHOUSE: [
            "greenhouse.io",
            "boards.greenhouse.io"
        ],
        ATSType.LEVER: [
            "lever.co",
            "jobs.lever.co"
        ],
        ATSType.WORKDAY: [
            "myworkdayjobs.com",
            "wd1.myworkdayjobs.com",
            "workday.com/jobs"
        ],
        ATSType.TALEO: [
            "taleo.net",
            "oracletaleo.com"
        ]
    }
    
    TEXT_PATTERNS = {
        ATSType.GUPY: [
            "powered by gupy",
            "candidatar-se agora",
            "aplicar na gupy",
            "vemprogupy"
        ],
        ATSType.GREENHOUSE: [
            "powered by greenhouse",
            "greenhouse software",
            "submit application"
        ],
        ATSType.LEVER: [
            "powered by lever",
            "apply for this job"
        ],
        ATSType.WORKDAY: [
            "powered by workday",
            "workday recruiting"
        ],
        ATSType.TALEO: [
            "powered by taleo",
            "oracle taleo"
        ]
    }
    
    def __init__(self):
        """Initialize ATS Detector"""
        self.db = get_mongodb()
    
    def detect(
        self, 
        empresa: str, 
        url: Optional[str] = None, 
        text: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Detect ATS system
        
        Args:
            empresa: Company name
            url: Job posting URL (optional)
            text: Job posting text (optional)
        
        Returns:
            {
                "ats_type": ATSType,
                "confidence": float (0-1),
                "source": "learned|url|text|unknown"
            }
        """
        logger.info(f"Detecting ATS for: {empresa}")
        
        # 1. Check learned patterns (highest priority)
        learned = self._check_learned_patterns(empresa)
        if learned:
            logger.info(f"✅ ATS detected from learned patterns: {learned['ats_type'].value}")
            return learned
        
        # 2. Check URL patterns
        if url:
            url_result = self._check_url_patterns(url)
            if url_result["ats_type"] != ATSType.UNKNOWN:
                logger.info(f"✅ ATS detected from URL: {url_result['ats_type'].value}")
                return url_result
        
        # 3. Check text patterns
        if text:
            text_result = self._check_text_patterns(text)
            if text_result["ats_type"] != ATSType.UNKNOWN:
                logger.info(f"✅ ATS detected from text: {text_result['ats_type'].value}")
                return text_result
        
        # 4. Unknown
        logger.warning(f"⚠️ Could not detect ATS for: {empresa}")
        return {
            "ats_type": ATSType.UNKNOWN,
            "confidence": 0.0,
            "source": "unknown"
        }
    
    def _check_learned_patterns(self, empresa: str) -> Optional[Dict]:
        """Check MongoDB for learned patterns"""
        pattern = self.db.get_ats_pattern(empresa.lower())
        
        if pattern and pattern.get("confirmed_count", 0) > 0:
            return {
                "ats_type": ATSType(pattern["ats_type"]),
                "confidence": min(pattern["confirmed_count"] / 5.0, 1.0),  # Max confidence at 5 confirmations
                "source": "learned"
            }
        
        return None
    
    def _check_url_patterns(self, url: str) -> Dict:
        """Check URL for ATS patterns"""
        domain = urlparse(url).netloc.lower()
        
        for ats_type, patterns in self.URL_PATTERNS.items():
            for pattern in patterns:
                if pattern in domain:
                    return {
                        "ats_type": ats_type,
                        "confidence": 0.9,  # High confidence for URL matches
                        "source": "url"
                    }
        
        return {
            "ats_type": ATSType.UNKNOWN,
            "confidence": 0.0,
            "source": "url"
        }
    
    def _check_text_patterns(self, text: str) -> Dict:
        """Check text for ATS patterns"""
        text_lower = text.lower()
        
        # Score each ATS type
        scores = {ats: 0 for ats in ATSType}
        
        for ats_type, patterns in self.TEXT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    scores[ats_type] += 1
        
        # Get best match
        best_ats = max(scores.items(), key=lambda x: x[1])
        
        if best_ats[1] > 0:
            return {
                "ats_type": best_ats[0],
                "confidence": min(best_ats[1] / 2.0, 0.8),  # Max 0.8 confidence for text
                "source": "text"
            }
        
        return {
            "ats_type": ATSType.UNKNOWN,
            "confidence": 0.0,
            "source": "text"
        }
    
    def confirm_ats(
        self,
        empresa: str,
        ats_type: ATSType,
        url: Optional[str] = None
    ):
        """
        User confirms/corrects ATS detection
        
        This is the learning mechanism - each confirmation
        strengthens the pattern
        
        Args:
            empresa: Company name
            ats_type: Confirmed ATS type
            url: Optional URL to extract patterns
        """
        logger.info(f"Confirming ATS for {empresa}: {ats_type.value}")
        
        # Extract patterns from URL if provided
        url_patterns = []
        if url:
            domain = urlparse(url).netloc
            url_patterns.append(domain)
        
        # Update MongoDB
        self.db.update_ats_pattern(empresa.lower(), ats_type.value)
        
        # If URL patterns found, add to learned patterns
        if url_patterns:
            pattern = self.db.get_ats_pattern(empresa.lower())
            if pattern:
                existing = pattern.get("url_patterns", [])
                updated = list(set(existing + url_patterns))
                
                self.db.ats_patterns.update_one(
                    {"empresa": empresa.lower()},
                    {"$set": {"url_patterns": updated}}
                )
        
        logger.info(f"✅ ATS pattern learned for {empresa}")
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        total_patterns = self.db.ats_patterns.count_documents({})
        
        # Count by ATS type
        ats_counts = {}
        for ats_type in ATSType:
            count = self.db.ats_patterns.count_documents({"ats_type": ats_type.value})
            if count > 0:
                ats_counts[ats_type.value] = count
        
        return {
            "total_learned_companies": total_patterns,
            "by_ats": ats_counts
        }
    
    def suggest_correction(
        self,
        empresa: str,
        detected: ATSType,
        confidence: float
    ) -> bool:
        """
        Should we ask user for confirmation?
        
        Returns True if confidence is low and user input is needed
        """
        # Ask if:
        # - Unknown ATS
        # - Low confidence (< 0.7)
        # - First time seeing this company
        
        if detected == ATSType.UNKNOWN:
            return True
        
        if confidence < 0.7:
            return True
        
        # Check if we have learned pattern
        pattern = self.db.get_ats_pattern(empresa.lower())
        if not pattern:
            return True  # First time, confirm
        
        return False
    
    def get_ats_rules(self, ats_type: ATSType) -> Dict:
        """
        Get ATS-specific rules and preferences
        
        These will be used by the ATS Simulator
        """
        RULES = {
            ATSType.GUPY: {
                "max_bullet_length": 80,
                "prefers_metrics": True,
                "keyword_repetition": (2, 3),  # Min, Max
                "formatting": "simple",
                "avoid_images": True,
                "avoid_tables": True
            },
            ATSType.GREENHOUSE: {
                "max_bullet_length": 100,
                "prefers_metrics": True,
                "keyword_repetition": (1, 2),
                "formatting": "simple",
                "chronological_order": True
            },
            ATSType.LEVER: {
                "max_bullet_length": 90,
                "prefers_metrics": False,
                "keyword_repetition": (2, 3),
                "formatting": "flexible"
            },
            ATSType.WORKDAY: {
                "max_bullet_length": 120,
                "prefers_metrics": True,
                "keyword_repetition": (1, 2),
                "formatting": "structured",
                "section_headers_required": True
            },
            ATSType.TALEO: {
                "max_bullet_length": 100,
                "prefers_metrics": True,
                "keyword_repetition": (2, 4),
                "formatting": "simple",
                "avoid_special_chars": True
            },
            ATSType.UNKNOWN: {
                "max_bullet_length": 90,
                "prefers_metrics": True,
                "keyword_repetition": (2, 3),
                "formatting": "simple"
            }
        }
        
        return RULES.get(ats_type, RULES[ATSType.UNKNOWN])
