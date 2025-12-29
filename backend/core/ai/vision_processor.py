import os
import base64
import requests
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VisionProcessor:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llava"  # Modelo de visão do Ollama
        
    def analyze_screenshot(self, image_path: str, prompt: str = None) -> dict:
        """
        Analisa screenshot com Vision AI
        
        Args:
            image_path: Caminho para a imagem
            prompt: Pergunta específica (opcional)
            
        Returns:
            {
                "success": bool,
                "analysis": str,
                "model": str,
                "error": str (if failed)
            }
        """
        try:
            # Verificar se arquivo existe
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"File not found: {image_path}"
                }
            
            # Ler e codificar imagem em base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prompt default se não fornecido
            if not prompt:
                prompt = """Analise esta screenshot e descreva:
1. O que você vê na imagem?
2. Qual parece ser o contexto (aplicativo, website, documento)?
3. Há alguma informação importante ou destaque?

Seja conciso mas informativo."""
            
            logger.info(f"📊 Analyzing screenshot with {self.model}...")
            
            # Chamar Ollama Vision API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False
                },
                timeout=60  # Vision pode demorar mais
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '').strip()
                
                logger.info(f"✅ Analysis complete: {len(analysis)} chars")
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "model": self.model,
                    "prompt": prompt
                }
            else:
                error_msg = f"Ollama returned status {response.status_code}"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama. Is it running?"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except requests.exceptions.Timeout:
            error_msg = "Ollama request timed out (60s)"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            logger.error(f"❌ Vision analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if Ollama is running and has llava model"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                has_llava = any('llava' in m['name'].lower() for m in models)
                if has_llava:
                    logger.info("✅ Ollama + LLaVA available")
                else:
                    logger.warning("⚠️ Ollama running but LLaVA not installed")
                return has_llava
            return False
        except:
            logger.warning("⚠️ Ollama not available")
            return False
    
    def get_status(self) -> dict:
        """Get detailed status of vision processor"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llava_models = [m for m in models if 'llava' in m['name'].lower()]
                
                if llava_models:
                    return {
                        "available": True,
                        "provider": "Ollama",
                        "model": llava_models[0]['name'],
                        "models": [m['name'] for m in llava_models]
                    }
                else:
                    return {
                        "available": False,
                        "provider": "Ollama",
                        "error": "LLaVA model not installed. Run: ollama pull llava"
                    }
            else:
                return {
                    "available": False,
                    "error": f"Ollama returned {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "available": False,
                "error": "Ollama not running. Start it with: ollama serve"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
