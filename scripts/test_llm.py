"""
Teste do LLM Router

Testa geração de sugestões com diferentes providers.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.router import LLMRouter, LLMConfig, LLMProvider

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_providers_status():
    """Testa status dos providers."""
    print("\n" + "="*60)
    print("TEST 1: Providers Status")
    print("="*60)
    
    router = LLMRouter()
    status = router.check_providers()
    
    print("\n📊 Provider Status:")
    for provider, available in status.items():
        emoji = "✅" if available else "❌"
        print(f"  {emoji} {provider.capitalize()}: {'Available' if available else 'Not available'}")
    
    print("\n" + "="*60)


def test_simple_suggestion():
    """Testa geração simples de sugestão."""
    print("\n" + "="*60)
    print("TEST 2: Simple Suggestion Generation")
    print("="*60)
    
    # Criar router
    config = LLMConfig(
        default_provider=LLMProvider.OLLAMA,
        enable_fallback=True
    )
    router = LLMRouter(config=config)
    
    # Histórico simples
    conversation = [
        {"speaker": "user", "text": "Olá, gostaria de saber mais sobre o produto."},
        {"speaker": "other", "text": "Claro! Nosso produto oferece..."},
        {"speaker": "user", "text": "Quanto custa?"}
    ]
    
    print("\n💬 Conversation:")
    for msg in conversation:
        speaker = "👤" if msg['speaker'] == 'user' else "🤖"
        print(f"  {speaker} {msg['text']}")
    
    print("\n🤔 Generating suggestion...")
    
    try:
        result = router.generate_suggestion(
            conversation_history=conversation,
            current_intent="question",
            user_goal="sales"
        )
        
        print(f"\n✅ Suggestion generated!")
        print(f"\n💡 SUGGESTION:")
        print(f"   {result['suggestion']}")
        print(f"\n📊 Metadata:")
        print(f"   Provider: {result['provider']}")
        print(f"   Model: {result['model']}")
        print(f"   Latency: {result['latency']:.2f}s")
        print(f"   Tokens: {result.get('tokens', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nℹ️ Make sure Ollama is running:")
        print("   - Install: winget install Ollama.Ollama")
        print("   - Run: ollama serve")
        print("   - Pull model: ollama pull llama3.1:8b-instruct-q4_K_M")
    
    print("\n" + "="*60)


def test_objection_handling():
    """Testa sugestão para objeção."""
    print("\n" + "="*60)
    print("TEST 3: Objection Handling")
    print("="*60)
    
    router = LLMRouter()
    
    conversation = [
        {"speaker": "user", "text": "Apresentação do produto X"},
        {"speaker": "other", "text": "Interessante, mas..."},
        {"speaker": "user", "text": "O preço está muito alto para nós."}
    ]
    
    print("\n💬 Conversation:")
    for msg in conversation:
        speaker = "👤" if msg['speaker'] == 'user' else "🤖"
        print(f"  {speaker} {msg['text']}")
    
    print("\n🎯 Intent: OBJECTION (price)")
    print("🤔 Generating persuasive response...")
    
    try:
        result = router.generate_suggestion(
            conversation_history=conversation,
            current_intent="objection",
            user_goal="sales",
            screen_context="Slide 5: Pricing - R$ 10,000/month"
        )
        
        print(f"\n💡 SUGGESTED RESPONSE:")
        print(f"   {result['suggestion']}")
        print(f"\n⚡ Generated in {result['latency']:.2f}s")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*60)


def test_interactive():
    """Teste interativo - você digita mensagens."""
    print("\n" + "="*60)
    print("TEST 4: Interactive Mode")
    print("="*60)
    
    router = LLMRouter()
    conversation = []
    
    print("\n📝 Interactive suggestion generator")
    print("   Type messages and get AI suggestions")
    print("   Commands: 'quit' to exit, 'stats' for statistics\n")
    
    while True:
        # Input do usuário
        user_input = input("YOU: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            break
        
        if user_input.lower() == 'stats':
            stats = router.get_stats()
            print("\n📊 Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            print()
            continue
        
        # Adicionar ao histórico
        conversation.append({
            "speaker": "user",
            "text": user_input
        })
        
        # Detectar intent simples
        intent = "neutral"
        if '?' in user_input or any(word in user_input.lower() for word in ['como', 'qual', 'quanto']):
            intent = "question"
        elif any(word in user_input.lower() for word in ['caro', 'preço', 'não']):
            intent = "objection"
        
        # Gerar sugestão
        try:
            print("🤔 Thinking...")
            result = router.generate_suggestion(
                conversation_history=conversation,
                current_intent=intent,
                user_goal="sales"
            )
            
            print(f"\n💡 SUGGESTION: {result['suggestion']}")
            print(f"   ({result['provider']}, {result['latency']:.1f}s)\n")
            
            # Opcional: adicionar resposta ao histórico
            # response = input("YOUR RESPONSE (or Enter to skip): ").strip()
            # if response:
            #     conversation.append({"speaker": "other", "text": response})
            
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    print("\n👋 Goodbye!")


def main():
    """Menu de testes."""
    print("\n" + "="*60)
    print("🤖 LLM ROUTER - TEST SUITE")
    print("="*60)
    
    choice = input("""
Escolha o teste:
1 - Check providers status
2 - Simple suggestion (RECOMENDADO se Ollama instalado) ⭐
3 - Objection handling
4 - Interactive mode
0 - Sair

Opção: """)
    
    if choice == '1':
        test_providers_status()
    elif choice == '2':
        test_simple_suggestion()
    elif choice == '3':
        test_objection_handling()
    elif choice == '4':
        test_interactive()
    elif choice == '0':
        print("\n👋 Goodbye!")
    else:
        print("Invalid option!")


if __name__ == "__main__":
    main()
