"""
Script de teste para o módulo Audio Capture

Testa captura de áudio, VAD e segmentação.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.capture.audio_capture import AudioCapture, AudioConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_list_devices():
    """Testa listagem de dispositivos de áudio."""
    print("\n" + "="*60)
    print("TEST 1: List Audio Devices")
    print("="*60)
    
    AudioCapture.list_devices()


def test_audio_capture():
    """Testa captura de áudio com VAD."""
    print("\n" + "="*60)
    print("TEST 2: Audio Capture with VAD")
    print("="*60)
    
    # Contador de segmentos
    segment_count = [0]  # Use list para modificar em callback
    
    def on_speech_detected(audio, sample_rate):
        """Callback quando detecta fala."""
        segment_count[0] += 1
        duration = len(audio) / sample_rate
        print(f"\n✅ Speech segment #{segment_count[0]}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Samples: {len(audio)}")
        print(f"   Sample rate: {sample_rate}Hz")
    
    # Configuração
    config = AudioConfig(
        sample_rate=16000,
        vad_threshold=0.02,  # Ajustar se necessário
        min_speech_duration_ms=300,
        max_speech_gap_ms=800
    )
    
    # Criar capture
    capture = AudioCapture(config=config, callback=on_speech_detected)
    
    print("\n📢 Fale algo! O sistema está ouvindo...")
    print("   (Pressione Ctrl+C para parar)")
    print("\nAguardando fala...\n")
    
    try:
        # Iniciar captura
        capture.start()
        
        # Manter rodando
        while True:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏹ Parando captura...")
        capture.stop()
        
        print(f"\n📊 Estatísticas:")
        print(f"   Total de segmentos: {segment_count[0]}")
        print("\n✅ Teste finalizado!")


def test_audio_queue():
    """Testa fila de áudio (sem callback)."""
    print("\n" + "="*60)
    print("TEST 3: Audio Queue")
    print("="*60)
    
    config = AudioConfig(sample_rate=16000)
    capture = AudioCapture(config=config)  # Sem callback
    
    print("\n📢 Fale algo! Testando fila de áudio...")
    print("   (O teste vai rodar por 10 segundos)")
    
    try:
        capture.start()
        
        start_time = time.time()
        segment_count = 0
        
        while time.time() - start_time < 10:
            # Tentar pegar segmento da fila
            segment = capture.get_audio_segment(timeout=0.5)
            
            if segment:
                segment_count += 1
                print(f"\n✅ Segmento #{segment_count} da fila")
                print(f"   Duration: {segment['duration']:.2f}s")
                print(f"   Samples: {len(segment['audio'])}")
        
        capture.stop()
        
        print(f"\n📊 Total de segmentos: {segment_count}")
        print("\n✅ Teste finalizado!")
    
    except KeyboardInterrupt:
        print("\n⏹ Interrompido")
        capture.stop()


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("🎤 AUDIO CAPTURE MODULE - TEST SUITE")
    print("="*60)
    
    choice = input("""
Escolha o teste:
1 - Listar dispositivos de áudio
2 - Testar captura com VAD (recomendado)
3 - Testar fila de áudio
0 - Todos os testes

Opção: """)
    
    if choice == '1':
        test_list_devices()
    elif choice == '2':
        test_audio_capture()
    elif choice == '3':
        test_audio_queue()
    elif choice == '0':
        test_list_devices()
        input("\nPressione Enter para continuar...")
        test_audio_capture()
    else:
        print("Opção inválida!")


if __name__ == "__main__":
    main()
