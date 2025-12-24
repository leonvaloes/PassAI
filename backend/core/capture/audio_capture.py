"""Captura de áudio com VAD (Voice Activity Detection) simplificado."""

import numpy as np
import sounddevice as sd
import queue
import threading
import logging
import wave
import os
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Configuração de captura de áudio"""
    sample_rate: int = 16000  # Hz
    channels: int = 1  # Mono
    chunk_duration_ms: int = 30  # Duração de cada chunk em ms
    dtype: str = 'int16'  # Tipo de dado
    
    # VAD (Voice Activity Detection) - ULTRA RÁPIDO
    vad_threshold: float = 0.02  # Threshold de energia para detectar voz
    min_speech_duration_ms: int = 200  # Mínimo de fala (0.2s = muito sensível)
    max_speech_gap_ms: int = 400  # Pausa de 0.4s já finaliza (MÁXIMA VELOCIDADE)
    
    # Streaming (transcrição em tempo real)
    streaming_enabled: bool = True  # Ativar transcrição incremental
    streaming_interval_ms: int = 2000  # Intervalo para emitir chunks parciais (2s)
    
    # Buffer
    max_buffer_seconds: int = 15  # Máximo de tempo em buffer


class SimpleVAD:
    """
    Voice Activity Detection simples baseado em energia do sinal.
    
    Para produção, considerar Silero VAD (PyTorch) ou WebRTC VAD.
    """
    
    def __init__(self, threshold: float = 0.02):
        self.threshold = threshold
        
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detecta se chunk contém fala baseado em energia.
        
        Args:
            audio_chunk: Array numpy com samples de áudio
            
        Returns:
            True se detectou fala, False caso contrário
        """
        # Normalizar para [-1, 1]
        if audio_chunk.dtype == np.int16:
            audio_normalized = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_normalized = audio_chunk
        
        # Calcular energia RMS (Root Mean Square)
        energy = np.sqrt(np.mean(audio_normalized ** 2))
        
        # Comparar com threshold
        return energy > self.threshold


class AudioCapture:
    """
    Captura áudio do microfone com detecção de voz e segmentação.
    
    Usage:
        def on_speech(audio, sample_rate):
            print(f"Speech detected: {len(audio)} samples")
        
        capture = AudioCapture(callback=on_speech)
        capture.start()
        
        # ... app running ...
        
        capture.stop()
    """
    
    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        callback: Optional[Callable] = None,
        device: Optional[int] = None
    ):
        """
        Inicializa captura de áudio.
        
        Args:
            config: Configuração de áudio (usa padrão se None)
            callback: Função chamada quando detecta fala (audio, sample_rate)
            device: ID do dispositivo de áudio (None = padrão)
        """
        self.config = config or AudioConfig()
        self.callback = callback
        self.device = device
        
        # Calcular tamanhos em samples
        self.chunk_size = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )
        self.min_speech_chunks = int(
            self.config.min_speech_duration_ms / self.config.chunk_duration_ms
        )
        self.max_gap_chunks = int(
            self.config.max_speech_gap_ms / self.config.chunk_duration_ms
        )
        
        # VAD
        self.vad = SimpleVAD(threshold=self.config.vad_threshold)
        
        # Estado
        self.is_speaking = False
        self.speech_chunks = 0
        self.silence_chunks = 0
        
        # Buffer circular para armazenar áudio durante fala
        max_buffer_chunks = int(
            self.config.max_buffer_seconds * 1000 / self.config.chunk_duration_ms
        )
        self.speech_buffer = deque(maxlen=max_buffer_chunks)
        
        # Fila para chunks processados
        self.audio_queue = queue.Queue(maxsize=100)
        
        # Stream
        self.gap_silence_chunks = 0
        self.is_running = False
        self.stream = None
        self._mic_save_counter = 0  # Debug: counter for saving mic audio
        
        logger.info(
            f"AudioCapture initialized: {self.config.sample_rate}Hz, "
            f"{self.config.channels}ch, chunk={self.chunk_size} samples"
        )
    
    def start(self):
        """Inicia captura de áudio."""
        if self.is_running:
            logger.warning("Audio capture already running")
            return
        
        logger.info(f"Starting audio capture (device: {self.device})")
        
        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                blocksize=self.chunk_size,
                dtype=self.config.dtype,
                callback=self._audio_callback
            )
            
            self.stream.start()
            self.is_running = True
            logger.info("Audio capture started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            raise
    
    def stop(self):
        """Para captura de áudio."""
        if not self.is_running:
            return
        
        logger.info("Stopping audio capture")
        self.is_running = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        logger.info("Audio capture stopped")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback executado a cada chunk de áudio capturado.
        
        Este método é chamado em uma thread separada pelo sounddevice.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Copiar dados (indata é read-only)
        audio_chunk = indata.copy().flatten()
        
        # Detectar fala
        is_speech = self.vad.is_speech(audio_chunk)
        
        # Máquina de estados para detecção de segmentos de fala
        if is_speech:
            self.speech_chunks += 1
            self.silence_chunks = 0
            
            # Adicionar ao buffer
            self.speech_buffer.append(audio_chunk)
            
            if not self.is_speaking and self.speech_chunks >= self.min_speech_chunks:
                # Início de fala detectado
                self.is_speaking = True
                logger.debug("Speech started")
        
        else:  # Silêncio
            self.silence_chunks += 1
            
            if self.is_speaking:
                # Ainda em segmento de fala, adicionar silêncio
                self.speech_buffer.append(audio_chunk)
                
                if self.silence_chunks >= self.max_gap_chunks:
                    # Fim de fala detectado
                    self._process_speech_segment()
                    self.is_speaking = False
                    self.speech_chunks = 0
                    logger.debug("Speech ended")
    
    def _process_speech_segment(self):
        """Processa segmento de fala completo."""
        if len(self.speech_buffer) == 0:
            return
        
        # Concatenar todos os chunks
        speech_audio = np.concatenate(list(self.speech_buffer))
        
        duration_seconds = len(speech_audio) / self.config.sample_rate
        logger.info(
            f"Speech segment: {len(speech_audio)} samples "
            f"({duration_seconds:.2f}s)"
        )
        
        # Adicionar à fila
        try:
            self.audio_queue.put_nowait({
                'audio': speech_audio,
                'sample_rate': self.config.sample_rate,
                'duration': duration_seconds,
                'channels': self.config.channels
            })
        except queue.Full:
            logger.warning("Audio queue full, dropping segment")
        
        # DEBUG: Save mic audio (every 10th segment)
        self._mic_save_counter += 1
        if self._mic_save_counter % 10 == 0:
            self._save_mic_debug(speech_audio)
        
        # Enviar para callback
        if self.callback:
            try:
                self.callback(speech_audio, self.config.sample_rate)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Limpar buffer
        self.speech_buffer.clear()
    
    def _save_mic_debug(self, audio_data: np.ndarray):
        """Salva um segmento de áudio do microfone para depuração."""
        debug_dir = "debug_audio_captures"
        os.makedirs(debug_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(debug_dir, f"mic_segment_{timestamp}.wav")
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.config.channels)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.config.sample_rate)
                wf.writeframes(audio_data.tobytes())
            logger.debug(f"Saved debug mic audio to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug mic audio to {filename}: {e}")
    
    def get_audio_segment(self, timeout: float = 1.0) -> Optional[dict]:
        """
        Retorna próximo segmento de áudio da fila.
        
        Args:
            timeout: Tempo máximo para esperar (segundos)
            
        Returns:
            Dict com 'audio', 'sample_rate', 'duration', 'channels'
            ou None se timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    @staticmethod
    def list_devices():
        """Lista dispositivos de áudio disponíveis."""
        devices = sd.query_devices()
        
        print("\n" + "="*60)
        print("Available Audio Devices:")
        print("="*60)
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"\n[{i}] {device['name']}")
                print(f"    Channels: {device['max_input_channels']} in")
                print(f"    Sample Rate: {device['default_samplerate']} Hz")
        
        print("\n" + "="*60)
        
        return devices
