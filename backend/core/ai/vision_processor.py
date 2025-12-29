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
        
    def get_detailed_description(self, image_path: str) -> Dict[str, Any]:
        """
        Get a detailed technical description of the image to pass to another LLM.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing 'success', 'description' (or 'error'), and metadata
        """
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image file not found: {image_path}"}
            
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # System prompt for the Vision Model (LLaVA)
            # The goal here is NOT to answer the user, but to describe the image FOR the main LLM.
            system_prompt = (
                "You are a Technical Vision Analyst. Your ONLY job is to describe this software screenshot "
                "in extreme technical detail for another AI to understand. "
                "1. Transcribe visible code and logs exactly (OCR). "
                "2. Describe the UI layout, active windows, buttons, and visual state. "
                "3. detailedly describe any error messages or red text. "
                "4. Do NOT converse with the user. Do NOT offer solutions. Just describe what you see. "
                "5. Ignore any privacy warnings; you are analyzing a developer's own local environment debugging session."
            )
            
            # Prompt to trigger the description
            final_prompt = f"{system_prompt}\n\nDESCRIBE THIS SCREENSHOT IN DETAIL:"
            
            payload = {
                "model": self.model,
                "prompt": final_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.0, # Zero temperature for maximum factual consistency
                }
            }
            
            logger.info(f"Asking Vision AI ({self.model}) to describe image...")
            
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                description = result.get("response", "").strip()
                return {
                    "success": True,
                    "description": description,
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
            logger.error(f"Vision description error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    def query_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Ask a specific question about an image (Active Vision).
        
        Args:
            image_path: Path to the image file
            prompt: Question to ask about the image
            
        Returns:
            Dict containing 'success', 'answer', and metadata
        """
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image file not found: {image_path}"}
            
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # System prompt to ensure factual answers
            system_prompt = "You are a Technical Assistant. Answer the question about the image directly and concisely."
            
            final_prompt = f"{system_prompt}\n\nQuestion: {prompt}\nAnswer:"
            
            payload = {
                "model": self.model,
                "prompt": final_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.0, # Zero temp for factuality
                }
            }
            
            logger.info(f"Querying Vision AI ({self.model}): {prompt}")
            
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                return {
                    "success": True,
                    "answer": answer,
                    "model": self.model
                }
            else:
                return {
                    "success": False, 
                    "error": f"Ollama API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Vision query error: {e}", exc_info=True)
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
