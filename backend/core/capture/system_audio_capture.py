"""
Simple System Audio Capture using PyAudioWPatch
"""

import numpy as np
import pyaudiowpatch as pyaudio
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class SystemAudioCapture:
    """Captures system audio (loopback) only"""
    
    def __init__(self, callback: Callable, sample_rate: int = 16000, device_index: int = None):
        self.callback = callback
        self.target_rate = sample_rate
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        
        # Audio configuration - 3s for real-time subtitles
        self.buffer_duration_ms = 3000  # 3s per user request
        self.samples_per_chunk = (self.target_rate * self.buffer_duration_ms) // 1000
        
        # Fixed gain - 10x (doubled per user request)
        self.adaptive_gain_enabled = False  # Fixed gain
        self.gain_min = 10.0  # Fixed
        self.gain_max = 10.0  # Fixed
        self.gain_current = 10.0  # 10x gain - doubled for higher volume
        self.target_rms = 0.10  # Not used
        
        # VAD configuration
        self.vad_enabled = True
        self.vad_threshold = 0.005  # Lower than mic (0.012) for system audio
        
        # Normalization
        self.normalize_enabled = False  # DISABLED - was causing issues
        
        # Noise reduction
        self.noise_reduction_enabled = False  # DISABLED - made hum worse
        self.highpass_freq = 80  # Hz - Remove low frequency hum/rumble
        
        # DEBUG MODE - Set to True to save all audio chunks
        self.debug_mode = True  # Re-enabled for debugging
        self.debug_save_interval = 1  # Save every chunk
        
        # Sentence-based segmentation (Balanced for stability)
        self.sentence_mode = True  # Enable sentence detection
        self.min_silence_duration = 0.2  # 200ms silence (balanced)
        self.min_segment_duration = 0.8  # Minimum 0.8s (prevent too many chunks)
        self.max_segment_duration = 3.0  # Maximum 3s (quick but stable)
        self.silence_threshold = 0.003  # RMS below this = silence
        
        # Tracking state
        self.is_speaking = False
        self.silence_start_time = None
        self.segment_start_time = None
        self.current_segment = []  # Accumulate current sentence
        self.samples_since_start = 0
        
        # Audio history for adaptive gain (last 10 chunks)
        self.rms_history = []
        self.max_history_length = 10
        
        # Audio accumulation
        self.audio_buffer = []
        
        # Device configuration
        self.channels = 2  # Stereo loopback device
        
        # Use specified device or find default
        self.loopback_device = device_index if device_index is not None else None
        self.device_rate = None
        
        if self.loopback_device is None:
            self._find_default_loopback()
        else:
            self._get_device_rate()
    
    def _get_device_rate(self):
        """Get sample rate for specified device"""
        try:
            device_info = self.p.get_device_info_by_index(self.loopback_device)
            self.device_rate = int(device_info["defaultSampleRate"])
            logger.info(f"✅ Using loopback device: {device_info['name']} (index {self.loopback_device}, {self.device_rate}Hz)")
        except Exception as e:
            logger.error(f"❌ Failed to get device info for index {self.loopback_device}: {e}")
            raise
    
    def _find_default_loopback(self):
        """Find default loopback device (fallback)"""
        try:
            wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self.p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            # Find loopback for default speakers
            for loopback in self.p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    self.loopback_device = loopback["index"]
                    self.device_rate = int(loopback["defaultSampleRate"])
                    logger.info(f"✅ Found default loopback: {loopback['name']} (index {self.loopback_device})")
                    return
            
            # If not found, use first loopback
            for loopback in self.p.get_loopback_device_info_generator():
                self.loopback_device = loopback["index"]
                self.device_rate = int(loopback["defaultSampleRate"])
                logger.info(f"✅ Using first loopback: {loopback['name']} (index {self.loopback_device})")
                return
                
        except Exception as e:
            logger.error(f"❌ Failed to find loopback device: {e}")
            raise
    
    def _has_speech(self, audio_data: np.ndarray) -> bool:
        """Detect if audio contains speech using simple VAD"""
        if not self.vad_enabled:
            return True  # Process all audio if VAD disabled
        
        rms = np.sqrt(np.mean(audio_data**2))
        return rms > self.vad_threshold
    
    def _calculate_adaptive_gain(self, audio_data: np.ndarray) -> float:
        """Calculate adaptive gain based on recent audio history"""
        if not self.adaptive_gain_enabled:
            return self.gain_current
        
        # Calculate current RMS
        rms = np.sqrt(np.mean(audio_data**2))
        
        # Update RMS history
        self.rms_history.append(rms)
        if len(self.rms_history) > self.max_history_length:
            self.rms_history.pop(0)
        
        # Calculate average RMS from history
        if len(self.rms_history) >= 3:  # Need at least 3 samples
            avg_rms = np.mean(self.rms_history)
            
            # Adjust gain to reach target RMS
            if avg_rms > 0.001:  # Avoid division by zero
                ideal_gain = self.target_rms / avg_rms
                # Smooth transition: move 20% towards ideal gain
                self.gain_current = self.gain_current * 0.8 + ideal_gain * 0.2
                # Clamp to safe range
                self.gain_current = np.clip(self.gain_current, self.gain_min, self.gain_max)
        
        return self.gain_current
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to use full dynamic range without clipping"""
        if not self.normalize_enabled:
            return audio_data
        
        peak = np.max(np.abs(audio_data))
        if peak > 0.01:  # Avoid normalizing silence
            # Normalize to -8dB (0.4) - balanced level
            return audio_data * (0.4 / peak)
        return audio_data
    
    def _analyze_audio_quality(self, audio_data: np.ndarray) -> dict:
        """Analyze audio quality metrics for logging"""
        rms = np.sqrt(np.mean(audio_data**2))
        peak = np.max(np.abs(audio_data))
        has_speech = self._has_speech(audio_data)
        
        return {
            'rms': rms,
            'peak': peak,
            'has_speech': has_speech,
            'gain': self.gain_current
        }
    
    def _remove_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Remove low-frequency hum and noise using high-pass filter"""
        if not self.noise_reduction_enabled or len(audio_data) < 100:
            return audio_data
        
        try:
            from scipy import signal as sp_signal
            
            # Design high-pass Butterworth filter (removes < 80Hz)
            # This removes electrical hum (50/60Hz) and low rumble
            nyquist = self.device_rate / 2
            cutoff = self.highpass_freq / nyquist
            
            if cutoff < 0.99:  # Only apply if cutoff is reasonable
                b, a = sp_signal.butter(4, cutoff, btype='high')
                # Apply filter (using filtfilt for zero-phase)
                filtered = sp_signal.filtfilt(b, a, audio_data)
                return filtered
        except Exception as e:
            logger.debug(f"Noise reduction failed: {e}")
        
        return audio_data
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process audio with adaptive gain, normalization, and VAD"""
        try:
            # Convert to numpy float
            audio_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # CRITICAL: Convert stereo to mono FIRST (device is 2 channels)
            if len(audio_data) % 2 == 0:  # Stereo
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)  # Average L+R channels
            
            # Remove low-frequency noise/hum BEFORE gain
            audio_data = self._remove_noise(audio_data)
            
            # DEBUG: Save raw audio before any processing (first chunk only to avoid spam)
            if self.debug_mode and not hasattr(self, '_saved_raw'):
                self._saved_raw = True
                if len(audio_data) > 16000:  # Only if decent size
                    raw_sample = audio_data[:16000]  # Save 1 second
                    self._save_debug_chunk(raw_sample, self.device_rate, "system_raw_input")
            
            # Calculate adaptive gain based on audio history
            gain = self._calculate_adaptive_gain(audio_data)
            
            # Apply gain
            audio_data = audio_data * gain
            
            # Normalize to prevent clipping and maximize dynamic range
            audio_data = self._normalize_audio(audio_data)
            
            # Clip as final safety measure
            audio_data = np.clip(audio_data, -1.0, 1.0)
            
            # Resample from device rate to target rate if needed
            if self.device_rate != self.target_rate:
                from scipy import signal
                # Use proper resampling with correct calculation
                num_samples = len(audio_data)
                duration = num_samples / self.device_rate  # Duration in seconds
                target_samples = int(duration * self.target_rate)  # Samples at target rate
                audio_resampled = signal.resample(audio_data, target_samples)
            else:
                audio_resampled = audio_data
            
            # Accumulate current sentence segment
            self.current_segment.extend(audio_resampled)
            self.samples_since_start += len(audio_resampled)
            
            # Calculate metrics
            segment_duration = self.samples_since_start / self.target_rate
            current_rms = np.sqrt(np.mean(audio_resampled**2))
            is_silent = current_rms < self.silence_threshold
            
            # Sentence-based segmentation
            if self.sentence_mode:
                import time
                
                if not is_silent:
                    # Speech detected
                    if not self.is_speaking:
                        self.is_speaking = True
                        if self.segment_start_time is None:
                            self.segment_start_time = time.time()
                    self.silence_start_time = None
                else:
                    # Silence detected
                    if self.is_speaking:
                        if self.silence_start_time is None:
                            self.silence_start_time = time.time()
                        
                        silence_duration = time.time() - self.silence_start_time
                        
                        # End of sentence: silence long enough + minimum duration met
                        if (silence_duration >= self.min_silence_duration and 
                            segment_duration >= self.min_segment_duration):
                            
                            # Safety: only process if we have enough samples
                            if len(self.current_segment) < self.target_rate * 0.3:  # At least 0.3s of audio
                                logger.debug(f"Skipping too-short segment: {len(self.current_segment)} samples")
                            else:
                                chunk = np.array(self.current_segment, dtype=np.float32)
                                quality = self._analyze_audio_quality(chunk)
                                
                                if quality['has_speech']:
                                    # Save debug
                                    if not hasattr(self, '_sentence_counter'):
                                        self._sentence_counter = 0
                                    self._sentence_counter += 1
                                    
                                    if self.debug_mode and (self._sentence_counter % self.debug_save_interval == 0):
                                        self._save_debug_chunk(chunk, self.target_rate, "sentence")
                                    
                                    logger.info(f"💬 Sentence #{self._sentence_counter} - {segment_duration:.1f}s | "\
                                              f"RMS: {quality['rms']:.4f} | Peak: {quality['peak']:.4f} | "\
                                              f"Gain: {quality['gain']:.1f}x")
                                    
                                    # Send complete sentence
                                    self.callback(chunk, self.target_rate, speaker="OUTROS")
                            
                            # Reset for next sentence
                            self.current_segment = []
                            self.samples_since_start = 0
                            self.segment_start_time = None
                            self.silence_start_time = None
                
                # Safety: max duration timeout
                if segment_duration >= self.max_segment_duration:
                    chunk = np.array(self.current_segment, dtype=np.float32)
                    quality = self._analyze_audio_quality(chunk)
                    
                    if quality['has_speech']:
                        if not hasattr(self, '_sentence_counter'):
                            self._sentence_counter = 0
                        self._sentence_counter += 1
                        
                        logger.info(f"⏱️ Max duration #{self._sentence_counter} - {segment_duration:.1f}s | "\
                                  f"RMS: {quality['rms']:.4f} | Gain: {quality['gain']:.1f}x")
                        
                        self.callback(chunk, self.target_rate, speaker="OUTROS")
                    
                    # Reset
                    self.current_segment = []
                    self.samples_since_start = 0
                    self.segment_start_time = None
                    self.is_speaking = False
                    self.silence_start_time = None
            
        except Exception as e:
            logger.error(f"Audio callback error: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def _save_debug_chunk(self, audio_chunk, sample_rate, source):
        """Save complete audio chunk to WAV file for debugging with detailed info"""
        try:
            import wave
            import os
            from datetime import datetime
            
            # Create debug folder
            debug_folder = "debug_audio"
            os.makedirs(debug_folder, exist_ok=True)
            
            # Calculate metrics
            rms = np.sqrt(np.mean(audio_chunk**2))
            peak = np.max(np.abs(audio_chunk))
            
            # Generate filename with metrics
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            chunk_num = getattr(self, '_chunk_counter', 0)
            filename = os.path.join(debug_folder, 
                f"{source}_chunk{chunk_num:03d}_{timestamp}_RMS{rms:.4f}_Peak{peak:.2f}_Gain{self.gain_current:.1f}x.wav")
            
            # Convert float to int16
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            
            # Save to WAV with CORRECT sample rate
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)  # Use the rate passed to function
                wav_file.writeframes(audio_int16.tobytes())
            
            logger.info(f"💾 Saved debug: {os.path.basename(filename)} ({len(audio_chunk)/sample_rate:.1f}s @ {sample_rate}Hz)")
            
        except Exception as e:
            logger.debug(f"Failed to save debug audio: {e}")
    
    def start(self):
        """Start the audio capture"""
        if self.loopback_device is None:
            logger.error("No loopback device found")
            return False
        
        try:
            # Initialize tracking variables BEFORE starting stream
            self.is_speaking = False
            self.silence_start_time = None
            self.segment_start_time = None
            self.current_segment = []
            self.samples_since_start = 0
            
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.device_rate,
                input=True,
                input_device_index=self.loopback_device,
                frames_per_buffer=512,
                stream_callback=self._audio_callback
            )
            
            self.is_running = True
            logger.info(f"✅ System audio capture started ({self.device_rate}Hz)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system audio capture: {e}")
            return False
    
    def stop(self):
        """Stop capturing"""
        if not self.is_running:
            return
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.is_running = False
        logger.info("System audio capture stopped")
    
    def __del__(self):
        self.stop()
        if hasattr(self, 'p'):
            self.p.terminate()
