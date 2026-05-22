"""
Search Engine - Job Aggregator
Executes saved search profiles across multiple sources
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.jobs.models import (
    SearchProfile, CrawlRun, CrawlRunStats, CrawlError,
    CrawlRunStatus, JobPosting
)
from modules.jobs.database import JobsDatabase
from modules.jobs.scraper import ScraperRegistry
from modules.jobs.enricher import enrich_job_with_ai

logger = logging.getLogger(__name__)


class SearchEngine:
    """Executes job searches based on saved profiles"""
    
    def __init__(self, jobs_db: JobsDatabase, llm_router):
        self.jobs_db = jobs_db
        self.llm_router = llm_router
        
        # Configuration
        self.max_concurrent_scrapers = 3
        self.timeout_per_job = 120  # 2 minutes
        self.max_job_age_days = 14
    
    def execute_search(
        self,
        profile: SearchProfile,
        sources: Optional[List[str]] = None
    ) -> str:
        """
        Execute search for a given profile
        
        Returns: crawl_run_id
        """
        # Create crawl run record
        crawl_run = CrawlRun(
            profileId=str(profile.dict().get('_id', 'unknown')),
            profileName=profile.name,
            status=CrawlRunStatus.RUNNING,
            sources=sources or ["linkedin", "gupy"]  # Default sources
        )
        
        run_id = self.jobs_db.create_crawl_run(crawl_run)
        logger.info(f"🔍 Starting search: {profile.name} (run_id: {run_id})")
        
        start_time = time.time()
        stats = CrawlRunStats()
        errors = []
        
        try:
            # Get job URLs from search (placeholder - would need actual search implementation)
            job_urls = self._search_jobs(profile, sources or ["linkedin", "gupy"])
            
            # Limit to maxJobsPerRun
            job_urls = job_urls[:profile.maxJobsPerRun]
            stats.jobsFound = len(job_urls)
            
            # Scrape jobs in parallel
            scraped_jobs = self._scrape_jobs_parallel(job_urls, stats, errors)
            
            # Save jobs to database
            for job_data in scraped_jobs:
                try:
                    # Enrich with AI - DISABLED AUTOMATICALLY (On-Demand now)
                    # Use simple extractor instead for keywords
                    # enriched = enrich_job_with_ai(job_data, self.llm_router)
                    
                    # Basic cleanup only
                    from modules.jobs.enricher import extract_basic_info
                    enriched = extract_basic_info(job_data)

                    if not self._is_open_for_applications(enriched):
                        logger.info(
                            "Skipping closed job: %s - %s",
                            enriched.get("title"),
                            enriched.get("url"),
                        )
                        stats.jobsFailed += 1
                        continue

                    if not self._is_recent_job(enriched):
                        logger.info(
                            "Skipping stale job: %s - %s",
                            enriched.get("title"),
                            enriched.get("url"),
                        )
                        stats.jobsFailed += 1
                        continue
                    
                    # FILTER: Only save jobs from Brazil (if profile has Brazil country filter)
                    if profile.filters.location and profile.filters.location.country == 'Brazil':
                        job_location = enriched.get('location', {})
                        if isinstance(job_location, dict):
                            job_country = job_location.get('country', '').lower()
                            job_city = job_location.get('city', '').lower()
                            job_state = job_location.get('state', '').lower()
                            
                            # List of US cities/states that might appear
                            us_indicators = [
                                'estados unidos', 'united states', 'usa', 'u.s.',
                                'san francisco', 'são francisco e região',  # SF often confused
                                'new york', 'nova york', 'seattle', 'austin',
                                'boston', 'chicago', 'los angeles', 'denver',
                                'silicon valley', 'bay area',
                                'california', 'califórnia', 'texas', 'washington',
                                'new jersey', 'massachusetts', 'florida'
                            ]
                            
                            # Check if any US indicator is present
                            location_text = f"{job_city} {job_state} {job_country}".lower()
                            if any(indicator in location_text for indicator in us_indicators):
                                logger.info(f"⚠️ Skipping non-Brazil job: {enriched.get('title')} - {location_text.strip()}")
                                stats.jobsFailed += 1
                                continue
                            
                            # Also check if country is explicitly not Brazil
                            if job_country and job_country not in ['brazil', 'brasil', '']:
                                logger.info(f"⚠️ Skipping non-Brazil job: {enriched.get('title')} - country: {job_country}")
                                stats.jobsFailed += 1
                                continue
                    
                    # Ensure URL is string, not HttpUrl
                    url_str = str(enriched.get('url', ''))
                    
                    # Create JobPosting
                    job = JobPosting(
                        url=url_str,
                        title=enriched.get('title'),
                        company=enriched.get('company'),
                        description=enriched.get('description'),
                        location=enriched.get('location'),
                        postedAt=enriched.get('postedAt'),
                        techKeywords=enriched.get('techKeywords', []),
                        seniority=enriched.get('seniority'),
                        mustHave=enriched.get('mustHave', []),
                        niceToHave=enriched.get('niceToHave', []),
                        rawHtml=enriched.get('rawHtml'),
                        rawText=enriched.get('rawText'),
                        extractionMethod="scrape"
                    )
                    
                    # Check if new or updated
                    existing = self.jobs_db.get_job_by_url(str(job.url))
                    if existing:
                        stats.jobsUpdated += 1
                    else:
                        stats.jobsNew += 1
                    
                    self.jobs_db.create_job(job)
                    
                except Exception as e:
                    logger.error(f"Failed to save job: {e}")
                    stats.jobsFailed += 1
            
            # Calculate stats
            elapsed = time.time() - start_time
            stats.avgExtractionTime = (elapsed / stats.jobsFound * 1000) if stats.jobsFound > 0 else 0
            
            # Update crawl run
            self.jobs_db.update_crawl_run(run_id, {
                "status": CrawlRunStatus.COMPLETED.value,
                "finishedAt": datetime.utcnow(),
                "stats": stats.dict(),
                "errors": [e.dict() for e in errors]
            })
            
            logger.info(f"✅ Search completed: {stats.jobsNew} new, {stats.jobsUpdated} updated, {stats.jobsFailed} failed")
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            
            # Mark as failed
            self.jobs_db.update_crawl_run(run_id, {
                "status": CrawlRunStatus.FAILED.value,
                "finishedAt": datetime.utcnow(),
                "errors": [CrawlError(url="", error=str(e)).dict()]
            })
        
        return run_id
    
    def _search_jobs(
        self,
        profile: SearchProfile,
        sources: List[str]
    ) -> List[str]:
        """
        Search for jobs based on profile filters
        
        Returns list of job URLs to scrape
        """
        from modules.jobs.scrapers import linkedin, gupy, indeed, glassdoor, catho
        from modules.jobs.scraper import ScraperRegistry
        
        logger.info(f"Searching across sources: {sources}")
        
        all_job_urls = []
        filters = profile.filters.dict()
        
        # Inject auth config if present
        if profile.authConfig:
            filters['auth_config'] = profile.authConfig.dict()
            
        max_per_source = profile.maxJobsPerRun // len(sources) if sources else profile.maxJobsPerRun
        
        # Map sources to scraper instances
        scraper_map = {
            'linkedin': ScraperRegistry.get_scraper('https://www.linkedin.com'),
            'gupy': ScraperRegistry.get_scraper('https://gupy.io'),
            'indeed': ScraperRegistry.get_scraper('https://br.indeed.com'),
            'glassdoor': ScraperRegistry.get_scraper('https://www.glassdoor.com.br'),
            'catho': ScraperRegistry.get_scraper('https://www.catho.com.br')
        }
        
        for source in sources:
            scraper = scraper_map.get(source)
            
            if not scraper:
                logger.warning(f"No scraper found for source: {source}")
                continue
            
            # Check if scraper has search method
            if not hasattr(scraper, 'search'):
                logger.warning(f"Scraper {source} doesn't support search")
                continue
            
            try:
                # Call scraper's search method
                job_urls = scraper.search(filters, max_jobs=max_per_source)
                
                logger.info(f"{source}: Found {len(job_urls)} jobs")
                all_job_urls.extend(job_urls)
                
            except Exception as e:
                logger.error(f"Search failed for {source}: {e}")
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in all_job_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Total unique jobs found: {len(unique_urls)}")
        
        # Limit to maxJobsPerRun
        return unique_urls[:profile.maxJobsPerRun]

    def _is_open_for_applications(self, job_data: Dict[str, Any]) -> bool:
        """
        Return False when the posting clearly no longer accepts applications.

        Scrapers should still try to return active jobs only, but this final gate
        catches public pages that remain indexed after closing.
        """
        status = str(job_data.get("status", "")).lower()
        if status in {"expired", "filled", "removed", "closed"}:
            return False

        raw_text = " ".join(
            str(job_data.get(key) or "")
            for key in ("rawText", "description", "title")
        ).lower()

        closed_phrases = [
            "vaga encerrada",
            "vaga expirada",
            "vaga fechada",
            "posição encerrada",
            "processo seletivo encerrado",
            "não aceita mais candidaturas",
            "não estamos mais aceitando candidaturas",
            "não estamos mais recebendo candidaturas",
            "não é mais possível se candidatar",
            "applications are no longer being accepted",
            "no longer accepting applications",
            "job is no longer available",
            "this job is no longer available",
            "position has been filled",
            "não encontramos essa vaga",
            "esta vaga não está mais disponível",
        ]
        if any(phrase in raw_text for phrase in closed_phrases):
            return False

        open_phrases = [
            "candidatar-se",
            "candidate-se",
            "candidatar",
            "apply now",
            "easy apply",
            "cadastre-se para se candidatar",
        ]
        if any(phrase in raw_text for phrase in open_phrases):
            return True

        # Unknown status is allowed, but with lower confidence. Some Brazilian
        # portals hide application buttons behind scripts or login walls.
        return True

    def _is_recent_job(self, job_data: Dict[str, Any]) -> bool:
        """Keep only jobs posted recently enough for application priority."""
        posted_at = job_data.get("postedAt")
        if isinstance(posted_at, datetime):
            return posted_at >= datetime.utcnow() - timedelta(days=self.max_job_age_days)

        raw_text = " ".join(
            str(job_data.get(key) or "")
            for key in ("rawText", "description", "title")
        ).lower()

        age_days = self._extract_age_days(raw_text)
        if age_days is None:
            return True

        return age_days <= self.max_job_age_days

    def _extract_age_days(self, text: str) -> Optional[int]:
        """Extract relative age from common PT-BR/EN job-board labels."""
        text = text.lower()

        if any(token in text for token in ["hoje", "today", "agora", "just now"]):
            return 0
        if any(token in text for token in ["ontem", "yesterday"]):
            return 1

        patterns = [
            (r"há\s+(\d+)\s+dias?", 1),
            (r"(\d+)\s+dias?\s+atrás", 1),
            (r"(\d+)\s+days?\s+ago", 1),
            (r"há\s+(\d+)\s+semanas?", 7),
            (r"(\d+)\s+semanas?\s+atrás", 7),
            (r"(\d+)\s+weeks?\s+ago", 7),
            (r"há\s+(\d+)\s+mes(?:es)?", 30),
            (r"(\d+)\s+months?\s+ago", 30),
        ]

        matches = []
        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, text):
                try:
                    matches.append((match.start(), int(match.group(1)) * multiplier))
                except ValueError:
                    continue

        if not matches:
            return None

        # Use the first age shown on the page. LinkedIn and other aggregators
        # include "similar jobs" later in the HTML, so picking the newest match
        # would let stale primary postings slip through.
        return sorted(matches, key=lambda item: item[0])[0][1]
    
    def _scrape_jobs_parallel(
        self,
        job_urls: List[str],
        stats: CrawlRunStats,
        errors: List[CrawlError]
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple jobs in parallel
        
        Returns list of scraped job data
        """
        scraped_jobs = []
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_scrapers) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(self._scrape_single_job, url): url
                for url in job_urls
            }
            
            # Collect results
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                
                try:
                    job_data = future.result(timeout=self.timeout_per_job)
                    
                    if job_data and "error" not in job_data:
                        scraped_jobs.append(job_data)
                    else:
                        error_msg = job_data.get("error", "Unknown error") if job_data else "No data"
                        errors.append(CrawlError(url=url, error=error_msg))
                        stats.jobsFailed += 1
                
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    errors.append(CrawlError(url=url, error=str(e)))
                    stats.jobsFailed += 1
        
        return scraped_jobs
    
    def _scrape_single_job(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single job URL
        
        Returns job data dict or None
        """
        try:
            # Get appropriate scraper
            scraper = ScraperRegistry.get_scraper(url)
            
            if not scraper:
                return {"error": f"No scraper for domain"}
            
            # Scrape
            job_data = scraper.extract_job_data(url)
            
            return job_data
        
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return {"error": str(e)}


def create_search_engine(jobs_db: JobsDatabase, llm_router) -> SearchEngine:
    """Factory function to create search engine"""
    return SearchEngine(jobs_db, llm_router)
