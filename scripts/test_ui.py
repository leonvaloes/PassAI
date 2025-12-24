"""
Teste da UI Overlay

Demonstra o overlay funcionando com atualizações simuladas.
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.overlay import PrivateOverlay, OverlayConfig


def test_basic_overlay():
    """Teste básico do overlay."""
    print("="*60)
    print("🖥️  UI OVERLAY - Basic Test")
    print("="*60)
    print("\nShowing overlay window...")
    print("- Drag the window to move it")
    print("- Click 'Clear' to clear content")
    print("- Click 'X' to close")
    print("\n" + "="*60)
    
    app = QApplication(sys.argv)
    
    # Criar overlay
    overlay = PrivateOverlay()
    
    # Mostrar mensagens de exemplo
    overlay.set_transcription("This is a sample transcription.")
    overlay.set_suggestion("This is an AI-generated suggestion!")
    overlay.set_status("🟢 Active")
    
    overlay.show()
    
    sys.exit(app.exec())


def test_live_updates():
    """Teste com atualizações em tempo real."""
    print("="*60)
    print("🖥️  UI OVERLAY - Live Updates Test")
    print("="*60)
    print("\nOverlay will update every 3 seconds...")
    print("Close the window to exit.")
    print("\n" + "="*60)
    
    app = QApplication(sys.argv)
    
    # Criar overlay
    config = OverlayConfig(
        width=450,
        height=350,
        opacity=0.98
    )
    overlay = PrivateOverlay(config=config)
    overlay.show()
    
    # Simular atualizações
    transcriptions = [
        "How much does this product cost?",
        "I'm not sure if this is right for us.",
        "What are the key features?",
        "Can you show me a demo?",
        "I need to think about it."
    ]
    
    suggestions = [
        "Great question! Let me walk you through our pricing tiers and ROI.",
        "I understand your concern. Let me share how other companies benefited.",
        "Absolutely! Our top 3 features are: scalability, ease of use, and 24/7 support.",
        "Of course! Let's schedule a personalized demo for your team.",
        "No problem! Can I address any specific concerns?"
    ]
    
    current_index = [0]  # Use list for closure
    
    def update_content():
        """Timer callback para atualizar conteúdo."""
        idx = current_index[0] % len(transcriptions)
        
        overlay.set_status(f"🎤 Processing... ({idx + 1}/{len(transcriptions)})")
        overlay.set_transcription(f"USER: {transcriptions[idx]}")
        
        # Aguardar um pouco antes de mostrar sugestão
        QTimer.singleShot(1000, lambda: overlay.set_suggestion(f"💡 {suggestions[idx]}"))
        QTimer.singleShot(1000, lambda: overlay.set_status("🟢 Ready"))
        
        current_index[0] += 1
    
    # Timer para updates
    timer = QTimer()
    timer.timeout.connect(update_content)
    timer.start(3000)  # A cada 3 segundos
    
    # Primeira atualização imediata
    update_content()
    
    sys.exit(app.exec())


def test_custom_style():
    """Teste com estilo personalizado."""
    print("="*60)
    print("🖥️  UI OVERLAY - Custom Style Test")
    print("="*60)
    print("\nShowing overlay with custom colors...")
    print("\n" + "="*60)
    
    app = QApplication(sys.argv)
    
    # Config personalizado
    config = OverlayConfig(
        width=500,
        height=400,
        background_color="#0a0a0a",  # Mais escuro
        text_color="#e0e0e0",
        accent_color="#00aaff",  # Azul
        opacity=0.92
    )
    
    overlay = PrivateOverlay(config=config)
    
    overlay.set_status("🎨 Custom Theme Active")
    overlay.set_transcription("This overlay has a custom blue theme!")
    overlay.set_suggestion("Try different colors by modifying OverlayConfig!")
    
    overlay.show()
    
    sys.exit(app.exec())


def main():
    """Menu de testes."""
    print("\n" + "="*60)
    print("🖥️  UI OVERLAY - TEST SUITE")
    print("="*60)
    
    choice = input("""
Escolha o teste:
1 - Basic overlay (static content)
2 - Live updates (simulated) ⭐
3 - Custom style
0 - Exit

Opção: """)
    
    if choice == '1':
        test_basic_overlay()
    elif choice == '2':
        test_live_updates()
    elif choice == '3':
        test_custom_style()
    elif choice == '0':
        print("\n👋 Goodbye!")
    else:
        print("Invalid option!")


if __name__ == "__main__":
    main()
