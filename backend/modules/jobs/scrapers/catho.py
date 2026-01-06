"""
Catho Job Scraper
Connector for Catho (catho.com.br)
"""
import logging
import re
from typing import Dict, Any, Optional
from modules.jobs.scraper import BaseScraper, ScraperRegistry

logger = logging.getLogger(__name__)


class CathoScraper(BaseScraper):
    """Scraper for Catho job postings"""
    
    def search(self, filters: Dict[str, Any], max_jobs: int = 50) -> list:
        """Search Catho for jobs"""
        
        job_urls = []
        
        try:
            # Simplified URL - Catho is tricky
            base_url = "https://www.catho.com.br/vagas/"
            
            # Build query parameter
            query_parts = []
            if filters.get('title'):
                query_parts.append(filters['title'])
            if filters.get('stack'):
                query_parts.extend(filters['stack'][:2])
            
            # Use query parameter instead of path
            if query_parts:
                from urllib.parse import quote
                query = ' '.join(query_parts)
                base_url += f"?q={quote(query)}"
            
            logger.info(f"Catho search: {base_url}")
            
            html = self.fetch_page(base_url)
            if html:
                soup = self.parse_html(html)
                job_links = soup.select('a[href*="/vagas/"], a[class*="job"]')
                
                for link in job_links[:max_jobs]:
                    href = link.get('href', '')
                    if href and href.startswith('/'):
                        href = 'https://www.catho.com.br' + href
                    if href and 'catho.com.br/vagas' in href and href not in job_urls:
                        job_urls.append(href)
            
            logger.info(f"✅ Found {len(job_urls)} Catho jobs")
            
        except Exception as e:
            logger.error(f"Catho search failed: {e}")
        
        return job_urls
    
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """Extract job data from Catho URL"""
        html = self.fetch_page(url)
        
        if not html:
            return {
                "url": url,
                "error": "Failed to fetch page"
            }
        
        soup = self.parse_html(html)
        
        # Extract data using CSS selectors
        data = {
            "url": url,
            "title": self._extract_title(soup),
            "company": self._extract_company(soup),
            "location": self._extract_location(soup),
            "description": self._extract_description(soup),
            "salary": self._extract_salary(soup),
            "rawHtml": html,
            "rawText": soup.get_text(separator=' ', strip=True)
        }
        
        # Clean all string values
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.clean_text(value)
        
        logger.info(f"✅ Extracted Catho job: {data.get('title', 'Unknown')}")
        
        return data
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract job title"""
        selectors = [
            'h1.job-title',
            'h1[itemprop="title"]',
            'h1.title',
            'h2.job-header-title'
        ]
        
        for selector in selectors:
            title = self.extract_text(soup, selector)
            if title:
                return title
        
        return None
    
    def _extract_company(self, soup) -> Optional[str]:
        """Extract company name"""
        selectors = [
            'span[itemprop="hiringOrganization"]',
            'a.company-name',
            'span.company',
            'div.company-name'
        ]
        
        for selector in selectors:
            company = self.extract_text(soup, selector)
            if company:
                return company
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location"""
        selectors = [
            'span[itemprop="jobLocation"]',
            'span.location',
            'div.job-location',
            'span.city'
        ]
        
        for selector in selectors:
            location = self.extract_text(soup, selector)
            if location:
                return self._parse_location(location)
        
        return None
    
    def _parse_location(self, location_str: str) -> Dict[str, str]:
        """Parse location string into components"""
        if not location_str:
            return {}
        
        location_str = location_str.strip()
        
        # Check for remote
        if any(word in location_str.lower() for word in ['remoto', 'home office', 'teletrabalho']):
            return {"remote": True}
        
        # Catho format: "São Paulo - SP"
        if '-' in location_str:
            parts = [p.strip() for p in location_str.split('-')]
            if len(parts) >= 2:
                return {
                    "city": parts[0],
                    "state": parts[1],
                    "country": "Brazil"
                }
        
        # Alternative: "São Paulo, SP"
        if ',' in location_str:
            parts = [p.strip() for p in location_str.split(',')]
            if len(parts) >= 2:
                return {
                    "city": parts[0],
                    "state": parts[1],
                    "country": "Brazil"
                }
        
        # Single value
        return {"city": location_str, "country": "Brazil"}
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract full job description"""
        selectors = [
            'div[itemprop="description"]',
            'div.job-description',
            'div.description',
            'div.job-detail-description'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
        
        return None
    
    def _extract_salary(self, soup) -> Optional[Dict[str, Any]]:
        """Extract salary if available"""
        selectors = [
            'span.salary',
            'div.salary-range',
            'span[itemprop="baseSalary"]',
            'div.job-salary'
        ]
        
        for selector in selectors:
            salary_text = self.extract_text(soup, selector)
            if salary_text:
                return self._parse_salary(salary_text)
        
        return None
    
    def _parse_salary(self, salary_text: str) -> Optional[Dict[str, Any]]:
        """Parse salary text into structured data"""
        if not salary_text:
            return None
        
        # Skip "A combinar" or similar
        if any(word in salary_text.lower() for word in ['combinar', 'negociar', 'confidencial']):
            return None
        
        currency = "BRL"
        
        # Extract numbers
        numbers = re.findall(r'[\d\.,]+', salary_text)
        
        if len(numbers) >= 2:
            # Range found
            min_val = float(numbers[0].replace('.', '').replace(',', '.'))
            max_val = float(numbers[1].replace('.', '').replace(',', '.'))
            
            # Determine period
            period = "monthly"
            if any(word in salary_text.lower() for word in ['ano', 'anual']):
                period = "yearly"
            
            return {
                "min": min_val,
                "max": max_val,
                "currency": currency,
                "period": period
            }
        elif len(numbers) == 1:
            # Single value (usually means "up to")
            value = float(numbers[0].replace('.', '').replace(',', '.'))
            
            # Check if it's "up to" or exact
            is_max = any(word in salary_text.lower() for word in ['até', 'up to', 'máximo'])
            
            if is_max:
                return {
                    "min": 0,
                    "max": value,
                    "currency": currency,
                    "period": "monthly"
                }
            else:
                return {
                    "min": value,
                    "max": value,
                    "currency": currency,
                    "period": "monthly"
                }
        
        return None


# Register Catho scraper
ScraperRegistry.register("catho.com.br", CathoScraper)
ScraperRegistry.register("www.catho.com.br", CathoScraper)
