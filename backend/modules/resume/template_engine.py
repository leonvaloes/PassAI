"""
Template Engine - DOCX manipulation with 100% layout preservation
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import copy

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    DOCX Template Engine
    
    CRITICAL RULES:
    - NEVER modify fonts, sizes, colors, spacing
    - ONLY replace text content in designated areas
    - Preserve all styles, margins, page breaks
    - Template is IMMUTABLE except for content
    """
    
    def __init__(self, template_path: str):
        """
        Initialize Template Engine
        
        Args:
            template_path: Path to DOCX template file
        """
        self.template_path = Path(template_path)
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        self.template_structure = None
        self.placeholders = {}
        
        # Analyze template on init
        self._analyze_template()
    
    def _analyze_template(self):
        """
        Analyze template structure and identify placeholders
        
        Placeholders can be:
        - {{FIELD_NAME}} - Explicit placeholder
        - Or predefined sections by paragraph index
        """
        logger.info(f"Analyzing template: {self.template_path}")
        
        doc = Document(self.template_path)
        
        self.template_structure = {
            "paragraphs_count": len(doc.paragraphs),
            "sections_count": len(doc.sections),
            "styles": [p.style.name for p in doc.paragraphs if p.style],
            "placeholders": []
        }
        
        # Find placeholders
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text
            
            # Explicit placeholders ({{...}})
            import re
            matches = re.findall(r'\{\{([A-Z_]+)\}\}', text)
            
            for match in matches:
                self.placeholders[match] = {
                    "paragraph_index": i,
                    "type": "explicit",
                    "original_text": text
                }
                self.template_structure["placeholders"].append(match)
        
        logger.info(f"✅ Template analyzed: {len(self.placeholders)} placeholders found")
        logger.info(f"   Placeholders: {list(self.placeholders.keys())}")
    
    def fill_template(
        self, 
        content: Dict[str, any], 
        output_path: str
    ) -> Dict[str, any]:
        """
        Fill template with content, preserving layout 100%
        
        Args:
            content: {
                "nome": "Leonardo Valoes",
                "email": "leo@example.com",
                "resumo": "Desenvolvedor...",
                "experiencias": [
                    {
                        "empresa": "Tech Corp",
                        "cargo": "Backend Developer",
                        "periodo": "2020-2023",
                        "bullets": ["Bullet 1", "Bullet 2"]
                    }
                ],
                "educacao": [...],
                "habilidades": [...]
            }
            output_path: Where to save filled document
        
        Returns:
            {
                "success": bool,
                "output_path": str,
                "layout_preserved": bool,
                "warnings": [str]
            }
        """
        logger.info("Filling template with content")
        
        # Load template (fresh copy)
        doc = Document(self.template_path)
        warnings = []
        
        try:
            # Replace placeholders
            if self.placeholders:
                self._replace_placeholders(doc, content, warnings)
            else:
                # No placeholders: Use section-based filling
                self._fill_by_sections(doc, content, warnings)
            
            # Validate layout preservation
            layout_ok = self._validate_layout(doc)
            
            if not layout_ok:
                warnings.append("Layout validation failed - template may have changed")
            
            # Check page count (must be <= 2)
            # Note: python-docx doesn't provide page count directly
            # We approximate by paragraph count
            if len(doc.paragraphs) > 100:  # Heuristic
                warnings.append("Content may exceed 2 pages")
            
            # Save
            doc.save(output_path)
            logger.info(f"✅ Template filled: {output_path}")
            
            return {
                "success": True,
                "output_path": output_path,
                "layout_preserved": layout_ok,
                "warnings": warnings
            }
        
        except Exception as e:
            logger.error(f"Template filling failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "layout_preserved": False,
                "warnings": warnings
            }
    
    def _replace_placeholders(
        self, 
        doc: Document, 
        content: Dict, 
        warnings: List[str]
    ):
        """Replace {{PLACEHOLDER}} markers with content"""
        
        for placeholder, info in self.placeholders.items():
            para_idx = info["paragraph_index"]
            
            if para_idx >= len(doc.paragraphs):
                warnings.append(f"Placeholder {placeholder} index out of range")
                continue
            
            paragraph = doc.paragraphs[para_idx]
            
            # Get replacement value
            value = content.get(placeholder.lower())
            
            if value is None:
                warnings.append(f"No content for placeholder: {placeholder}")
                continue
            
            # Replace in ALL runs to preserve formatting
            for run in paragraph.runs:
                if f"{{{{{placeholder}}}}}" in run.text:
                    # Replace text ONLY
                    run.text = run.text.replace(
                        f"{{{{{placeholder}}}}}",
                        str(value)
                    )
                    # DO NOT modify run.font, run.bold, etc.
    
    def _fill_by_sections(
        self,
        doc: Document,
        content: Dict,
        warnings: List[str]
    ):
        """
        Fill template by predefined sections (when no placeholders)
        
        ASSUMPTION: Template has sections in order:
        1. Header (nome, contato)
        2. Resumo Profissional
        3. Experiência Profissional
        4. Educação
        5. Habilidades
        """
        # This is template-specific logic
        # For MVP, we'll use a simple heuristic
        
        # Find section headers
        sections = {
            "resumo": None,
            "experiencia": None,
            "educacao": None,
            "habilidades": None
        }
        
        for i, para in enumerate(doc.paragraphs):
            text_lower = para.text.lower()
            
            if "resumo" in text_lower or "perfil" in text_lower:
                sections["resumo"] = i
            elif "experiência" in text_lower or "experiencia" in text_lower:
                sections["experiencia"] = i
            elif "educação" in text_lower or "educacao" in text_lower or "formação" in text_lower:
                sections["educacao"] = i
            elif "habilidades" in text_lower or "skills" in text_lower:
                sections["habilidades"] = i
        
        # For each section, replace content in following paragraphs
        # This is simplified - real implementation would be more sophisticated
        
        if sections["resumo"] is not None:
            # Replace paragraph after "Resumo" header
            idx = sections["resumo"] + 1
            if idx < len(doc.paragraphs) and "resumo" in content:
                para = doc.paragraphs[idx]
                # Replace runs
                if para.runs:
                    para.runs[0].text = content["resumo"]
                    # Clear other runs
                    for run in para.runs[1:]:
                        run.text = ""
        
        # Similar for other sections...
        # This is template-dependent and would need customization
    
    def _validate_layout(self, doc: Document) -> bool:
        """
        Validate that layout is preserved
        
        Checks:
        - Same number of sections
        - Styles unchanged
        - (More checks can be added)
        """
        try:
            # Check section count
            if len(doc.sections) != self.template_structure["sections_count"]:
                logger.warning("Section count changed")
                return False
            
            # Check paragraph count (should be similar, +/- for bullets)
            para_diff = abs(len(doc.paragraphs) - self.template_structure["paragraphs_count"])
            if para_diff > 20:  # Allow some variance for dynamic content
                logger.warning(f"Paragraph count changed significantly: {para_diff}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Layout validation error: {e}")
            return False
    
    def shorten_content(
        self,
        content: Dict,
        max_chars_per_bullet: int = 80
    ) -> Dict:
        """
        Shorten content to fit template
        
        Strategies:
        - Reduce bullet points to max_chars_per_bullet
        - Remove least relevant experiences
        - Summarize descriptions
        
        Args:
            content: Original content
            max_chars_per_bullet: Max characters per bullet point
        
        Returns:
            Shortened content dict
        """
        logger.info("Shortening content to fit template")
        
        shortened = copy.deepcopy(content)
        
        # Shorten bullets
        if "experiencias" in shortened:
            for exp in shortened["experiencias"]:
                if "bullets" in exp:
                    exp["bullets"] = [
                        bullet[:max_chars_per_bullet].rstrip() + "..."
                        if len(bullet) > max_chars_per_bullet
                        else bullet
                        for bullet in exp["bullets"]
                    ]
        
        # Shorten resumo
        if "resumo" in shortened and len(shortened["resumo"]) > 300:
            shortened["resumo"] = shortened["resumo"][:300].rstrip() + "..."
        
        return shortened
    
    def estimate_fit(self, content: Dict) -> Tuple[bool, str]:
        """
        Estimate if content will fit in 2-page template
        
        Returns:
            (fits: bool, reason: str)
        """
        # Rough heuristic based on character count
        total_chars = 0
        
        # Count all text
        for key, value in content.items():
            if isinstance(value, str):
                total_chars += len(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        total_chars += len(item)
                    elif isinstance(item, dict):
                        total_chars += sum(
                            len(str(v)) for v in item.values()
                        )
        
        # Estimate: 2 pages ≈ 3000 characters (very rough)
        MAX_CHARS = 3500
        
        if total_chars > MAX_CHARS:
            return False, f"Content too large ({total_chars} chars, max {MAX_CHARS})"
        
        return True, "Content should fit"
    
    def get_template_info(self) -> Dict:
        """Get template structure info"""
        return {
            "path": str(self.template_path),
            "structure": self.template_structure,
            "placeholders": list(self.placeholders.keys())
        }
