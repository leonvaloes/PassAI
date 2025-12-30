"""
Job Extractor - Extract structured job data from multiple sources
"""
import logging
import re
from typing import Dict, Optional, List
from urllib.parse import urlparse
from pathlib import Path

from database.models import Job, JobSource, ATSType

logger = logging.getLogger(__name__)


class JobExtractor:
    """Extract job posting data from various sources"""
    
    def __init__(self, vision_processor=None, llm_router=None):
        """
        Initialize JobExtractor
        
        Args:
            vision_processor: VisionProcessor instance for screenshot analysis
            llm_router: LLMRouter instance for structured parsing
        """
        self.vision_processor = vision_processor
        self.llm_router = llm_router
        
        # Domain patterns for ATS detection
        self.domain_ats_map = {
            "gupy.io": ATSType.GUPY,
            "vemprogupy.com": ATSType.GUPY,
            "greenhouse.io": ATSType.GREENHOUSE,
            "lever.co": ATSType.LEVER,
            "myworkdayjobs.com": ATSType.WORKDAY,
            "https://taleo.net": ATSType.TALEO
        }
    
    def extract(self, input_data: Dict) -> Job:
        """
        Extract job data from input
        
        Args:
            input_data: {
                "type": "url|text|pdf|screenshot",
                "content": str | bytes | Path
            }
        
        Returns:
            Job model instance
        
        Raises:
            ValueError: If extraction fails
        """
        input_type = input_data.get("type")
        content = input_data.get("content")
        
        logger.info(f"Extracting job from {input_type}")
        
        try:
            if input_type == "url":
                return self._extract_from_url(content)
            elif input_type == "text":
                return self._extract_from_text(content)
            elif input_type == "pdf":
                return self._extract_from_pdf(content)
            elif input_type == "screenshot":
                return self._extract_from_screenshot(content)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
        
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            raise
    
    def _extract_from_url(self, url: str) -> Job:
        """Extract from job posting URL"""
        logger.info(f"Extracting from URL: {url}")
        
        # Detect domain
        domain = urlparse(url).netloc
        
        # Try scrapers
        if "linkedin.com" in domain:
            raw_html = self._scrape_linkedin(url)
        elif "gupy.io" in domain or "vemprogupy.com" in domain:
            raw_html = self._scrape_gupy(url)
        else:
            # Generic scraper
            raw_html = self._scrape_generic(url)
        
        # Parse with LLM
        job_data = self._parse_with_llm(raw_html)
        
        # Detect ATS
        ats_type = self._detect_ats_from_url(url, raw_html)
        
        return Job(
            source=JobSource.URL,
            url=url,
            raw_content=raw_html[:5000],  # Limit size
            ats_detectado=ats_type,
            **job_data
        )
    
    def _extract_from_text(self, text: str) -> Job:
        """Extract from pasted text"""
        logger.info("Extracting from text")
        
        # Parse with LLM
        job_data = self._parse_with_llm(text)
        
        # Try to detect ATS from text patterns
        ats_type = self._detect_ats_from_text(text)
        
        return Job(
            source=JobSource.TEXT,
            raw_content=text[:5000],
            ats_detectado=ats_type,
            **job_data
        )
    
    def _extract_from_pdf(self, pdf_path: str) -> Job:
        """Extract from PDF file"""
        import pypdf
        
        logger.info(f"Extracting from PDF: {pdf_path}")
        
        # Extract text from PDF
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        
        # Parse with LLM
        job_data = self._parse_with_llm(text)
        
        return Job(
            source=JobSource.PDF,
            raw_content=text[:5000],
            ats_detectado=ATSType.UNKNOWN,
            **job_data
        )
    
    def _extract_from_screenshot(self, image_path: str) -> Job:
        """Extract from screenshot using Vision AI"""
        logger.info(f"Extracting from screenshot: {image_path}")
        
        if not self.vision_processor:
            raise ValueError("VisionProcessor required for screenshot extraction")
        
        # Use Vision AI to extract text
        prompt = """
        Extract all text from this job posting screenshot.
        Include: job title, company name, location, requirements, 
        salary, benefits, and any other visible details.
        """
        
        vision_result = self.vision_processor.query_image(image_path, prompt)
        
        if not vision_result.get("success"):
            raise ValueError(f"Vision extraction failed: {vision_result.get('error')}")
        
        extracted_text = vision_result["answer"]
        
        # Parse with LLM
        job_data = self._parse_with_llm(extracted_text)
        
        # Try to detect ATS from visible text
        ats_type = self._detect_ats_from_text(extracted_text)
        
        return Job(
            source=JobSource.SCREENSHOT,
            raw_content=extracted_text[:5000],
            ats_detectado=ats_type,
            **job_data
        )
    
    def _parse_with_llm(self, text: str) -> Dict:
        """
        Parse job posting text into structured data using LLM
        
        Returns:
            Dict with job fields (cargo, empresa, requisitos, etc)
        """
        logger.info("Parsing job data with LLM")
        
        prompt = f"""
Extraia as seguintes informações da vaga de emprego abaixo.
Retorne APENAS um objeto JSON válido, sem texto adicional.

Formato esperado:
{{
  "cargo": "título da vaga",
  "empresa": "nome da empresa",
  "local": "cidade/estado ou 'Remoto'",
  "modalidade": "remoto|hibrido|presencial",
  "senioridade": "junior|pleno|senior|especialista",
  "salario": "faixa salarial ou null",
  "beneficios": ["benefício 1", "benefício 2"],
  "requisitos_tecnicos": ["Python", "Django", "AWS"],
  "requisitos_comportamentais": ["liderança", "comunicação"]
}}

Regras:
- Se um campo não estiver claro, use null ou lista vazia
- requisitos_tecnicos: apenas tecnologias/ferramentas
- requisitos_comportamentais: soft skills

Vaga:
{text[:3000]}

JSON:
"""
        
        # Generate with LLM
        if not self.llm_router:
            # Fallback: manual parsing (basic)
            return self._fallback_parse(text)
        
        response = self.llm_router.llm.generate(
            prompt,
            temperature=0.1,  # Low temp for structured output
            max_tokens=500
        )
        
        # Extract JSON from response
        import json
        import re
        
        # Find JSON in response (might have extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                job_data = json.loads(json_match.group())
                logger.info("✅ LLM parsing successful")
                return job_data
            except json.JSONDecodeError:
                logger.warning("JSON parse failed, using fallback")
                return self._fallback_parse(text)
        
        return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict:
        """Fallback parser using regex patterns"""
        logger.info("Using fallback parsing")
        
        # Basic extraction
        cargo = self._extract_field(text, ["cargo", "vaga", "posição"])
        empresa = self._extract_field(text, ["empresa", "company"])
        local = self._extract_field(text, ["local", "localização", "location"])
        
        return {
            "cargo": cargo or "Vaga não especificada",
            "empresa": empresa or "Empresa não especificada",
            "local": local,
            "modalidade": None,
            "senioridade": None,
            "salario": None,
            "beneficios": [],
            "requisitos_tecnicos": [],
            "requisitos_comportamentais": []
        }
    
    def _extract_field(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract field using keywords"""
        for kw in keywords:
            pattern = rf"{kw}[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _detect_ats_from_url(self, url: str, html: str = "") -> ATSType:
        """Detect ATS system from URL and HTML"""
        domain = urlparse(url).netloc
        
        # Check domain map
        for pattern, ats_type in self.domain_ats_map.items():
            if pattern in domain:
                logger.info(f"✅ ATS detected from domain: {ats_type.value}")
                return ats_type
        
        # Check HTML patterns
        return self._detect_ats_from_text(html)
    
    def _detect_ats_from_text(self, text: str) -> ATSType:
        """Detect ATS from text patterns"""
        text_lower = text.lower()
        
        if "powered by greenhouse" in text_lower or "greenhouse software" in text_lower:
            return ATSType.GREENHOUSE
        elif "aplicar na gupy" in text_lower or "vemprogupy" in text_lower:
            return ATSType.GUPY
        elif "powered by lever" in text_lower:
            return ATSType.LEVER
        elif "workday" in text_lower and "apply" in text_lower:
            return ATSType.WORKDAY
        elif "taleo" in text_lower:
            return ATSType.TALEO
        
        return ATSType.UNKNOWN
    
    def _scrape_linkedin(self, url: str) -> str:
        """Scrape LinkedIn job posting"""
        # TODO: Implement LinkedIn scraping
        # For now, return placeholder
        logger.warning("LinkedIn scraper not implemented, using generic")
        return self._scrape_generic(url)
    
    def _scrape_gupy(self, url: str) -> str:
        """Scrape Gupy job posting"""
        import requests
        from bs4 import BeautifulSoup
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content (Gupy-specific selectors)
            content = soup.find('div', class_='sc-') or soup.find('main')
            
            if content:
                return content.get_text(separator='\n', strip=True)
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gupy scraping failed: {e}")
            return self._scrape_generic(url)
    
    def _scrape_generic(self, url: str) -> str:
        """Generic web scraper"""
        import requests
        from bs4 import BeautifulSoup
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        
        except Exception as e:
            logger.error(f"Generic scraping failed: {e}")
            raise ValueError(f"Failed to scrape URL: {e}")
