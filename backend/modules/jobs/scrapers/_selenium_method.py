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
            
            params['f_TPR'] = 'r2592000'  # Last 30 days
            if filters.get('modality') == 'remote':
                params['f_WT'] = '2'
            params['sortBy'] = 'DD'  # Sort by date
            
            search_url = base_url + '?' + urlencode(params)
            logger.info(f\"Selenium LinkedIn search: {search_url}\")
            
            # Load page
            driver.get(search_url)
            time.sleep(3)  # Wait for initial load
            
            # Scroll to load more jobs
            last_height = driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            max_scrolls = 20  # Safety limit
            
            while len(job_urls) < max_jobs and scrolls < max_scrolls:
                # Find all job links
                try:
                    job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/view/"]')
                    
                    for elem in job_elements:
                        try:
                            href = elem.get_attribute('href')
                            if href and '/jobs/view/' in href:
                                clean_url = href.split('?')[0]
                                if clean_url not in job_urls:
                                    job_urls.append(clean_url)
                                    
                                if len(job_urls) >= max_jobs:
                                    break
                        except:
                            continue
                    
                    if len(job_urls) >= max_jobs:
                        break
                    
                    # Scroll down
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for content to load
                    
                    # Check if reached bottom
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info("Reached bottom of page, no more jobs to load")
                        break
                    
                    last_height = new_height
                    scrolls += 1
                    
                    if scrolls % 5 == 0:
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
