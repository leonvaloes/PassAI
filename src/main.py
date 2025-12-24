"""
AI Copilot - Aplicação Final Integrada

Integra todos os componentes:
Audio Capture → ASR → Context → LLM → UI Overlay

Esta é a aplicação completa e funcional!
"""

import sys
import logging
import asyncio
import queue
import threading
from pathlib import Path

# Add project root to path (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

from src.capture.audio_capture import AudioCapture, AudioConfig
from src.processing.asr_pipeline import ASRPipeline, ASRConfig
from src.intelligence.context_manager import ConversationContext
from src.llm.router import LLMRouter, LLMConfig, LLMProvider
from src.ui.overlay import PrivateOverlay, OverlayConfig
from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.utils.hotkeys import HotkeyManager
from src.utils.session_export import SessionExporter

logger = logging.getLogger(__name__)


class AIWorkerThread(QThread):
    """
    Thread worker para processar áudio em background.
    
    Evita bloquear a UI thread do Qt.
    """
    
    transcription_ready = pyqtSignal(str, str)  # text, intent
    suggestion_ready = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self, context, asr, llm_router):
        super().__init__()
        self.context = context
        self.asr = asr
        self.llm_router = llm_router
        self.running = True
        
        # Fila assíncrona para LLM (não bloqueia transcrição)
        self.llm_queue = queue.Queue(maxsize=10)
        self.llm_thread = threading.Thread(target=self._llm_worker, daemon=True)
        self.llm_thread.start()
    
    def process_audio(self, audio, sample_rate):
        """Processa áudio: ASR → Context → LLM (async)."""
        if not self.running:
            return
        
        try:
            # Status
            self.status_update.emit("🎤 Transcribing...")
            
            # ASR (bloqueante, mas rápido ~0.3s)
            result = self.asr.transcribe(audio, sample_rate)
            text = result['text']
            
            # Context
            message = self.context.add_transcription(
                text=text,
                speaker="user",
                duration=result['duration']
            )
            
            intent = message.intent
            
            # Emitir transcrição IMEDIATAMENTE
            self.transcription_ready.emit(text, intent)
            
            # LLM assíncrono - não bloqueia próxima transcrição!
            llm_context = self.context.get_llm_context()
            llm_task = {
                'text': text,
                'conversation_history': llm_context['conversation_history'],
                'intent': intent,
                'user_goal': llm_context['user_profile']['goal']
            }
            
            # Adicionar à fila (não bloqueia)
            try:
                self.llm_queue.put_nowait(llm_task)
                self.status_update.emit("🟢 Ready (LLM processing in background...)")
            except queue.Full:
                logger.warning("LLM queue full, skipping suggestion")
                self.status_update.emit("🟢 Ready")
            
            logger.info(f"Transcribed: '{text[:50]}...'")
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            self.status_update.emit(f"❌ Error: {str(e)[:30]}")
    
    def _llm_worker(self):
        """Worker thread para processar LLM em background."""
        while self.running:
            try:
                # Pegar próxima tarefa (bloqueia com timeout)
                task = self.llm_queue.get(timeout=1.0)
                
                # Gerar sugestão (pode demorar ~3s)
                suggestion_result = self.llm_router.generate_suggestion(
                    conversation_history=task['conversation_history'],
                    current_intent=task['intent'],
                    user_goal=task['user_goal']
                )
                
                # Emitir sugestão quando pronta
                self.suggestion_ready.emit(suggestion_result['suggestion'])
                
                logger.info(f"LLM suggestion: '{task['text'][:30]}...' → '{suggestion_result['suggestion'][:50]}...'")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"LLM worker error: {e}")
    
    def stop(self):
        """Para thread."""
        self.running = False


class AICopilotApp:
    """
    Aplicação principal do AI Copilot.
    
    Integra todos os componentes e gerencia o ciclo de vida.
    """
    
    def __init__(self):
        """Inicializa aplicação."""
        logger.info("="*60)
        logger.info("🚀 Starting AI Copilot v0.1.0")
        logger.info("="*60)
        
        # Carregar configuração
        self.config = load_config()
        logger.info("✅ Configuration loaded")
        
        # Inicializar componentes
        self._init_components()
        
        # Qt Application
        self.qt_app = QApplication(sys.argv)
        
        # UI Overlay
        overlay_config = OverlayConfig(
            width=self.config.get('ui', {}).get('width', 450),
            height=self.config.get('ui', {}).get('height', 350),
            opacity=self.config.get('ui', {}).get('opacity', 0.95)
        )
        self.overlay = PrivateOverlay(config=overlay_config)
        
        # Worker thread
        self.worker = AIWorkerThread(self.context, self.asr, self.llm_router)
        self.worker.transcription_ready.connect(self._on_transcription)
        self.worker.suggestion_ready.connect(self._on_suggestion)
        self.worker.status_update.connect(self._on_status)
        
        # Session Export
        self.session_export = SessionExporter(output_dir="sessions")
        
        # Hotkeys
        self.hotkeys = HotkeyManager()
        self._setup_hotkeys()
        
        logger.info("✅ All components initialized")
    
    def _init_components(self):
        """Inicializa componentes core."""
        logger.info("Initializing components...")
        
        # Context Manager
        self.context = ConversationContext(
            window_size=self.config.get('context', {}).get('window_size', 10)
        )
        logger.info("  ✅ Context Manager")
        
        # ASR Pipeline
        asr_config = ASRConfig(
            model_size=self.config.get('asr', {}).get('model', 'tiny'),
            language=self.config.get('asr', {}).get('language', 'pt')
        )
        self.asr = ASRPipeline(config=asr_config)
        logger.info("  ✅ ASR Pipeline")
        
        # LLM Router
        llm_config = LLMConfig(
            default_provider=LLMProvider.OLLAMA,
            ollama_model=self.config.get('llm', {}).get('model', 'llama3.1:8b')
        )
        self.llm_router = LLMRouter(config=llm_config)
        logger.info("  ✅ LLM Router")
        
        # Audio Capture (configura depois)
        audio_config = AudioConfig(
            sample_rate=self.config.get('audio', {}).get('sample_rate', 16000),
            vad_threshold=self.config.get('audio', {}).get('vad_threshold', 0.02)
        )
        self.audio_capture = AudioCapture(
            config=audio_config,
            callback=self._on_speech_detected
        )
        logger.info("  ✅ Audio Capture")
    
    def _on_speech_detected(self, audio, sample_rate):
        """Callback quando detecta fala."""
        # Processa em background thread
        self.worker.process_audio(audio, sample_rate)
    
    def _on_transcription(self, text: str, intent: str):
        """Callback quando transcrição está pronta."""
        self.overlay.set_transcription(f"USER ({intent}): {text}")
        # Salvar na sessão
        self.session_export.add_transcription(text, intent)
    
    def _on_suggestion(self, suggestion: str):
        """Callback quando sugestão está pronta."""
        self.overlay.set_suggestion(suggestion)
        # Salvar na sessão
        self.session_export.add_suggestion(suggestion)
    
    def _on_status(self, status: str):
        """Callback para atualizar status."""
        self.overlay.set_status(status)
    
    def _setup_hotkeys(self):
        """Configura hotkeys globais."""
        # Ctrl+Shift+P - Pausar/Retomar
        self.hotkeys.register('ctrl+shift+p', self._toggle_pause)
        
        # Ctrl+Shift+C - Limpar contexto
        self.hotkeys.register('ctrl+shift+c', self._clear_context)
        
        # Ctrl+Shift+S - Salvar sessão
        self.hotkeys.register('ctrl+shift+s', self._save_session)
        
        logger.info("Hotkeys configured:")
        logger.info("  Ctrl+Shift+P - Pause/Resume")
        logger.info("  Ctrl+Shift+C - Clear Context")
        logger.info("  Ctrl+Shift+S - Save Session")
    
    def _toggle_pause(self):
        """Pausa/retoma captura de áudio."""
        if self.audio_capture.is_running:
            self.audio_capture.stop()
            self.overlay.set_status("⏸️ Paused (Ctrl+Shift+P to resume)")
            logger.info("Audio capture paused")
        else:
            self.audio_capture.start()
            self.overlay.set_status("🟢 Ready - Resumed")
            logger.info("Audio capture resumed")
    
    def _clear_context(self):
        """Limpa contexto de conversação."""
        # Reset context
        old_stats = self.context.get_stats()
        self.context = ConversationContext(
            window_size=self.config.get('context', {}).get('window_size', 10)
        )
        
        self.overlay.set_status("🧹 Context cleared")
        logger.info(f"Context cleared ({old_stats['total_messages']} messages removed)")
        
        # Atualizar worker
        self.worker.context = self.context
    
    def _save_session(self):
        """Salva sessão atual."""
        try:
            # Adicionar metadata
            stats = self.context.get_stats()
            self.session_export.set_metadata('total_messages', stats['total_messages'])
            self.session_export.set_metadata('questions', stats['questions_detected'])
            
            # Salvar ambos formatos
            json_path = self.session_export.export_json()
            md_path = self.session_export.export_markdown()
            
            self.overlay.set_status(f"💾 Session saved!")
            logger.info(f"Session saved: {json_path} & {md_path}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            self.overlay.set_status(f"❌ Save failed: {str(e)[:30]}")
    
    def run(self):
        """Executa aplicação."""
        logger.info("="*60)
        logger.info("🎤 AI Copilot is running!")
        logger.info("="*60)
        logger.info("- Speak and see real-time transcription + AI suggestions")
        logger.info("- Close the overlay window to exit")
        logger.info("="*60)
        
        # Mostrar overlay
        self.overlay.show()
        self.overlay.set_status("🟢 Ready - Start speaking!")
        
        # Iniciar hotkeys
        self.hotkeys.start()
        
        # Iniciar captura de áudio
        self.audio_capture.start()
        
        # Executar Qt event loop
        exit_code = self.qt_app.exec()
        
        # Cleanup
        self.cleanup()
        
        return exit_code
    
    def cleanup(self):
        """Limpa recursos."""
        logger.info("Shutting down...")
        
        # Parar hotkeys
        if self.hotkeys:
            self.hotkeys.stop()
        
        # Parar audio capture
        if self.audio_capture:
            self.audio_capture.stop()
        
        # Parar worker
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        
        # Estatísticas finais
        logger.info("\n" + "="*60)
        logger.info("📊 Session Statistics")
        logger.info("="*60)
        
        stats = self.context.get_stats()
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        asr_stats = self.asr.get_stats()
        logger.info(f"  total_transcriptions: {asr_stats['total_transcriptions']}")
        
        llm_stats = self.llm_router.get_stats()
        logger.info(f"  llm_requests: {llm_stats['total_requests']}")
        
        logger.info("="*60)
        logger.info("✅ AI Copilot stopped")
        logger.info("="*60)


def main():
    """Entry point."""
    # Setup logging
    setup_logging({
        'logging': {
            'level': 'INFO',
            'file': 'logs/ai-copilot.log'
        }
    })
    
    try:
        # Criar e executar app
        app = AICopilotApp()
        sys.exit(app.run())
        
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
