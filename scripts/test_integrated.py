"""
Teste integrado: Audio Capture + ASR + Context Manager

Demonstra o pipeline completo funcionando junto.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.capture.audio_capture import AudioCapture, AudioConfig
from src.processing.asr_pipeline import ASRPipeline, ASRConfig
from src.intelligence.context_manager import ConversationContext, ScreenContext

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_context_manager():
    """Testa Context Manager isoladamente."""
    print("\n" + "="*60)
    print("TEST 1: Context Manager")
    print("="*60)
    
    # Criar contexto
    context = ConversationContext(window_size=5)
    
    print(f"\nSession ID: {context.session_id[:8]}...")
    print(f"Window size: {context.window_size}")
    
    # Adicionar algumas mensagens
    print("\n📝 Adding messages...")
    
    context.add_transcription("Olá, como funciona o produto?", speaker="user")
    context.add_transcription("Deixe-me explicar as funcionalidades.", speaker="other")
    context.add_transcription("Quanto custa?", speaker="user")
    context.add_transcription("O preço está muito alto para nós.", speaker="user")
    context.add_transcription("Entendo, posso mostrar o ROI.", speaker="other")
    
    # Mostrar histórico
    print("\n💬 Recent messages:")
    for msg in context.get_recent_messages():
        print(f"  [{msg.speaker}] {msg.text} (intent: {msg.intent})")
    
    # Estatísticas
    print("\n📊 Statistics:")
    stats = context.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Contexto para LLM
    print("\n🤖 LLM Context:")
    llm_ctx = context.get_llm_context()
    print(f"  Messages in context: {len(llm_ctx['conversation_history'])}")
    print(f"  Questions: {llm_ctx['stats']['questions_detected']}")
    print(f"  Objections: {llm_ctx['stats']['objections_detected']}")
    
    # Resumo
    print("\n📋 Summary:")
    print(context.get_conversation_summary())
    
    print("\n✅ Test complete!")


def test_integrated_pipeline():
    """Testa pipeline completo integrado."""
    print("\n" + "="*60)
    print("TEST 2: Integrated Pipeline (Audio → ASR → Context)")
    print("="*60)
    
    # Setup componentes
    print("\n⚙️  Initializing components...")
    
    # Context Manager
    context = ConversationContext(window_size=10)
    print(f"✅ Context Manager (session: {context.session_id[:8]}...)")
    
    # ASR Pipeline
    print("📥 Loading Whisper model...")
    asr = ASRPipeline(config=ASRConfig(model_size="tiny", language="pt"))
    print("✅ ASR Pipeline ready")
    
    # Audio Capture com integração
    def on_speech(audio, sample_rate):
        """Processa fala: ASR → Context"""
        print(f"\n{'='*60}")
        print("🎤 Speech detected, processing...")
        print(f"{'='*60}")
        
        # Transcrever
        result = asr.transcribe(audio, sample_rate)
        
        # Adicionar ao contexto
        message = context.add_transcription(
            text=result['text'],
            speaker="user",
            confidence=result.get('confidence', 1.0),
            duration=result['duration']
        )
        
        # Mostrar resultado
        print(f"\n📝 Transcription: {result['text']}")
        print(f"🎯 Intent detected: {message.intent}")
        print(f"⏱️  Processing: {result['processing_time']:.2f}s")
        
        # Mostrar contexto atual
        print(f"\n💬 Recent conversation ({len(context.messages)} total):")
        for msg in context.get_recent_messages(3):
            emoji = "👤" if msg.speaker == "user" else "🤖"
            print(f"  {emoji} {msg.text}")
        
        # Estatísticas
        stats = context.get_stats()
        print(f"\n📊 Session stats:")
        print(f"  Questions: {stats['questions_detected']}")
        print(f"  Objections: {stats['objections_detected']}")
        print(f"  Agreements: {stats['agreements_detected']}")
        print(f"{'='*60}\n")
    
    audio_config = AudioConfig(
        sample_rate=16000,
        vad_threshold=0.02,
        min_speech_duration_ms=500,
        max_speech_gap_ms=1000
    )
    
    capture = AudioCapture(config=audio_config, callback=on_speech)
    
    print("\n" + "="*60)
    print("📢 FALE ALGO!")
    print("="*60)
    print("\nExemplos:")
    print("  - Perguntas: 'Como funciona?', 'Quanto custa?'")
    print("  - Objeções: 'Está muito caro', 'Não tenho certeza'")
    print("  - Acordo: 'Ok, concordo', 'Perfeito'")
    print("\n(Pressione Ctrl+C para parar)")
    print("="*60 + "\n")
    
    try:
        capture.start()
        
        # Manter rodando
        while True:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping...")
        capture.stop()
        
        # Resumo final
        print("\n" + "="*60)
        print("📋 SESSION SUMMARY")
        print("="*60)
        print(context.get_conversation_summary())
        
        # Exportar sessão
        export_path = f"session_{context.session_id[:8]}.json"
        context.export_session(export_path)
        print(f"\n💾 Session saved to: {export_path}")
        
        print("\n✅ Test complete!")


def test_screen_context():
    """Testa adição de contexto de tela."""
    print("\n" + "="*60)
    print("TEST 3: Screen Context")
    print("="*60)
    
    context = ConversationContext()
    
    # Simular contexto de tela
    screen = ScreenContext(
        extracted_text="Slide 1: Apresentação do Produto\n- Recurso A\n- Recurso B\n- Preço: R$ 1.000",
        slide_number=1,
        key_entities=["Produto", "Recurso A", "Recurso B", "R$ 1.000"],
        visual_summary="Slide de apresentação com 3 recursos principais e preço"
    )
    
    context.update_screen_context(screen)
    
    # Adicionar mensagens
    context.add_transcription("Vejo que o preço é R$ 1.000, correto?")
    context.add_transcription("Sim, mas temos desconto para volume.")
    
    # Contexto para LLM (com tela)
    llm_ctx = context.get_llm_context(include_screen=True)
    
    print("\n🖥️  Screen context:")
    print(f"  Slide: {llm_ctx['current_screen']['slide_number']}")
    print(f"  Text: {llm_ctx['current_screen']['text'][:100]}...")
    print(f"  Summary: {llm_ctx['current_screen']['summary']}")
    
    print("\n💬 Conversation:")
    for msg in llm_ctx['conversation_history']:
        print(f"  [{msg['speaker']}] {msg['text']}")
    
    print("\n✅ Test complete!")


def main():
    """Menu de testes."""
    print("\n" + "="*60)
    print("🧠 CONTEXT MANAGER - TEST SUITE")
    print("="*60)
    
    choice = input("""
Escolha o teste:
1 - Context Manager isolado
2 - Pipeline integrado (Audio + ASR + Context) ⭐
3 - Screen Context
0 - Todos

Opção: """)
    
    if choice == '1':
        test_context_manager()
    elif choice == '2':
        test_integrated_pipeline()
    elif choice == '3':
        test_screen_context()
    elif choice == '0':
        test_context_manager()
        input("\nPress Enter to continue...")
        test_screen_context()
        input("\nPress Enter to continue...")
        test_integrated_pipeline()
    else:
        print("Invalid option!")


if __name__ == "__main__":
    main()
