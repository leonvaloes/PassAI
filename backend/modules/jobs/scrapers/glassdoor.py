"""
Glassdoor Job Scraper
Connector for Glassdoor (glassdoor.com.br)
"""
import logging
import re
from typing import Dict, Any, Optional
from modules.jobs.scraper import BaseScraper, ScraperRegistry

logger = logging.getLogger(__name__)


class GlassdoorScraper(BaseScraper):
    """Scraper for Glassdoor job postings"""
    
    def search(self, filters: Dict[str, Any], max_jobs: int = 50) -> list:
        """Search Glassdoor for jobs"""
        from urllib.parse import urlencode
        
        job_urls = []
        
        try:
            base_url = "https://www.glassdoor.com.br/Vaga/brasil-vagas-SRCH_IL.0,6_IN36.htm"
            params = {}
            
            if filters.get('title'):
                params['sc.keyword'] = filters['title']
            
            search_url = base_url + ('&' if '?' in base_url else '?') + urlencode(params)
            logger.info(f"Glassdoor search: {search_url}")
            
            html = self.fetch_page(search_url)
            if html:
                soup = self.parse_html(html)
                job_links = soup.select('a[href*="/job-listing/"], a[class*="jobLink"]')
                
                for link in job_links[:max_jobs]:
                    href = link.get('href', '')
                    if href and href.startswith('/'):
                        href = 'https://www.glassdoor.com.br' + href
                    if href and 'glassdoor' in href and href not in job_urls:
                        job_urls.append(href)
            
            logger.info(f"✅ Found {len(job_urls)} Glassdoor jobs")
            
        except Exception as e:
            logger.error(f"Glassdoor search failed: {e}")
        
        return job_urls
    
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """Extract job data from Glassdoor URL"""
        html = self.fetch_page(url)
        
        if not html:
            return {
                "url": url,
                "error": "Failed to fetch page"
            }
        
        soup = self.parse_html(html)
        
        # Try JSON-LD first (Glassdoor often uses it)
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
                "salary": self._extract_salary(soup),
                "rawHtml": html,
                "rawText": soup.get_text(separator=' ', strip=True)
            }
        
        # Clean all string values
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.clean_text(value)
        
        logger.info(f"✅ Extracted Glassdoor job: {data.get('title', 'Unknown')}")
        
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
            'h1[data-test="job-title"]',
            'h2.jobTitle',
            'div.JobInfoHeader-title'
        ]
        
        for selector in selectors:
            title = self.extract_text(soup, selector)
            if title:
                return title
        
        return None
    
    def _extract_company(self, soup) -> Optional[str]:
        """Extract company name"""
        selectors = [
            'div[data-test="employer-name"]',
            'span.employerName',
            'a.EmployerProfile_employerName'
        ]
        
        for selector in selectors:
            company = self.extract_text(soup, selector)
            if company:
                return company
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location"""
        selectors = [
            'div[data-test="location"]',
            'span.location',
            'div.JobInfoHeader-location'
        ]
        
        for selector in selectors:
            location = self.extract_text(soup, selector)
            if location:
                return location
        
        return None
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract full job description"""
        selectors = [
            'div[data-test="jobDescriptionContent"]',
            'div.jobDescriptionContent',
            'div.desc'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
        
        return None
    
    def _extract_salary(self, soup) -> Optional[Dict[str, Any]]:
        """Extract salary if available"""
        selectors = [
            'span[data-test="detailSalary"]',
            'div.SalaryEstimate',
            'span.salary'
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
        
        return None


# Register Glassdoor scraper
ScraperRegistry.register("glassdoor.com", GlassdoorScraper)
ScraperRegistry.register("glassdoor.com.br", GlassdoorScraper)
ScraperRegistry.register("www.glassdoor.com", GlassdoorScraper)
ScraperRegistry.register("www.glassdoor.com.br", GlassdoorScraper)
