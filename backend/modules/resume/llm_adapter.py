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
        max_tokens: int = 20000,  # Increased to 20K for very detailed resumes
        seed: int = None
    ) -> str:
        """
        Generate text from prompt using configured LLM provider
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            seed: Random seed (not used with current LLMRouter)
        
        Returns:
            Generated text
        """
        # Use LLMRouter's generate method which respects the configured provider
        try:
            return self.router.generate(prompt, temperature, max_tokens, seed)
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
    import yaml
    import os
    
    # Load resume config to get LLM settings
    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    config_path = os.path.join(backend_dir, 'config', 'resume_config.yaml')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        resume_config = yaml.safe_load(f)['resume']
    
    # Create LLMConfig from resume_config.yaml
    from core.llm.router import LLMProvider
    
    provider_map = {
        "ollama": LLMProvider.OLLAMA,
        "openai": LLMProvider.OPENAI
    }
    
    llm_provider = provider_map.get(resume_config.get('llm_provider', 'ollama'), LLMProvider.OLLAMA)
    
    config = LLMConfig(
        default_provider=llm_provider,
        ollama_model=resume_config.get('llm_model', 'llama3.1:8b'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),  # Read from .env
        openai_model=resume_config.get('llm_model', 'gpt-4o-mini')
    )
    
    logger.info(f"Creating LLM for resume with provider: {llm_provider.value}, model: {resume_config.get('llm_model')}")
    
    router = CoreLLMRouter(config)
    adapter = LLMAdapter(router)
    return adapter
