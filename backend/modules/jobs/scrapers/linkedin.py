"""
LinkedIn Job Scraper
Connector for LinkedIn job postings
"""
import logging
import re
import time
import os
import pickle
from typing import Dict, Any, Optional, List
from modules.jobs.scraper import BaseScraper, ScraperRegistry

logger = logging.getLogger(__name__)

# Check if Selenium is available
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
    logger.info("✅ Selenium available for LinkedIn scraping")
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("⚠️ Selenium IMPORTS failed, will use HTTP-only scraping")


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job postings"""
    
    def search(self, filters: Dict[str, Any], max_jobs: int = 100) -> List[str]:
        """Search LinkedIn for jobs - Uses Selenium for max_jobs >= 5, HTTP otherwise"""
        # Use Selenium for larger searches if available
        # Lowered threshold to 5 because search engine splits maxJobsPerRun across sources
        # e.g. 50 jobs / 5 sources = 10 jobs per source. We want Selenium for this.
        if SELENIUM_AVAILABLE:  # FORCE SELENIUM FOR DEBUGGING
            try:
                logger.info(f"Using Selenium to fetch {max_jobs} LinkedIn jobs")
                return self._search_with_selenium(filters, max_jobs)
            except Exception as e:
                logger.error(f"Selenium scraping failed: {e}, falling back to HTTP")
                # Fallback to HTTP with reduced limit
                return self._search_with_http(filters, min(max_jobs, 10))
        else:
            if max_jobs >= 5:
                logger.warning(f"Requested {max_jobs} jobs but Selenium not available, limiting to 10")
            return self._search_with_http(filters, min(max_jobs, 10))
    
    def _search_with_http(self, filters: Dict[str, Any], max_jobs: int = 10) -> List[str]:
        """Search LinkedIn for jobs matching filters - Returns list of job URLs"""
        from urllib.parse import urlencode
        
        job_urls = []
        
        try:
            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search/"
            params = {}
            
            if filters.get('title'):
                params['keywords'] = filters['title']
            
            # Location - CRITICAL: Always filter by country to avoid international jobs
            location = filters.get('location')
            if location:
                # If Brazil, ALWAYS add to filter (even if remote)
                # Use ENGLISH "Brazil" for better LinkedIn compatibility
                if location.get('country') in ['Brazil', 'Brasil']:
                    params['location'] = 'Brazil'
                elif not location.get('remote'):
                    # Build from city/state
                    loc_parts = []
                    if location.get('city'):
                        loc_parts.append(location['city'])
                    if location.get('state'):
                        loc_parts.append(location['state'])
                    if loc_parts:
                        params['location'] = ', '.join(loc_parts)
            
            params['f_TPR'] = 'r1209600'  # Last 14 days
            
            if filters.get('modality') == 'remote':
                params['f_WT'] = '2'
            
            params['sortBy'] = 'DD'  # Sort by date
            
            # Fetch multiple pages to get up to 100 jobs
            page = 0
            max_pages = 10  # LinkedIn shows ~25 jobs per page, so 4 pages ≈ 100 jobs
            
            while len(job_urls) < max_jobs and page < max_pages:
                # Add pagination
                params['start'] = page * 25
                
                search_url = base_url + '?' + urlencode(params)
                if page == 0:
                    logger.info(f"LinkedIn search: {search_url}")
                else:
                    logger.info(f"LinkedIn page {page + 1}: start={params['start']}")
                
                # Fetch search results
                html = self.fetch_page(search_url)
                if not html:
                    break
                
                # Extract job URLs - prioritize main search results
                soup = self.parse_html(html)
                
                # Try to find jobs in the main results list first (most accurate)
                job_links = soup.select('ul.jobs-search__results-list a[href*="/jobs/view/"]')
                if not job_links:
                    job_links = soup.select('div.jobs-search-results-list a[href*="/jobs/view/"]')
                
                # Fallback to any job link (includes recommendations)
                if not job_links:
                    job_links = soup.select('a[href*="/jobs/view/"]')
                if not job_links:
                    job_links = soup.select('a.base-card__full-link')
                if not job_links:
                    job_links = soup.select('a[class*="job-card-container__link"]')
                
                if page == 0:
                    logger.info(f"LinkedIn: Found {len(job_links)} job links in HTML")
                
                # Extract URLs
                page_urls_count = 0
                for link in job_links:
                    if len(job_urls) >= max_jobs:
                        break
                        
                    href = link.get('href', '')
                    if '/jobs/view/' in href:
                        clean_url = href.split('?')[0]
                        if clean_url.startswith('/'):
                            clean_url = 'https://www.linkedin.com' + clean_url
                        if clean_url not in job_urls:
                            job_urls.append(clean_url)
                            page_urls_count += 1
                
                logger.info(f"Page {page + 1}: Added {page_urls_count} new jobs (total: {len(job_urls)})")
                
                # Stop if no new jobs found
                if page_urls_count == 0:
                    logger.info("No new jobs found, stopping pagination")
                    break
                
                page += 1
            
            logger.info(f"✅ Found {len(job_urls)} LinkedIn jobs across {page} pages")
            
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
        
        return job_urls
    
    def _search_with_selenium(self, filters: Dict[str, Any], max_jobs: int = 100) -> List[str]:
        """Use Selenium to scrape LinkedIn with scrolling for 100+ jobs"""
        from urllib.parse import urlencode
        
        job_urls = []
        driver = None
        
        try:
            # Setup Chrome options
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Run without UI
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            
            # --- AUTHENTICATION FLOW ---
            driver.get('https://www.linkedin.com')
            
            # Try to load cookies
            cookies_loaded = False
            if os.path.exists('linkedin_cookies.pkl'):
                try:
                    with open('linkedin_cookies.pkl', 'rb') as f:
                        cookies = pickle.load(f)
                        for cookie in cookies:
                            driver.add_cookie(cookie)
                    cookies_loaded = True
                    logger.info("✅ Loaded LinkedIn cookies")
                    driver.refresh() # Refresh to apply cookies
                except Exception as e:
                    logger.warning(f"Failed to load cookies: {e}")
            
            # Check if login needed
            if not cookies_loaded:
                # Load credentials (Priority: Filter Auth > .env)
                from dotenv import load_dotenv
                load_dotenv()
                
                auth_config = filters.get('auth_config', {})
                email = auth_config.get('linkedinEmail') or os.getenv('LINKEDIN_EMAIL')
                password = auth_config.get('linkedinPassword') or os.getenv('LINKEDIN_PASSWORD')
                
                if email and password:
                    logger.info("Logging into LinkedIn...")
                    try:
                        driver.get('https://www.linkedin.com/login')
                        time.sleep(2)
                        
                        email_field = driver.find_element(By.ID, 'username')
                        email_field.send_keys(email)
                        
                        password_field = driver.find_element(By.ID, 'password')
                        password_field.send_keys(password)
                        
                        login_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                        login_btn.click()
                        
                        time.sleep(5) # Wait for login
                        
                        # Save cookies
                        with open('linkedin_cookies.pkl', 'wb') as f:
                            pickle.dump(driver.get_cookies(), f)
                        logger.info("✅ Login successful, cookies saved")
                        
                    except Exception as e:
                        logger.error(f"Login failed: {e}")
                else:
                    logger.warning("No credentials found in .env, continuing without login")
            # ---------------------------
                        
            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search/"
            params = {}
            
            if filters.get('title'):
                params['keywords'] = filters['title']
            
            location = filters.get('location')
            if location:
                if location.get('country') in ['Brazil', 'Brasil']:
                    params['location'] = 'Brazil'
                elif not location.get('remote'):
                    loc_parts = []
                    if location.get('city'):
                        loc_parts.append(location['city'])
                    if location.get('state'):
                        loc_parts.append(location['state'])
                    if loc_parts:
                        params['location'] = ', '.join(loc_parts)
            
            params['f_TPR'] = 'r1209600'  # Last 14 days
            if filters.get('modality') == 'remote':
                params['f_WT'] = '2'
            params['sortBy'] = 'DD'  # Sort by date
            
            search_url = base_url + '?' + urlencode(params)
            logger.info(f"Selenium LinkedIn search: {search_url}")
            
            # Load page
            driver.get(search_url)
            time.sleep(3)  # Wait for initial load
            
            # Verify Login Status
            is_logged_in = False
            try:
                # Check for common logged-in elements (Nav bar, Me icon)
                if driver.find_elements(By.ID, 'global-nav') or driver.find_elements(By.CSS_SELECTOR, '.global-nav__me-photo'):
                    is_logged_in = True
                    logger.info("✅ Verified: Browsing as Logged-In User")
                else:
                    logger.warning(f"⚠️ Detected GUEST view on search page: {driver.current_url}")
                    
                    # If we expected to be logged in (cookies loaded), retry login clearly
                    # Ensure we have credentials
                    if 'email' not in locals():
                        from dotenv import load_dotenv
                        load_dotenv()
                        auth_config = filters.get('auth_config', {})
                        email = auth_config.get('linkedinEmail') or os.getenv('LINKEDIN_EMAIL')
                        password = auth_config.get('linkedinPassword') or os.getenv('LINKEDIN_PASSWORD')

                    if cookies_loaded or (email and password):
                        logger.info(f"🔄 Retrying full login flow (Credentials available: {bool(email)})...")
                        
                        # Go to login page
                        driver.get('https://www.linkedin.com/login')
                        time.sleep(2)
                        
                        # Check if already logged in (redirected)
                        if 'feed' in driver.current_url or 'search' in driver.current_url:
                            is_logged_in = True
                        else:
                            # Perform login
                            try:
                                email_field = driver.find_element(By.ID, 'username')
                                email_field.clear()
                                email_field.send_keys(email)
                                
                                password_field = driver.find_element(By.ID, 'password')
                                password_field.send_keys(password)
                                
                                login_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                                login_btn.click()
                                
                                time.sleep(5)
                                
                                # Check success
                                if 'feed' in driver.current_url or 'search' in driver.current_url or driver.find_elements(By.ID, 'global-nav'):
                                    is_logged_in = True
                                    logger.info("✅ Retry Login Successful")
                                    # Update cookies
                                    with open('linkedin_cookies.pkl', 'wb') as f:
                                        pickle.dump(driver.get_cookies(), f)
                                    
                                    # Reload search
                                    driver.get(search_url)
                                    time.sleep(3)
                                else:
                                    logger.error("❌ Retry Login Failed")
                            except Exception as e:
                                logger.error(f"Retry login error: {e}")
                                
            except Exception as e:
                logger.warning(f"Login check error: {e}")
            
            # Scroll to load more jobs
            last_height = driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = 20  # Safety limit
            no_change_count = 0
            
            while len(job_urls) < max_jobs and scrolls < max_scrolls:
                # Find all job links
                try:
                    # Look for various job card selectors
                    selectors = [
                        'a[href*="/jobs/view/"]',
                        'a.job-card-list__title',
                        'a.job-card-container__link',
                        'div[data-job-id] a'
                    ]
                    
                    found_new = False
                    for selector in selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            try:
                                href = elem.get_attribute('href')
                                if href and '/jobs/view/' in href:
                                    clean_url = href.split('?')[0]
                                    if clean_url not in job_urls:
                                        job_urls.append(clean_url)
                                        found_new = True
                            except:
                                continue
                                
                    if len(job_urls) >= max_jobs:
                        break
                    
                    # Scroll down
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for content to load
                    
                    # Try clicking "See more jobs" button if it exists
                    try:
                        see_more = driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="See more jobs"], button.infinite-scroller__show-more-button')
                        if see_more and see_more[0].is_displayed():
                            driver.execute_script("arguments[0].click();", see_more[0])
                            time.sleep(2)
                    except:
                        pass

                    # Check if reached bottom
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        no_change_count += 1
                        # Retry a few times before giving up (content might be loading)
                        if no_change_count >= 3:
                            logger.info("Reached bottom of page (height unchanged 3x), no more jobs to load")
                            break
                        time.sleep(2)
                    else:
                        no_change_count = 0
                        last_height = new_height
                        
                    scrolls += 1
                    
                    if scrolls % 2 == 0:
                        logger.info(f"Selenium scroll {scrolls}: Found {len(job_urls)} jobs so far")
                
                except Exception as e:
                    logger.warning(f"Error during scroll {scrolls}: {e}")
                    break
            
            logger.info(f"✅ Selenium found {len(job_urls)} LinkedIn jobs after {scrolls} scrolls")
            
        except Exception as e:
            logger.error(f"Selenium LinkedIn scraping failed: {e}")
            raise
        
        finally:
            if driver:
                driver.quit()
        
        return job_urls[:max_jobs]
    
    def extract_job_data(self, url: str) -> Dict[str, Any]:
        """Extract job data from LinkedIn URL"""
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
        
        logger.info(f"✅ Extracted LinkedIn job: {data.get('title', 'Unknown')}")
        
        return data
    
    def _extract_title(self, soup) -> Optional[str]:
        """Extract job title"""
        # Try multiple selectors (LinkedIn changes frequently)
        selectors = [
            'h1.top-card-layout__title',
            'h1.topcard__title',
            'h2.top-card-layout__title',
            '.job-details-jobs-unified-top-card__job-title'
        ]
        
        for selector in selectors:
            title = self.extract_text(soup, selector)
            if title:
                return title
        
        return None
    
    def _extract_company(self, soup) -> Optional[str]:
        """Extract company name"""
        selectors = [
            'a.topcard__org-name-link',
            'span.topcard__flavor',
            '.job-details-jobs-unified-top-card__company-name',
            'a.sub-nav-cta__optional-url'
        ]
        
        for selector in selectors:
            company = self.extract_text(soup, selector)
            if company:
                # Remove "· " prefix if present
                company = company.replace('·', '').strip()
                return company
        
        return None
    
    def _extract_location(self, soup) -> Optional[str]:
        """Extract location"""
        selectors = [
            'span.topcard__flavor--bullet',
            'span.top-card-layout__location',
            '.job-details-jobs-unified-top-card__workplace-type'
        ]
        
        for selector in selectors:
            location = self.extract_text(soup, selector)
            if location:
                # Parse into city, state
                return self._parse_location(location)
        
        return None
    
    def _parse_location(self, location_str: str) -> Dict[str, str]:
        """Parse location string into components"""
        # Examples: "São Paulo, SP", "Remote", "Brasília, DF, Brazil"
        
        if not location_str:
            return {}
        
        location_str = location_str.strip()
        
        # Check for remote
        if 'remote' in location_str.lower():
            return {"remote": True}
        
        # Split by comma
        parts = [p.strip() for p in location_str.split(',')]
        
        if len(parts) >= 2:
            return {
                "city": parts[0],
                "state": parts[1],
                "country": parts[2] if len(parts) > 2 else "Brazil"
            }
        elif len(parts) == 1:
            return {"city": parts[0]}
        
        return {}
    
    def _extract_description(self, soup) -> Optional[str]:
        """Extract full job description"""
        selectors = [
            'div.show-more-less-html__markup',
            'div.description__text',
            '.job-details-jobs-unified-top-card__job-description'
        ]
        
        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Get full text including nested elements
                return desc_elem.get_text(separator='\n', strip=True)
        
        return None
    
    def _extract_salary(self, soup) -> Optional[Dict[str, Any]]:
        """Extract salary if available"""
        # LinkedIn rarely shows salary on public pages
        # Try to find salary indicators
        
        selectors = [
            'span.salary',
            '.compensation__salary'
        ]
        
        for selector in selectors:
            salary_text = self.extract_text(soup, selector)
            if salary_text:
                return self._parse_salary(salary_text)
        
        return None
    
    def _parse_salary(self, salary_text: str) -> Optional[Dict[str, Any]]:
        """Parse salary text into structured data"""
        # Examples:
        # "R$ 5.000 - R$ 8.000/mês"
        # "$50,000 - $80,000/year"
        
        if not salary_text:
            return None
        
        # Extract currency
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
            if "year" in salary_text.lower() or "ano" in salary_text.lower():
                period = "yearly"
            
            return {
                "min": min_val,
                "max": max_val,
                "currency": currency,
                "period": period
            }
        
        return None


# Register LinkedIn scraper
ScraperRegistry.register("linkedin.com", LinkedInScraper)
ScraperRegistry.register("www.linkedin.com", LinkedInScraper)
