import os
import base64
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Processor for Vision AI tasks using Ollama + LLaVA"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llava"):
        self.ollama_url = ollama_url
        self.model = model
        
    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze an image using the vision model.
        
        Args:
            image_path: Path to the image file
            prompt: Text prompt/question about the image
            
        Returns:
            Dict containing 'success', 'response' (or 'error'), and metadata
        """
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image file not found: {image_path}"}
            
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Prepare request to Ollama
            # Add a system prompt to guide the model towards technical analysis and avoid false refusal
            system_prompt = (
                "You are a Senior Software Engineer assisting the developer (user) with their own code. "
                "The user has explicitly requested this analysis for debugging purposes. "
                "You have full permission to analyze the code, text, and UI shown in this image. "
                "Do NOT refuse to analyze. Do NOT mention privacy or permission. "
                "Focus purely on the technical content (syntax, logic, UI layout, errors) visible in the screenshot."
            )
            
            final_prompt = f"{system_prompt}\n\nUser Question: {prompt}"
            
            payload = {
                "model": self.model,
                "prompt": final_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.1, # Very low temperature for strict adherence to instructions
                }
            }
            
            logger.info(f"Sending image to Vision AI ({self.model})...")
            
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", "").strip(),
                    "model": self.model
                }
            else:
                return {
                    "success": False, 
                    "error": f"Ollama API error: {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Could not connect to Ollama. Make sure it is running on port 11434."
            }
        except Exception as e:
            logger.error(f"Vision analysis error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                # Check for llava or similar vision models
                return any(m.get("name", "").startswith(self.model) for m in models)
            return False
        except:
            return False
