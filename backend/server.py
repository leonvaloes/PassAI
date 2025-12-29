"""
Backend API Server - SIMPLE VERSION

Single microphone capture with AI chat support.
"""

import logging
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import threading
import os
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.capture.audio_capture import AudioCapture, AudioConfig
from core.processing.asr_pipeline import ASRPipeline, ASRConfig
from core.intelligence.conversation_manager_v2 import ConversationManager
from core.llm.router import LLMRouter, LLMConfig, LLMProvider
from core.utils.config import load_config
from core.utils.logger import setup_logging

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Copilot", version="2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from core.ai.vision_processor import VisionProcessor

class SimpleBackend:
    """Simple backend with mic capture and AI chat"""
    def __init__(self):
        self.config = load_config()
        self.websocket: Optional[WebSocket] = None
        self.is_paused = False
        self.ws_lock = threading.Lock()
        
        logger.info("Initializing...")
        
        # Conversation manager
        self.conversation = ConversationManager()
        
        # AI Chat history
        self.ai_chat_history = []
        
        # ASR (using 'base' for faster loading)
        self.asr = ASRPipeline(config=ASRConfig(model_size='base', language='pt'))
        
        # LLM
        self.llm_router = LLMRouter(config=LLMConfig(default_provider=LLMProvider.OLLAMA))
        
        # Vision AI
        self.vision_processor = VisionProcessor()
        self.last_screenshot_path: Optional[str] = None
        
        # Audio capture mode
        self.capture_active = False
        self.system_audio_enabled = False
        self.audio_capture = None
        self.dual_capture = None
        self.system_capture = None  # For system audio only
        
        # Start with single mic capture
        self._init_mic_capture()
        
        logger.info("✅ Ready (Captura parada - clique 'Iniciar Captura')")
    
    def _init_mic_capture(self):
        """Initialize microphone-only capture"""
        if self.dual_capture:
            self.dual_capture.stop()
            self.dual_capture = None
        
        self.audio_capture = AudioCapture(
            config=AudioConfig(sample_rate=16000),
            callback=self._on_audio
        )
        logger.info("Using microphone-only capture")
    
    def _init_dual_capture(self):
        """Initialize mic + system audio capture (separate streams)"""
        logger.info("=" * 50)
        logger.info("INITIALIZING MIC + SYSTEM AUDIO CAPTURE")
        logger.info("=" * 50)
        
        try:
            # Keep mic capture running
            if not self.audio_capture:
                logger.info("Starting microphone capture...")
                self.audio_capture = AudioCapture(
                    config=AudioConfig(sample_rate=16000),
                    callback=self._on_audio
                )
                self.audio_capture.start()
            
            # Add system audio capture with selected device
            logger.info(f"Starting system audio capture with device index: {self.selected_output_device}")
            from core.capture.system_audio_capture import SystemAudioCapture
            
            # Convert device index to int if it's a string
            device_idx = None
            if self.selected_output_device and self.selected_output_device != "default":
                try:
                    device_idx = int(self.selected_output_device)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid device index: {self.selected_output_device}, using default")
            
            self.system_capture = SystemAudioCapture(
                callback=self._on_audio_with_speaker,
                sample_rate=16000,
                device_index=device_idx,  # Pass specific device or None for default
                config=self.config
            )
            self.system_capture.start()
            
            logger.info("✅ Dual capture initialized successfully!")
            logger.info("=" * 50)
            
        except ImportError as e:
            logger.error(f"❌ Failed to import SystemAudioCapture: {e}")
            logger.error("PyAudioWPatch might not be installed")
            logger.info("Falling back to mic-only")
            if not self.audio_capture:
                self._init_mic_capture()
        except Exception as e:
            logger.error(f"❌ Failed to init system capture: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info("Mic capture will continue, system audio disabled")
    
    def _on_audio_with_speaker(self, audio, sample_rate, speaker):
        """Callback that includes speaker info (for system audio)"""
        if not self.capture_active or self.is_paused:
            return
        
        # Calculate and send audio level
        audio_level = self._calculate_audio_level(audio)
        source = "you" if speaker == "YOU" else "other"
        self._send_ws({
            "type": "audio_level",
            "data": {"source": source, "level": audio_level}
        })
        
        # Process transcription
        self._process_audio(audio, sample_rate, speaker)
    
    def _on_audio(self, audio, sample_rate):
        """Audio callback"""
        if not self.capture_active or self.is_paused:
            return
        
        # Calculate and send audio level for meter
        audio_level = self._calculate_audio_level(audio)
        self._send_ws({
            "type": "audio_level",
            "data": {"source": "you", "level": audio_level}
        })
        
        self._process_audio(audio, sample_rate, "YOU")
    
    def _on_dual_audio(self, audio, sample_rate, speaker):
        """Dual audio callback (includes speaker info)"""
        if not self.capture_active or self.is_paused:
            return
        
        # Calculate and send audio level
        audio_level = self._calculate_audio_level(audio)
        source = "you" if speaker == "YOU" else "other"
        self._send_ws({
            "type": "audio_level",
            "data": {"source": source, "level": audio_level}
        })
        
        # Process transcription
        self._process_audio(audio, sample_rate, speaker)
    
    def _process_audio(self, audio, sample_rate, speaker):
        """Process audio"""
        try:
            self._send_ws({"type": "status", "data": {"status": f"🎤 Transcribing..."}})
            
            result = self.asr.transcribe(audio, sample_rate)
            text = result['text']
            
            message = self.conversation.add_message(text=text, speaker=speaker)
            
            self._send_ws({
                "type": "conversation_message",
                "data": message.to_dict()
            })
            
            self._send_ws({"type": "status", "data": {"status": "🟢 Ready"}})
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            self._send_ws({"type": "status", "data": {"status": f"❌ Error"}})
    
    def _calculate_audio_level(self, audio):
        """Calculate audio level (0-100) for audio meters"""
        import numpy as np
        if audio.dtype == np.int16:
            audio_normalized = audio.astype(np.float32) / 32768.0
        else:
            audio_normalized = audio
        rms = np.sqrt(np.mean(audio_normalized ** 2))
        return min(100, int(rms * 500))
    
    def analyze_conversation(self, custom_prompt: str = ""):
        """Analyze conversation"""
        try:
            self._send_ws({"type": "status", "data": {"status": "🤖 Analyzing..."}})
            
            dialogue = self.conversation.get_formatted_dialogue()
            
            if not custom_prompt:
                custom_prompt = "Analise esta conversa:"
            
            full_prompt = f"""{custom_prompt}

{dialogue}

Análise:
"""
            
            history = [{"speaker": "user", "text": full_prompt}]
            
            response = self.llm_router.generate_suggestion(
                conversation_history=history,
                current_intent="analysis",
                user_goal="Analyze"
            )
            
            # Send as AI chat message
            self._send_ws({
                "type": "ai_chat_response",
                "data": {"text": f"📊 Análise:\n{response['suggestion']}"}
            })
            
            self._send_ws({"type": "status", "data": {"status": "🟢 Ready"}})
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            self._send_ws({"type": "status", "data": {"status": "❌ Failed"}})
    
    def handle_ai_chat(self, question: str):
        """Handle AI chat with Optional Vision Support"""
        try:
            self._send_ws({"type": "status", "data": {"status": "🤖 Thinking..."}})
            
            # Use Vision AI if we have an active screenshot
            image_path = self.last_screenshot_path
            vision_context = ""
            
            if image_path and os.path.exists(image_path):
                # Check cache first
                if hasattr(self, 'current_image_description') and self.current_image_description and self.current_image_path == image_path:
                    logger.info(f"Using CACHED Vision Description for: {os.path.basename(image_path)}")
                    description = self.current_image_description
                    vision_result = {"success": True} # Simulated success
                else:
                    logger.info(f"Generating NEW Vision Description for: {os.path.basename(image_path)}")
                    self._send_ws({"type": "status", "data": {"status": "👁️ Analisando Contexto Visual..."}})
                    
                    # Get pure description from Vision Model
                    vision_result = self.vision_processor.get_detailed_description(image_path)
                    
                    if vision_result["success"]:
                        description = vision_result["description"]
                        # Cache it
                        self.current_image_description = description
                        self.current_image_path = image_path
                        logger.info("✅ Vision Description Cached")
                
                if vision_result["success"]:
                    vision_context = f"""
[CONTEXTO VISUAL - DESCRIÇÃO DA IMAGEM ATUAL]
A seguinte descrição foi gerada por um modelo de visão AI sobre a imagem que o usuário enviou:
---
{description}
---
[FIM DO CONTEXTO VISUAL]
Use esta descrição para responder à pergunta do usuário como se você pudesse ver a imagem.
"""
                else:
                    logger.error(f"Vision failed: {vision_result.get('error')}")
                    vision_context = f"[ERRO NA ANÁLISE VISUAL: {vision_result.get('error')}]"

            # Prepare user message with context
            full_user_message = f"{vision_context}\n\n{question}" if vision_context else question
            
            self.ai_chat_history.append({"speaker": "user", "text": full_user_message})
            
            # Send to Main LLM (Text-only Router)
            response = self.llm_router.generate_suggestion(
                conversation_history=self.ai_chat_history[-10:], # Keep last 10 turns
                current_intent="chat",
                user_goal="Answer"
            )
            
            ai_response = response['suggestion']
            
            # CHECK FOR ACTIVE VISION REQUEST [LOOK: ...]
            if "[LOOK:" in ai_response:
                clean_response = ai_response # Fallback
                try:
                    import re
                    match = re.search(r"\[LOOK:\s*(.*?)\]", ai_response)
                    
                    # ALWAYS strip the tag for the final user display, purely for cleanliness
                    clean_response = re.sub(r"\[LOOK:\s*.*?\]", "", ai_response).strip()
                    if not clean_response:
                        clean_response = "Hmmm..." # Loading placeholder if empty

                    if match and image_path:
                        query = match.group(1).strip()
                        print("\n" + "="*60)
                        logger.info(f"🕵️‍♂️ ACTIVE VISION TRIGGERED")
                        logger.info(f"❓ Question: {query}")
                        self._send_ws({"type": "status", "data": {"status": f"👁️ Verificando: {query}..."}})
                        
                        # Query Vision AI
                        vision_query_res = self.vision_processor.query_image(image_path, query)
                        
                        if vision_query_res["success"]:
                            vision_answer = vision_query_res["answer"]
                            logger.info(f"💡 Answer:   {vision_answer}")
                            print("="*60 + "\n")
                            
                            # Feed back to Main LLM
                            nav_update = f"""[TOOL RESULT]
Vision Query: "{query}"
Vision Answer: "{vision_answer}"
Now answer the user's original question based on this new information."""
                            
                            self.ai_chat_history.append({"speaker": "system", "text": nav_update})
                            
                            # Re-prompt Main LLM
                            response_final = self.llm_router.generate_suggestion(
                                conversation_history=self.ai_chat_history[-10:],
                                current_intent="chat",
                                user_goal="Answer"
                            )
                            ai_response = response_final['suggestion']
                        else:
                            # Vision Failed
                            logger.warning("Active vision query failed")
                            ai_response = f"{clean_response}\n\n(Não consegui ver os detalhes: {vision_query_res.get('error')})"
                    
                    elif match and not image_path:
                         # Tag triggered but no image
                         logger.warning("Active vision triggered but NO IMAGE active")
                         ai_response = f"{clean_response}\n\n(Eu preciso que você capture um screenshot para eu ver isso.)"
                    else:
                         # Regex match failed but tag present?
                         ai_response = clean_response

                except Exception as ex:
                    logger.error(f"Re-Act Loop Error: {ex}")
                    ai_response = clean_response # Safe fallback
            
            self.ai_chat_history.append({"speaker": "assistant", "text": ai_response})
            
            self._send_ws({
                "type": "ai_chat_response",
                "data": {"text": ai_response}
            })
            
            self._send_ws({"type": "status", "data": {"status": "🟢 Ready"}})
            
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            
            # Send helpful error message to user
            error_msg = "⚠️ LLM não disponível. Verifique se o Ollama está rodando (http://localhost:11434) ou configure OpenAI API key."
            self._send_ws({
                "type": "ai_chat_response",
                "data": {"text": error_msg}
            })
            self._send_ws({"type": "status", "data": {"status": "⚠️ LLM Offline"}})
    
    def _send_ws(self, data):
        """Send WebSocket"""
        with self.ws_lock:
            if self.websocket:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.websocket.send_json(data))
                    loop.close()
                except:
                    pass


backend = SimpleBackend()


@app.get("/api/audio-devices")
async def get_audio_devices():
    """Get list of available audio devices (input, output, and loopback)"""
    try:
        import sounddevice as sd
        import pyaudiowpatch as pyaudio
        
        devices = sd.query_devices()
        
        audio_inputs = []
        audio_outputs = []
        loopback_devices = []
        
        # Get regular devices from sounddevice
        for i, device in enumerate(devices):
            device_info = {
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'] or device['max_output_channels'],
                'sample_rate': device['default_samplerate']
            }
            
            if device['max_input_channels'] > 0:
                audio_inputs.append(device_info)
            
            if device['max_output_channels'] > 0:
                audio_outputs.append(device_info)
        
        # Get ALL loopback devices specifically
        try:
            p = pyaudio.PyAudio()
            for loopback in p.get_loopback_device_info_generator():
                loopback_info = {
                    'index': loopback['index'],
                    'name': loopback['name'],
                    'channels': loopback['maxInputChannels'],
                    'sample_rate': loopback['defaultSampleRate'],
                    'isLoopback': True
                }
                loopback_devices.append(loopback_info)
            p.terminate()
        except Exception as e:
            logger.error(f"Failed to enumerate loopback devices: {e}")
        
        return {
            'inputs': audio_inputs,
            'outputs': audio_outputs,
            'loopbacks': loopback_devices  # NEW: separate list of loopback devices
        }
    except Exception as e:
        logger.error(f"Failed to get audio devices: {e}")
        return {'inputs': [], 'outputs': [], 'loopbacks': []}


@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting...")
    if backend.audio_capture:
        backend.audio_capture.start()
    elif backend.dual_capture:
        backend.dual_capture.start()


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 Stopping...")
    if backend.audio_capture:
        backend.audio_capture.stop()
    if backend.dual_capture:
        backend.dual_capture.stop()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    backend.websocket = websocket
    logger.info("✅ WebSocket connected")
    
    try:
        await websocket.send_json({"type": "status", "data": {"status": "🟢 Ready"}})
        
        for message in backend.conversation.get_messages():
            await websocket.send_json({
                "type": "conversation_message",
                "data": message
            })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ai_chat":
                question = data.get("data", {}).get("question", "")
                if question:
                    threading.Thread(
                        target=backend.handle_ai_chat,
                        args=(question,)
                    ).start()
            
            elif data.get("type") == "command":
                action = data.get("data", {}).get("action")
                
                if action == "start_capture":
                    backend.capture_active = True
                    await websocket.send_json({
                        "type": "status",
                        "data": {"status": "🎙️ Capturando áudio..."}
                    })
                    logger.info("🎙️ Audio capture STARTED")
                    
                elif action == "stop_capture":
                    backend.capture_active = False
                    await websocket.send_json({
                        "type": "status",
                        "data": {"status": "⏸️ Captura pausada"}
                    })
                    logger.info("⏹️ Audio capture STOPPED")
                
                elif action == "toggle_system_audio":
                    command_data = data.get("data", {})
                    enabled = command_data.get("enabled", False)
                    output_device = command_data.get("output_device", "default")
                    
                    logger.info(f"Toggle system audio: {enabled}, device: {output_device}")
                    
                    backend.system_audio_enabled = enabled
                    backend.selected_output_device = output_device
                    was_active = backend.capture_active
                    
                    if was_active:
                        if backend.audio_capture:
                            backend.audio_capture.stop()
                        if backend.dual_capture:
                            backend.dual_capture.stop()
                    
                    if enabled and output_device != "default":
                        logger.info(f"Initializing dual capture with output device: {output_device}")
                        backend._init_dual_capture()
                    else:
                        logger.info("Using mic-only capture")
                        backend._init_mic_capture()
                    
                    if was_active:
                        if backend.dual_capture:
                            backend.dual_capture.start()
                        elif backend.audio_capture:
                            backend.audio_capture.start()
                    
                    status = f"🔊 Sistema (device {output_device}) + Mic" if enabled else "🎙️ Só microfone"
                    await websocket.send_json({"type": "status", "data": {"status": status}})
                
                elif action == "pause":
                    backend.is_paused = True
                    await websocket.send_json({"type": "status", "data": {"status": "⏸️ Paused"}})
                    
                elif action == "resume":
                    backend.is_paused = False
                    await websocket.send_json({"type": "status", "data": {"status": "🟢 Resumed"}})
                    
                elif action == "clear":
                    backend.conversation.clear()
                    backend.ai_chat_history = []  # Also clear AI chat history
                    backend.last_screenshot_path = None  # Clear Vision Context
                    backend.current_image_description = None # Clear Cache
                    backend.current_image_path = None
                    logger.info("🧹 Conversation and Context cleared")
                    await websocket.send_json({"type": "conversation_cleared"})
                    await websocket.send_json({"type": "status", "data": {"status": "🧹 Cleared"}})
                    
                elif action == "save":
                    try:
                        md = backend.conversation.export_markdown()
                        import os
                        os.makedirs("conversations", exist_ok=True)
                        filename = f"conversations/conv_{backend.conversation.conversation_id}.md"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(md)
                        await websocket.send_json({"type": "status", "data": {"status": "💾 Saved!"}})
                    except Exception as e:
                        logger.error(f"Save error: {e}")
                        await websocket.send_json({"type": "status", "data": {"status": "❌ Failed"}})
                
                elif action == "analyze":
                    threading.Thread(
                        target=backend.analyze_conversation,
                        args=("",)
                    ).start()
                        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        backend.websocket = None


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gpu": backend.asr.config.device == "cuda",
        "messages": len(backend.conversation.messages)
    }


# Screenshot API Endpoints
from core.capture.screenshot_capture import ScreenshotCapture
from pydantic import BaseModel


class ScreenshotRequest(BaseModel):
    monitor: int = 0  # 0 = all monitors, 1+ = specific monitor
    analyze: bool = False  # Future: vision analysis


@app.post("/api/screenshot")
async def capture_screenshot(request: ScreenshotRequest):
    """Capture screenshot"""
    try:
        # Initialize on demand to avoid startup issues
        screenshot_capture = ScreenshotCapture()
        filepath, img = screenshot_capture.capture_screen(request.monitor)
        
        if filepath is None:
            return {
                "success": False,
                "error": "Failed to capture screenshot"
            }
        
        result = {
            "success": True,
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "timestamp": datetime.now().isoformat(),
            "size": {
                "width": img.size[0],
                "height": img.size[1]
            }
        }
        
        # Future: Add vision analysis here if request.analyze is True
        
        logger.info(f"📸 Screenshot captured: {filepath}")
        
        # Store context for Vision AI
        backend.last_screenshot_path = filepath
        
        return result
        
    except Exception as e:
        logger.error(f"Screenshot capture error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/screenshots")
async def list_screenshots(limit: int = 20):
    """List recent screenshots"""
    try:
        screenshot_capture = ScreenshotCapture()
        screenshots = screenshot_capture.list_screenshots(limit)
        return {
            "success": True,
            "screenshots": screenshots,
            "count": len(screenshots)
        }
    except Exception as e:
        logger.error(f"List screenshots error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/monitors")
async def get_monitors():
    """Get available monitors"""
    try:
        screenshot_capture = ScreenshotCapture()
        monitors = screenshot_capture.get_monitors()
        return {
            "success": True,
            "monitors": monitors,
            "count": len(monitors)
        }
    except Exception as e:
        logger.error(f"Get monitors error: {e}")
        return {
            "success": False,
            "error": str(e)
        }



# Serve screenshot files
screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

if __name__ == "__main__":
    setup_logging({'logging': {'level': 'INFO'}})
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
