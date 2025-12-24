"""
Script de teste para o ASR Pipeline

Testa transcrição com Whisper de diferentes formas.
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.asr_pipeline import ASRPipeline, ASRConfig, StreamingASR
from src.capture.audio_capture import AudioCapture, AudioConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_model_info():
    """Testa informações dos modelos."""
    print("\n" + "="*60)
    print("TEST 1: Model Information")
    print("="*60)
    
    models = ASRPipeline.list_available_models()
    print(f"\nAvailable models: {', '.join(models)}\n")
    
    info = ASRPipeline.get_model_info()
    
    for model, details in info.items():
        print(f"{model.upper()}")
        print(f"  Parameters: {details['parameters']}")
        print(f"  VRAM: {details['required_vram']}")
        print(f"  Speed: {details['relative_speed']}")
        print()


def test_audio_transcription():
    """Testa transcrição de áudio ao vivo."""
    print("\n" + "="*60)
    print("TEST 2: Live Audio Transcription")
    print("="*60)
    
    # Configurar ASR
    print("\n📥 Loading Whisper model (this may take a moment)...")
    asr_config = ASRConfig(
        model_size="tiny",  # Modelo pequeno para teste
        language="pt",
        word_timestamps=True
    )
    asr = ASRPipeline(config=asr_config)
    print("✅ Model loaded!\n")
    
    # Contador
    transcription_count = [0]
    
    def on_speech(audio, sample_rate):
        """Callback quando detecta fala - transcreve imediatamente."""
        transcription_count[0] += 1
        
        print(f"\n{'='*60}")
        print(f"🎤 Transcription #{transcription_count[0]}")
        print(f"{'='*60}")
        
        # Transcrever
        result = asr.transcribe(audio, sample_rate)
        
        print(f"\n📝 Text: {result['text']}")
        print(f"🌐 Language: {result['language']}")
        print(f"⏱️  Duration: {result['duration']:.2f}s")
        print(f"⚡ Processing: {result['processing_time']:.2f}s")
        print(f"📊 RTF: {result['real_time_factor']:.2f}x")
        
        # Mostrar segmentos se houver
        if result['segments']:
            print(f"\n📍 Segments:")
            for seg in result['segments']:
                print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
        
        print(f"\n{'='*60}\n")
    
    # Configurar captura de áudio
    audio_config = AudioConfig(
        sample_rate=16000,
        vad_threshold=0.02,
        min_speech_duration_ms=500,  # Fala mais longa para melhor transcrição
        max_speech_gap_ms=1000
    )
    
    capture = AudioCapture(config=audio_config, callback=on_speech)
    
    print("📢 Fale algo em português! O sistema vai transcrever.")
    print("   (Pressione Ctrl+C para parar)\n")
    print("Aguardando fala...\n")
    
    try:
        capture.start()
        
        # Manter rodando
        while True:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏹ Parando...")
        capture.stop()
        
        # Estatísticas
        stats = asr.get_stats()
        print(f"\n📊 Estatísticas Finais:")
        print(f"   Total de transcrições: {stats['total_transcriptions']}")
        print(f"   Duração total de áudio: {stats['total_duration_seconds']:.2f}s")
        print(f"   Tempo total de processamento: {stats['total_processing_time']:.2f}s")
        if stats['total_transcriptions'] > 0:
            print(f"   Tempo médio de processamento: {stats['avg_processing_time']:.2f}s")
            print(f"   RTF médio: {stats['avg_rtf']:.2f}x")
        
        print("\n✅ Teste finalizado!")


def test_synthetic_audio():
    """Testa com áudio sintético (para debug)."""
    print("\n" + "="*60)
    print("TEST 3: Synthetic Audio Test")
    print("="*60)
    
    print("\n📥 Loading Whisper model...")
    asr = ASRPipeline(config=ASRConfig(model_size="tiny"))
    print("✅ Model loaded!\n")
    
    # Criar áudio sintético (silêncio)
    print("🔊 Creating 3 seconds of synthetic audio...")
    sample_rate = 16000
    duration = 3
    audio = np.zeros(sample_rate * duration, dtype=np.float32)
    
    # Adicionar um pouco de ruído para testar
    audio += np.random.normal(0, 0.01, len(audio))
    
    print("📝 Transcribing...")
    result = asr.transcribe(audio, sample_rate)
    
    print(f"\nText: '{result['text']}'")
    print(f"Language: {result['language']}")
    print(f"Processing time: {result['processing_time']:.2f}s")
    print(f"RTF: {result['real_time_factor']:.2f}x")
    
    print("\n✅ Teste finalizado!")


def test_streaming_mode():
    """Testa modo streaming do ASR."""
    print("\n" + "="*60)
    print("TEST 4: Streaming ASR")
    print("="*60)
    
    print("\n📥 Loading Whisper model...")
    asr = ASRPipeline(config=ASRConfig(model_size="tiny", language="pt"))
    streaming = StreamingASR(asr)
    print("✅ Model loaded!\n")
    
    transcription_count = [0]
    
    def on_speech(audio, sample_rate):
        """Processa áudio no modo streaming."""
        result = streaming.process_chunk(audio, sample_rate)
        
        if result:
            transcription_count[0] += 1
            print(f"\n✅ Transcription #{transcription_count[0]}: {result['text']}")
    
    # Captura
    capture = AudioCapture(callback=on_speech)
    
    print("📢 Fale algo! Modo streaming (mais rápido).")
    print("   (Pressione Ctrl+C para parar)\n")
    
    try:
        capture.start()
        
        while True:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏹ Parando...")
        capture.stop()
        print(f"\n📊 Total: {transcription_count[0]} transcrições")
        print("\n✅ Teste finalizado!")


def main():
    """Executa testes do ASR."""
    print("\n" + "="*60)
    print("🎙️  ASR PIPELINE - TEST SUITE")
    print("="*60)
    
    choice = input("""
Escolha o teste:
1 - Informações dos modelos
2 - Transcrição de áudio ao vivo (RECOMENDADO) ⭐
3 - Teste com áudio sintético (debug)
4 - Modo streaming
0 - Todos os testes

Opção: """)
    
    if choice == '1':
        test_model_info()
    elif choice == '2':
        test_audio_transcription()
    elif choice == '3':
        test_synthetic_audio()
    elif choice == '4':
        test_streaming_mode()
    elif choice == '0':
        test_model_info()
        input("\nPressione Enter para continuar...")
        test_synthetic_audio()
        input("\nPressione Enter para continuar...")
        test_audio_transcription()
    else:
        print("Opção inválida!")


if __name__ == "__main__":
    main()
