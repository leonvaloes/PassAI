"""
Gupy Job Scraper
Connector for Gupy recruiting platform
"""
import logging
import re
from typing import Dict, Any, Optional
from modules.jobs.scraper import BaseScraper, ScraperRegistry

logger = logging.getLogger(__name__)


class GupyScraper(BaseScraper):
    """Scraper for Gupy job postings"""
    
    def search(self, filters: Dict[str, Any], max_jobs: int = 50) -> list:
        """Gupy doesn't have unified search - skip"""
        logger.info("Gupy: No global search (per-company only)")
        return []
    
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """Extract job data from Gupy URL"""
        html = self.fetch_page(url)
        
        if not html:
            return {
                "url": url,
                "error": "Failed to fetch page"
            }
        
        soup = self.parse_html(html)
        
        # Gupy often uses JSON-LD structured data
        json_data = self._try_extract_json_ld(soup)
        
        if json_data:
            data = self._parse_json_ld(json_data, url)
        else:
            # Fallback to HTML parsing
            data = {
                "url": url,
                "title": self._extract_title(soup),
                "company": self._extract_company(soup),
                "location": self._extract_location(soup),
                "description": self._extract_description(soup),
                "rawHtml": html,
                "rawText": soup.get_text(separator=' ', strip=True)
            }
        
        # Clean all string values
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.clean_text(value)
        
        logger.info(f"✅ Extracted Gupy job: {data.get('title', 'Unknown')}")
        
        return data
    
    def _try_extract_json_ld(self, soup) -> Optional[Dict]:
        """Try to extract JSON-LD structured data"""
        try:
            import json
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                return json.loads(script_tag.string)
        except Exception as e:
            logger.debug(f"No JSON-LD found: {e}")
        return None
    
    def _parse_json_ld(self, json_data: Dict, url: str) -> Dict[str, Any]:
        """Parse JSON-LD structured data"""
        return {
            "url": url,
            "title": json_data.get('title'),
            "company": json_data.get('hiringOrganization', {}).get('name'),
            "location": json_data.get('jobLocation', {}).get('address', {}).get('addressLocality'),
            "description": json_data.get('description'),
            "salary": self._parse_salary_from_json(json_data)
        }
    
    def _parse_salary_from_json(self, json_data: Dict) -> Optional[Dict]:
        """Parse salary from JSON-LD"""
        base_salary = json_data.get('baseSalary', {})
        if base_salary:
            value = base_salary.get('value', {})
            return {
                "min": value.get('minValue'),
                "max": value.get('maxValue'),
                "currency": base_salary.get('currency', 'BRL'),
                "period": base_salary.get('unitText', 'monthly')
            }
        return None
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract job title from HTML"""
        selectors = [
            'h1.job-title',
            'h1[class*="title"]',
            '.sc-job-title'
        ]
        
        for selector in selectors:
            title = self.extract_text(soup, selector)
            if title:
                return title
        
        return None
    
    def _extract_company(self, soup) -> Optional[str]:
        """Extract company name"""
        selectors = [
            '.company-name',
            'a[class*="company"]',
            '.sc-company-name'
        ]
        
        for selector in selectors:
            company = self.extract_text(soup, selector)
            if company:
                return company
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location"""
        selectors = [
            '.job-location',
            'span[class*="location"]',
            '.sc-job-location'
        ]
        
        for selector in selectors:
            location = self.extract_text(soup, selector)
            if location:
                return location
        
        return None
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract full job description"""
        selectors = [
            'div.job-description',
            'div[class*="description"]',
            '.sc-job-description'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
        
        return None


# Register Gupy scraper
ScraperRegistry.register("gupy.io", GupyScraper)
ScraperRegistry.register("vaga.gupy.io", GupyScraper)
