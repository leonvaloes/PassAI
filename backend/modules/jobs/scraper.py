"""
Job Scraper - Base Class
Abstract scraper for job boards
"""
import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.rate_limit_delay = 1  # seconds
        self.last_request_time = 0
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with rate limiting"""
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30, allow_redirects=True)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching {url}: {e}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')
    
    @abstractmethod
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """
        Extract job data from URL.
        Must be implemented by subclasses.
        
        Returns dict with fields:
        - title
        - company
        - location
        - description
        - salary (if available)
        - etc.
        """
        pass
    
    def extract_text(self, element, selector: str, method: str = 'css') -> Optional[str]:
        """Extract text from element using CSS or XPath selector"""
        try:
            if method == 'css':
                found = element.select_one(selector)
            elif method == 'xpath':
                # BeautifulSoup doesn't support XPath directly
                # Would need lxml for full XPath support
                logger.warning("XPath not fully supported, using CSS fallback")
                return None
            else:
                return None
            
            if found:
                return found.get_text(strip=True)
            return None
        
        except Exception as e:
            logger.error(f"Error extracting with selector '{selector}': {e}")
            return None
    
    def extract_elements(self, element, selector: str) -> List:
        """Extract multiple elements"""
        try:
            return element.select(selector)
        except Exception as e:
            logger.error(f"Error extracting elements with selector '{selector}': {e}")
            return []
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text"""
        if not text:
            return None
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')
        
        return text.strip()


class ScraperRegistry:
    """Registry for domain-specific scrapers"""
    
    _scrapers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, domain: str, scraper_class: type):
        """Register a scraper for a domain"""
        cls._scrapers[domain] = scraper_class
        logger.info(f"Registered scraper for: {domain}")
    
    @classmethod
    def get_scraper(cls, url: str) -> Optional[BaseScraper]:
        """Get appropriate scraper for URL"""
        domain = urlparse(url).netloc
        
        # Try exact match
        if domain in cls._scrapers:
            return cls._scrapers[domain]()
        
        # Try partial match (e.g., jobs.linkedin.com -> linkedin.com)
        for registered_domain, scraper_class in cls._scrapers.items():
            if registered_domain in domain:
                return scraper_class()
        
        logger.warning(f"No scraper found for domain: {domain}")
        return None
    
    @classmethod
    def list_domains(cls) -> List[str]:
        """List all registered domains"""
        return list(cls._scrapers.keys())
