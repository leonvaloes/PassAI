"""
ASR (Automatic Speech Recognition) Pipeline

Transcrição de áudio em texto usando OpenAI Whisper.
"""

import numpy as np
import whisper
import logging
import time
from typing import Optional, Dict, List, Union
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ASRConfig:
    """Configuração do pipeline ASR"""
    model_size: str = "tiny"  # tiny, base, small, medium, large
    device: str = "cuda" if __import__('torch').cuda.is_available() else "cpu"  # Auto-detect
    language: Optional[str] = "pt"  # Idioma (None = auto-detect)
    
    # Opções de transcrição
    task: str = "transcribe"  # transcribe ou translate
    temperature: float = 0.0  # Temperature para sampling
    best_of: int = 5  # Número de candidates
    beam_size: int = 5  # Beam search size
    
    # Timestamps
    word_timestamps: bool = True  # Timestamps por palavra
    
    # Outros
    fp16: bool = True  # Usar FP16 (auto com CUDA)
    verbose: bool = False  # Log detalhado


class ASRPipeline:
    """
    Pipeline de ASR usando OpenAI Whisper.
    
    Usage:
        asr = ASRPipeline(config=ASRConfig(model_size="tiny"))
        result = asr.transcribe(audio_array)
        print(result['text'])
    """
    
    def __init__(self, config: Optional[ASRConfig] = None):
        """
        Inicializa pipeline ASR.
        
        Args:
            config: Configuração ASR (usa padrão se None)
        """
        self.config = config or ASRConfig()
        
        logger.info(f"Initializing ASR Pipeline with model '{self.config.model_size}'")
        
        # Carregar modelo (pode demorar na primeira vez)
        start_time = time.time()
        self.model = whisper.load_model(
            self.config.model_size,
            device=self.config.device
        )
        load_time = time.time() - start_time
        
        logger.info(
            f"Whisper model '{self.config.model_size}' loaded in {load_time:.2f}s "
            f"(device: {self.config.device})"
        )
        
        # Estatísticas
        self.stats = {
            'total_transcriptions': 0,
            'total_duration_seconds': 0.0,
            'total_processing_time': 0.0
        }
    
    def transcribe(
        self,
        audio: Union[np.ndarray, str, Path],
        sample_rate: int = 16000
    ) -> Dict:
        """
        Transcreve áudio para texto.
        
        Args:
            audio: Array numpy ou caminho para arquivo de áudio
            sample_rate: Taxa de amostragem do áudio (padrão: 16kHz)
            
        Returns:
            Dict com:
                - text: Texto transcrito
                - language: Idioma detectado
                - segments: Lista de segmentos com timestamps
                - duration: Duração do áudio (segundos)
                - processing_time: Tempo de processamento (segundos)
                - words: (Opcional) Palavras com timestamps
        """
        start_time = time.time()
        
        # Preparar áudio
        audio_array = self._prepare_audio(audio, sample_rate)
        audio_duration = len(audio_array) / sample_rate
        
        logger.debug(f"Transcribing {audio_duration:.2f}s of audio")
        
        # FIX: Forçar GPU se CUDA disponível e device configurado
        if self.config.device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    # Mover model para GPU
                    self.model = self.model.to("cuda")
                    logger.debug("Model moved to CUDA for inference")
            except Exception as e:
                logger.warning(f"Could not move model to CUDA: {e}")
        
        # Transcrever
        try:
            # Usar FP16 quando CUDA está ativo
            use_fp16 = self.config.fp16 if self.config.device == "cuda" else False
            
            result = self.model.transcribe(
                audio_array,
                language=self.config.language,
                task=self.config.task,
                temperature=self.config.temperature,
                best_of=self.config.best_of,
                beam_size=self.config.beam_size,
                word_timestamps=self.config.word_timestamps,
                fp16=use_fp16,
                verbose=self.config.verbose
            )
            
            processing_time = time.time() - start_time
            
            # Atualizar estatísticas
            self.stats['total_transcriptions'] += 1
            self.stats['total_duration_seconds'] += audio_duration
            self.stats['total_processing_time'] += processing_time
            
            # Formatar resultado
            formatted_result = {
                'text': result['text'].strip(),
                'language': result['language'],
                'segments': self._format_segments(result.get('segments', [])),
                'duration': audio_duration,
                'processing_time': processing_time,
                'real_time_factor': processing_time / audio_duration if audio_duration > 0 else 0
            }
            
            # Adicionar words se disponível
            if self.config.word_timestamps:
                formatted_result['words'] = self._extract_words(result.get('segments', []))
            
            logger.info(
                f"Transcription complete: '{formatted_result['text'][:50]}...' "
                f"({audio_duration:.2f}s audio, {processing_time:.2f}s processing, "
                f"RTF: {formatted_result['real_time_factor']:.2f}x)"
            )
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def _prepare_audio(
        self,
        audio: Union[np.ndarray, str, Path],
        sample_rate: int
    ) -> np.ndarray:
        """
        Prepara áudio para transcrição.
        
        Whisper espera:
        - Mono (1 canal)
        - 16kHz sample rate
        - Float32 normalizado [-1, 1]
        """
        # Se for caminho, carregar arquivo
        if isinstance(audio, (str, Path)):
            audio = whisper.load_audio(str(audio))
        
        # Converter para numpy se necessário
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio)
        
        # Converter para float32 se necessário
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        
        # Resample para 16kHz se necessário
        if sample_rate != 16000:
            logger.warning(f"Resampling from {sample_rate}Hz to 16000Hz")
            audio = whisper.pad_or_trim(audio)
        
        # Garantir mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Pad ou trim para 30s (padrão Whisper)
        audio = whisper.pad_or_trim(audio)
        
        return audio
    
    def _format_segments(self, segments: List) -> List[Dict]:
        """Formata segmentos de transcrição."""
        formatted = []
        
        for segment in segments:
            formatted.append({
                'id': segment.get('id', 0),
                'start': segment.get('start', 0.0),
                'end': segment.get('end', 0.0),
                'text': segment.get('text', '').strip(),
                'confidence': segment.get('avg_logprob', 0.0)
            })
        
        return formatted
    
    def _extract_words(self, segments: List) -> List[Dict]:
        """Extrai palavras com timestamps dos segmentos."""
        words = []
        
        for segment in segments:
            if 'words' in segment:
                for word in segment['words']:
                    words.append({
                        'word': word.get('word', '').strip(),
                        'start': word.get('start', 0.0),
                        'end': word.get('end', 0.0),
                        'probability': word.get('probability', 0.0)
                    })
        
        return words
    
    def transcribe_file(self, file_path: Union[str, Path]) -> Dict:
        """
        Transcreve arquivo de áudio.
        
        Args:
            file_path: Caminho para arquivo de áudio
            
        Returns:
            Resultado da transcrição
        """
        logger.info(f"Transcribing file: {file_path}")
        return self.transcribe(file_path)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do pipeline."""
        stats = self.stats.copy()
        
        if stats['total_transcriptions'] > 0:
            stats['avg_processing_time'] = (
                stats['total_processing_time'] / stats['total_transcriptions']
            )
            stats['avg_audio_duration'] = (
                stats['total_duration_seconds'] / stats['total_transcriptions']
            )
            stats['avg_rtf'] = (
                stats['total_processing_time'] / stats['total_duration_seconds']
                if stats['total_duration_seconds'] > 0 else 0
            )
        
        return stats
    
    def reset_stats(self):
        """Reseta estatísticas."""
        self.stats = {
            'total_transcriptions': 0,
            'total_duration_seconds': 0.0,
            'total_processing_time': 0.0
        }
        logger.info("Statistics reset")
    
    @staticmethod
    def list_available_models() -> List[str]:
        """Lista modelos Whisper disponíveis."""
        return ["tiny", "base", "small", "medium", "large"]
    
    @staticmethod
    def get_model_info() -> Dict[str, Dict]:
        """Retorna informações sobre os modelos."""
        return {
            "tiny": {
                "parameters": "39M",
                "english_only": False,
                "required_vram": "~1GB",
                "relative_speed": "~32x"
            },
            "base": {
                "parameters": "74M",
                "english_only": False,
                "required_vram": "~1GB",
                "relative_speed": "~16x"
            },
            "small": {
                "parameters": "244M",
                "english_only": False,
                "required_vram": "~2GB",
                "relative_speed": "~6x"
            },
            "medium": {
                "parameters": "769M",
                "english_only": False,
                "required_vram": "~5GB",
                "relative_speed": "~2x"
            },
            "large": {
                "parameters": "1550M",
                "english_only": False,
                "required_vram": "~10GB",
                "relative_speed": "~1x"
            }
        }


class StreamingASR:
    """
    Versão streaming do ASR para processar áudio contínuo.
    
    Processa segmentos de áudio conforme chegam.
    """
    
    def __init__(self, asr_pipeline: ASRPipeline):
        """
        Args:
            asr_pipeline: Pipeline ASR configurado
        """
        self.asr = asr_pipeline
        self.pending_audio = []
        
    def process_chunk(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> Optional[Dict]:
        """
        Processa chunk de áudio.
        
        Se o chunk for grande o suficiente, transcreve.
        Caso contrário, acumula para processar depois.
        """
        self.pending_audio.extend(audio_chunk)
        
        # Se temos pelo menos 1s de áudio, processar
        if len(self.pending_audio) >= sample_rate:
            audio_array = np.array(self.pending_audio)
            result = self.asr.transcribe(audio_array, sample_rate)
            
            # Limpar buffer
            self.pending_audio = []
            
            return result
        
        return None
