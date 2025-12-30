"""
LLM Adapter for Resume Generator

Adapts LLMRouter to work with Resume Generator's expected interface
"""
import logging
from core.llm.router import LLMRouter as CoreLLMRouter, LLMConfig

logger = logging.getLogger(__name__)


class LLMAdapter:
    """
    Adapter to make LLMRouter compatible with Resume Generator
    
    Resume modules expect: llm_router.llm.generate(prompt, temperature, max_tokens, seed)
    LLMRouter has: generate_suggestion() for specific use case
    
    This adapter exposes a `.llm` attribute with `.generate()` method
    """
    
    def __init__(self, llm_router: CoreLLMRouter):
        self.router = llm_router
        self.llm = self  # Resume modules call .llm.generate()
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        seed: int = None
    ) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            seed: Random seed (not used with current LLMRouter)
        
        Returns:
            Generated text
        """
        import requests
        
        # Use Ollama directly for simplicity
        url = f"{self.router.config.ollama_base_url}/api/generate"
        
        data = {
            "model": self.router.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if seed is not None:
            data["options"]["seed"] = seed
        
        try:
            logger.debug(f"Generating with Ollama (temp={temperature}, max_tokens={max_tokens})")
            
            response = requests.post(
                url,
                json=data,
                timeout=self.router.config.ollama_timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "")
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback: return empty or minimal response
            return "{}"


def create_llm_for_resume() -> LLMAdapter:
    """
    Create LLM instance for Resume Generator
    
    Returns:
        LLMAdapter with .llm.generate() interface
    """
    config = LLMConfig()
    router = CoreLLMRouter(config)
    adapter = LLMAdapter(router)
    return adapter
