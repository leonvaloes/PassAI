"""
Indeed Job Scraper
Connector for Indeed Brazil (br.indeed.com)
"""
import logging
import re
from typing import Dict, Any, Optional
from modules.jobs.scraper import BaseScraper, ScraperRegistry

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job postings"""
    
    def search(self, filters: Dict[str, Any], max_jobs: int = 50) -> list:
        """Search Indeed BR for jobs matching filters"""
        from urllib.parse import urlencode
        
        job_urls = []
        
        try:
            base_url = "https://br.indeed.com/jobs"
            params = {}
            
            # Build query
            query_parts = []
            if filters.get('title'):
                query_parts.append(filters['title'])
            if filters.get('stack'):
                query_parts.extend(filters['stack'][:3])  # Top 3 techs
            
            if query_parts:
                params['q'] = ' '.join(query_parts)
            
            # Location
            location = filters.get('location')
            if location and not location.get('remote'):
                loc_parts = []
                if location.get('city'):
                    loc_parts.append(location['city'])
                if location.get('state'):
                    loc_parts.append(location['state'])
                if loc_parts:
                    params['l'] = ', '.join(loc_parts)
            
            if filters.get('modality') == 'remote':
                params['remotejob'] = '032b3046-06a3-4876-8dfd-474eb5e7ed11'
            
            params['sort'] = 'date'
            
            search_url = base_url + '?' + urlencode(params)
            logger.info(f"Indeed search: {search_url}")
            
            html = self.fetch_page(search_url)
            if not html:
                return []
            
            soup = self.parse_html(html)
            job_links = soup.select('a[href*="/rc/clk?jk="], a[class*="jcs-JobTitle"]')
            
            for link in job_links[:max_jobs]:
                href = link.get('href', '')
                if href:
                    if href.startswith('/'):
                        href = 'https://br.indeed.com' + href
                    if 'indeed.com' in href and href not in job_urls:
                        job_urls.append(href)
            
            logger.info(f"✅ Found {len(job_urls)} Indeed jobs")
            
        except Exception as e:
            logger.error(f"Indeed search failed: {e}")
        
        return job_urls
    
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """Extract job data from Indeed URL"""
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
        
        # Clean extracted data
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.clean_text(value)
        
        logger.info(f"✅ Extracted Indeed job: {data.get('title', 'Unknown')}")
        
        return data
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract job title"""
        selectors = [
            'h1.jobsearch-JobInfoHeader-title',
            'h1[class*="jobTitle"]',
            'h2.icl-u-xs-mb--xs'
        ]
        
        for selector in selectors:
            title = self.extract_text(soup, selector)
            if title:
                return title
        
        return None
    
    def _extract_company(self, soup) -> Optional[str]:
        """Extract company name"""
        selectors = [
            'div[data-company-name="true"]',
            'a[data-tn-element="companyName"]',
            'span.companyName'
        ]
        
        for selector in selectors:
            company = self.extract_text(soup, selector)
            if company:
                return company
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location"""
        selectors = [
            'div[data-testid="job-location"]',
            'div.companyLocation',
            'span.location'
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
        if any(word in location_str.lower() for word in ['remoto', 'remote', 'home office']):
            return {"remote": True}
        
        # Indeed format: "São Paulo, SP"
        parts = [p.strip() for p in location_str.split(',')]
        
        if len(parts) >= 2:
            return {
                "city": parts[0],
                "state": parts[1],
                "country": "Brazil"
            }
        elif len(parts) == 1:
            return {"city": parts[0], "country": "Brazil"}
        
        return {}
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract full job description"""
        selectors = [
            'div#jobDescriptionText',
            'div.jobsearch-jobDescriptionText',
            'div[class*="description"]'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
        
        return None
    
    def _extract_salary(self, soup) -> Optional[Dict[str, Any]]:
        """Extract salary if available"""
        selectors = [
            'div#salaryInfoAndJobType',
            'span.salary',
            'div[class*="salary"]'
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
        
        # Determine currency
        currency = "BRL"
        if "$" in salary_text and "R$" not in salary_text:
            currency = "USD"
        
        # Extract numbers
        numbers = re.findall(r'[\d\.,]+', salary_text)
        
        if len(numbers) >= 2:
            # Range found
            min_val = float(numbers[0].replace('.', '').replace(',', '.'))
            max_val = float(numbers[1].replace('.', '').replace(',', '.'))
            
            # Determine period
            period = "monthly"
            if any(word in salary_text.lower() for word in ['ano', 'year', 'anual']):
                period = "yearly"
            
            return {
                "min": min_val,
                "max": max_val,
                "currency": currency,
                "period": period
            }
        elif len(numbers) == 1:
            # Single value
            value = float(numbers[0].replace('.', '').replace(',', '.'))
            return {
                "min": value,
                "max": value,
                "currency": currency,
                "period": "monthly"
            }
        
        return None


# Register Indeed scraper
ScraperRegistry.register("indeed.com", IndeedScraper)
ScraperRegistry.register("br.indeed.com", IndeedScraper)
ScraperRegistry.register("www.indeed.com", IndeedScraper)
