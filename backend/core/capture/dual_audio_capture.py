"""
Dual Audio Capture - Captures both microphone and system audio simultaneously

Uses PyAudioWPatch for Windows WASAPI loopback to capture system audio.
"""

import numpy as np
import pyaudiowpatch as pyaudio
import logging
from typing import Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DualAudioConfig:
    """Configuration for dual audio capture"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    vad_threshold: float = 0.02
    silence_duration: float = 1.5  # seconds of silence before ending segment


class DualAudioCapture:
    """
    Captures two audio sources simultaneously:
    1. Microphone (input device) - Speaker: YOU
    2. System audio (loopback/output) - Speaker: OTHER
    """
    
    def __init__(
        self,
        config: DualAudioConfig,
        mic_callback: Callable,
        system_callback: Callable
    ):
        self.config = config
        self.mic_callback = mic_callback
        self.system_callback = system_callback
        
        self.p = pyaudio.PyAudio()
        self.mic_stream = None
        self.system_stream = None
        self.is_running = False
        
        # VAD state for each source
        self.mic_vad_state = {"is_speaking": False, "silence_chunks": 0, "buffer": []}
        self.system_vad_state = {"is_speaking": False, "silence_chunks": 0, "buffer": []}
        
        logger.info("DualAudioCapture initialized")
    
    def _find_loopback_device(self):
        """Find Windows WASAPI loopback device"""
        try:
            # Get default WASAPI output device
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self.p.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"]
            )
            
            if not default_speakers["isLoopbackDevice"]:
                # Find loopback device for default speakers
                for loopback in self.p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        return loopback["index"]
            
            return default_speakers["index"]
        except Exception as e:
            logger.error(f"Failed to find loopback device: {e}")
            return None
    
    def _vad_detect(self, audio_chunk: np.ndarray) -> bool:
        """Simple VAD based on RMS energy"""
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        return rms > self.config.vad_threshold
    
    def _mic_audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for microphone audio"""
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        is_speech = self._vad_detect(audio_data)
        state = self.mic_vad_state
        
        if is_speech:
            if not state["is_speaking"]:
                logger.debug("Microphone - Speech started")
                state["is_speaking"] = True
            
            state["buffer"].append(audio_data)
            state["silence_chunks"] = 0
        
        elif state["is_speaking"]:
            state["buffer"].append(audio_data)
            state["silence_chunks"] += 1
            
            silence_duration = (state["silence_chunks"] * frame_count) / self.config.sample_rate
            
            if silence_duration >= self.config.silence_duration:
                # End of speech segment
                full_audio = np.concatenate(state["buffer"])
                logger.info(f"Microphone - Speech segment: {len(full_audio)} samples")
                
                # Call callback with speaker="YOU"
                try:
                    self.mic_callback(full_audio, self.config.sample_rate, speaker="YOU")
                except Exception as e:
                    logger.error(f"Mic callback error: {e}")
                
                # Reset state
                state["is_speaking"] = False
                state["buffer"] = []
                state["silence_chunks"] = 0
        
        return (in_data, pyaudio.paContinue)
    
    def _system_audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for system audio (loopback)"""
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        is_speech = self._vad_detect(audio_data)
        state = self.system_vad_state
        
        if is_speech:
            if not state["is_speaking"]:
                logger.debug("System audio - Speech started")
                state["is_speaking"] = True
            
            state["buffer"].append(audio_data)
            state["silence_chunks"] = 0
        
        elif state["is_speaking"]:
            state["buffer"].append(audio_data)
            state["silence_chunks"] += 1
            
            silence_duration = (state["silence_chunks"] * frame_count) / self.config.sample_rate
            
            if silence_duration >= self.config.silence_duration:
                # End of speech segment
                full_audio = np.concatenate(state["buffer"])
                logger.info(f"System audio - Speech segment: {len(full_audio)} samples")
                
                # Call callback with speaker="OTHER"
                try:
                    self.system_callback(full_audio, self.config.sample_rate, speaker="OTHER")
                except Exception as e:
                    logger.error(f"System callback error: {e}")
                
                # Reset state
                state["is_speaking"] = False
                state["buffer"] = []
                state["silence_chunks"] = 0
        
        return (in_data, pyaudio.paContinue)
    
    def start(self):
        """Start capturing both audio sources"""
        if self.is_running:
            logger.warning("Already running")
            return
        
        try:
            # Start microphone stream
            self.mic_stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._mic_audio_callback
            )
            logger.info("✅ Microphone stream started")
            
            # Find and start loopback stream
            loopback_index = self._find_loopback_device()
            if loopback_index is not None:
                # Get device info to use its native sample rate
                device_info = self.p.get_device_info_by_index(loopback_index)
                loopback_rate = int(device_info['defaultSampleRate'])
                
                self.system_stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=loopback_rate,  # Use device's native rate
                    input=True,
                    frames_per_buffer=self.config.chunk_size,
                    input_device_index=loopback_index,
                    stream_callback=self._system_audio_callback
                )
                logger.info(f"✅ System audio (loopback) stream started at {loopback_rate}Hz")
            else:
                logger.warning("⚠️ Could not find loopback device - system audio disabled")
            
            self.is_running = True
            logger.info("✅ Dual audio capture started")
            
        except Exception as e:
            logger.error(f"Failed to start dual audio capture: {e}")
            self.stop()
    
    def stop(self):
        """Stop capturing both audio sources"""
        if not self.is_running:
            return
        
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
            logger.info("Microphone stream stopped")
        
        if self.system_stream:
            self.system_stream.stop_stream()
            self.system_stream.close()
            self.system_stream = None
            logger.info("System audio stream stopped")
        
        self.is_running = False
        logger.info("Dual audio capture stopped")
    
    def __del__(self):
        """Cleanup"""
        self.stop()
        if hasattr(self, 'p'):
            self.p.terminate()
