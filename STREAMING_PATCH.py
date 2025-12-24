# Patch para Audio Capture - Streaming Transcription
# Adicione estes métodos à classe AudioCapture

def __init__(
    self,
    config: Optional[AudioConfig] = None,
    callback: Optional[Callable] = None,
    streaming_callback: Optional[Callable] = None,  # NOVO
    device: Optional[int] = None
):
    """MODIFICAR __init__ para aceitar streaming_callback"""
    # ... código existente ...
    self.streaming_callback = streaming_callback  # ADICIONAR esta linha
    
    # Streaming chunks (para transcrição em tempo real)
    self.streaming_chunk_count = int(
        self.config.streaming_interval_ms / self.config.chunk_duration_ms
    )
    self.chunks_since_last_streaming = 0


def _emit_streaming_chunk(self):
    """Emite chunk parcial para transcrição em tempo real."""
    if not self.streaming_callback or len(self.speech_buffer) == 0:
        return
    
    # Concatenar buffer atual (transcri\u00e7\u00e3o parcial)
    partial_audio = np.concatenate(list(self.speech_buffer))
    
    try:
        # Enviar com flag is_final=False
        self.streaming_callback(
            partial_audio, 
            self.config.sample_rate,
            is_final=False
        )
    except Exception as e:
        logger.error(f"Streaming callback error: {e}")


def _process_speech_segment(self, is_final=True):
    """Processa segmento de fala (final ou parcial)."""
    if len(self.speech_buffer) == 0:
        return
    
    # Concatenar todos os chunks
    speech_audio = np.concatenate(list(self.speech_buffer))
    
    duration_seconds = len(speech_audio) / self.config.sample_rate
    
    if is_final:
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
    
    # Callback apropriado
    if is_final and self.callback:
        try:
            self.callback(speech_audio, self.config.sample_rate)
        except Exception as e:
            logger.error(f"Callback error: {e}")
    elif not is_final and self.streaming_callback:
        try:
            self.streaming_callback(
                speech_audio, 
                self.config.sample_rate,
                is_final=True  # Último chunk da stream
            )
        except Exception as e:
            logger.error(f"Streaming callback error: {e}")
    
    # Limpar buffer apenas se final
    if is_final:
        self.speech_buffer.clear()


def _audio_callback(self, indata, frames, time_info, status):
    """Callback com suporte a streaming."""
    if status:
        logger.warning(f"Audio callback status: {status}")
    
    audio_chunk = indata.copy().flatten()
    is_speech = self.vad.is_speech(audio_chunk)
    
    if is_speech:
        self.speech_chunks += 1
        self.silence_chunks = 0
        self.speech_buffer.append(audio_chunk)
        
        if not self.is_speaking and self.speech_chunks >= self.min_speech_chunks:
            self.is_speaking = True
            self.chunks_since_last_streaming = 0
            logger.debug("Speech started")
        
        # STREAMING: emitir chunk parcial a cada N chunks
        if self.is_speaking and self.config.streaming_enabled:
            self.chunks_since_last_streaming += 1
            
            if self.chunks_since_last_streaming >= self.streaming_chunk_count:
                self._emit_streaming_chunk()
                self.chunks_since_last_streaming = 0
    
    else:  # Silêncio
        self.silence_chunks += 1
        
        if self.is_speaking:
            self.speech_buffer.append(audio_chunk)
            
            if self.silence_chunks >= self.max_gap_chunks:
                self._process_speech_segment(is_final=True)
                self.is_speaking = False
                self.speech_chunks = 0
                self.chunks_since_last_streaming = 0
                logger.debug("Speech ended")
