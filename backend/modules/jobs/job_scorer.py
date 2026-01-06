"""
Job Scorer - AI-powered job matching and ranking
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class JobScore(BaseModel):
    """Score for a job posting relative to user profile"""
    overall_score: float  # 0-100
    skill_match_pct: float  # 0-100, percentage of required skills user has
    matched_skills: List[str]
    missing_skills: List[str]
    seniority_match: bool
    salary_estimate: Optional[Dict[str, Any]] = None
    match_reasons: List[str]
    concerns: List[str]


class JobScorer:
    """Calculate compatibility scores between user profile and jobs"""
    
    def __init__(self, llm_router):
        self.llm_router = llm_router
    
    def score_job(self, job: Dict[str, Any], user_profile: Dict[str, Any], use_llm: bool = True) -> JobScore:
        """
        Calculate overall match score for a job
        
        Args:
            job: JobPosting as dict
            user_profile: User CV/profile data
            use_llm: Whether to use AI for deep analysis (default: True)
            
        Returns:
            JobScore with compatibility metrics
        """
        try:
            # Extract data
            job_skills = set(job.get('techKeywords', []))
            job_title = job.get('title', '')
            job_description = job.get('description', '')
            job_seniority = job.get('seniority', 'pleno')
            
            user_skills = set(user_profile.get('skills', []))
            user_seniority = user_profile.get('seniority', 'pleno')
            user_experience_years = user_profile.get('experience_years', 3)
            
            # Calculate skill match
            if job_skills:
                matched = job_skills & user_skills
                missing = job_skills - user_skills
                skill_match_pct = (len(matched) / len(job_skills)) * 100
            else:
                matched = set()
                missing = set()
                skill_match_pct = 50.0  # neutral if no skills specified
            
            # Seniority match
            seniority_levels = {'junior': 1, 'pleno': 2, 'senior': 3, 'especialista': 4}
            job_level = seniority_levels.get(job_seniority.lower() if job_seniority else 'pleno', 2)
            user_level = seniority_levels.get(user_seniority.lower(), 2)
            seniority_match = abs(job_level - user_level) <= 1
            
            # Use LLM (or fallback for performance)
            if use_llm:
                llm_analysis = self._analyze_with_llm(job, user_profile)
                
                # Calculate overall score (weighted average)
                overall_score = (
                    skill_match_pct * 0.4 +  # 40% weight on skills
                    llm_analysis['compatibility_score'] * 0.4 +  # 40% on LLM analysis
                    (100 if seniority_match else 50) * 0.2  # 20% on seniority
                )
            else:
                # Lightweight Scoring (No LLM)
                llm_analysis = {
                    'compatibility_score': 0,
                    'pros': [],
                    'cons': [],
                    'salary_estimate': None
                }
                
                # Re-distribute weights: 70% Skills, 30% Seniority
                overall_score = (
                    skill_match_pct * 0.7 +
                    (100 if seniority_match else 50) * 0.3
                )
            
            # Build match reasons
            match_reasons = []
            if skill_match_pct >= 70:
                match_reasons.append(f"Strong skill match: {len(matched)}/{len(job_skills)} required skills")
            if seniority_match:
                match_reasons.append(f"Seniority level aligned ({job_seniority})")
            if use_llm:
                match_reasons.extend(llm_analysis.get('pros', []))
            
            # Build concerns
            concerns = []
            if skill_match_pct < 50:
                concerns.append(f"Missing {len(missing)} key skills: {', '.join(list(missing)[:3])}")
            if not seniority_match:
                concerns.append(f"Seniority mismatch (job: {job_seniority}, you: {user_seniority})")
            if use_llm:
                concerns.extend(llm_analysis.get('cons', []))
            
            # Salary estimate
            salary_estimate = llm_analysis.get('salary_estimate')
            
            return JobScore(
                overall_score=round(overall_score, 1),
                skill_match_pct=round(skill_match_pct, 1),
                matched_skills=list(matched),
                missing_skills=list(missing),
                seniority_match=seniority_match,
                salary_estimate=salary_estimate,
                match_reasons=match_reasons[:3],
                concerns=concerns[:3]
            )
            
        except Exception as e:
            logger.error(f"Failed to score job: {e}")
            # Return neutral score on error
            return JobScore(
                overall_score=50.0,
                skill_match_pct=50.0,
                matched_skills=[],
                missing_skills=[],
                seniority_match=True,
                match_reasons=["Unable to calculate detailed match"],
                concerns=[]
            )
    
    def _analyze_with_llm(self, job: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to deeply analyze job-user compatibility"""
        try:
            prompt = f"""Analyze this job opportunity for the candidate.

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:800]}
Required Skills: {', '.join(job.get('techKeywords', []))}
Seniority: {job.get('seniority')}

CANDIDATE:
Experience: {user_profile.get('experience_years', 3)} years
Skills: {', '.join(user_profile.get('skills', []))}
Seniority: {user_profile.get('seniority', 'pleno')}
Background: {user_profile.get('summary', '')}

INSTRUCTIONS:
You are a JSON-only API. You must return a valid JSON object.
Do not output any markdown, explanations, or introductory text.

REQUIRED JSON FORMAT:
{{
  "compatibility_score": 85,
  "pros": ["reason1", "reason2"],
  "cons": ["concern1", "concern2"],
  "salary_estimate": {{"min": 8000, "max": 12000, "currency": "BRL"}}
}}
"""
            
            response = self.llm_router.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
                seed=42
            )
            
            # Parse JSON response
            import json
            
            try:
                # Robust JSON extraction: Find first '{' and last '}'
                text = response.strip()
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = text[start_idx : end_idx + 1]
                    result = json.loads(json_str)
                    return result
                else:
                    logger.warning(f"No JSON object found in response: {text[:100]}...")
                    raise ValueError("No JSON found")

            except (json.JSONDecodeError, ValueError) as e:
                # Fallback and LOG THE ERROR content
                logger.warning(f"LLM response not valid JSON: {e}")
                logger.warning(f"Raw response was: {response[:500]}...") # Log first 500 chars
                
                return {
                    'compatibility_score': 70,
                    'pros': ["General experience match"],
                    'cons': ["Requires detailed review"],
                    'salary_estimate': {'min': 5000, 'max': 10000, 'currency': 'BRL'}
                }
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                'compatibility_score': 60,
                'pros': [],
                'cons': [],
                'salary_estimate': None
            }
