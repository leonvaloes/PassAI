"""
Modern UI Overlay - Perssua Style (Clean & Minimal)

Design clean e profissional inspirado no Perssua do Lucas Montano.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QScrollArea, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OverlayConfig:
    """Configuração da UI overlay"""
    width: int = 450
    height: int = 350
    opacity: float = 0.92
    

class ModernOverlay(QWidget):
    """
    Overlay minimalista estilo Perssua.
    
    Design limpo, profissional, discreto.
    """
    
    def __init__(self, config: Optional[OverlayConfig] = None):
        super().__init__()
        
        self.config = config or OverlayConfig()
        self.drag_position = None
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        
        logger.info("Modern Overlay initialized")
    
    def _setup_window(self):
        """Configura janela."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Usar resize ao invés de setFixedSize
        self.resize(self.config.width, self.config.height)
        
        # Posição top-right
        screen = self.screen().geometry()
        self.move(screen.width() - self.config.width - 20, 20)
    
    def _setup_ui(self):
        """UI limpa e minimalista."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.setLayout(layout)
        
        # Header com botão de fechar
        header_layout = QHBoxLayout()
        
        self.header_label = QLabel("AI Copilot")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.header_label.setFont(QFont("Inter", 16, QFont.Weight.DemiBold))
        self.header_label.setStyleSheet("""
            color: #FFFFFF;
            padding: 8px 0px;
        """)
        header_layout.addWidget(self.header_label)
        
        # Botão de fechar
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Inter", 20))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 0.8);
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Status compact
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setFont(QFont("Inter", 10, QFont.Weight.Medium))
        self.status_label.setStyleSheet("""
            color: #4CAF50;
            background: rgba(76, 175, 80, 0.1);
            padding: 6px 12px;
            border-radius: 6px;
        """)
        layout.addWidget(self.status_label)
        
        # Transcription área com scroll
        self.transcription_label = QLabel("Speak to see transcription...")
        self.transcription_label.setWordWrap(True)
        self.transcription_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.transcription_label.setFont(QFont("Inter", 11))
        self.transcription_label.setStyleSheet("""
            color: #E0E0E0;
            background: rgba(40, 40, 40, 0.5);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(70, 70, 70, 0.3);
        """)
        
        # Scroll area para transcrição
        transcription_scroll = QScrollArea()
        transcription_scroll.setWidget(self.transcription_label)
        transcription_scroll.setWidgetResizable(True)
        transcription_scroll.setMaximumHeight(100)
        transcription_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(50, 50, 50, 0.3);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 0.5);
                border-radius: 4px;
            }
        """)
        layout.addWidget(transcription_scroll)
        
        # Suggestion área com scroll
        self.suggestion_label = QLabel("AI suggestions...")
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.suggestion_label.setFont(QFont("Inter", 10))
        self.suggestion_label.setStyleSheet("""
            color: #B0B0B0;
            background: rgba(30, 30, 30, 0.4);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(60, 60, 60, 0.3);
        """)
        
        # Scroll area para sugestão
        suggestion_scroll = QScrollArea()
        suggestion_scroll.setWidget(self.suggestion_label)
        suggestion_scroll.setWidgetResizable(True)
        suggestion_scroll.setMaximumHeight(120)
        suggestion_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(50, 50, 50, 0.3);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 100, 100, 0.5);
                border-radius: 4px;
            }
        """)
        layout.addWidget(suggestion_scroll)
        
        # Footer discreto
        footer = QLabel("Ctrl+Shift+P  •  Ctrl+Shift+S")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Inter", 8))
        footer.setStyleSheet("""
            color: rgba(150, 150, 150, 0.4);
            padding: 4px;
        """)
        layout.addWidget(footer)
        
        layout.addStretch()
    
    def _setup_animations(self):
        """Animações sutis."""
        self.transcription_fade = QGraphicsOpacityEffect()
        self.transcription_label.setGraphicsEffect(self.transcription_fade)
        
        self.transcription_anim = QPropertyAnimation(self.transcription_fade, b"opacity")
        self.transcription_anim.setDuration(250)
        self.transcription_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.suggestion_fade = QGraphicsOpacityEffect()
        self.suggestion_label.setGraphicsEffect(self.suggestion_fade)
        
        self.suggestion_anim = QPropertyAnimation(self.suggestion_fade, b"opacity")
        self.suggestion_anim.setDuration(300)
        self.suggestion_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def paintEvent(self, event):
        """Background limpo estilo Perssua."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background escuro sutil
        bg_color = QColor(18, 18, 18, int(255 * 0.92))
        
        painter.setBrush(bg_color)
        painter.setPen(QPen(QColor(45, 45, 45, 150), 1))
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        # Borda sutil
        painter.setPen(QPen(QColor(70, 70, 70, 100), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
    
    def set_transcription(self, text: str):
        """Atualiza transcrição."""
        self.transcription_anim.setStartValue(1.0)
        self.transcription_anim.setEndValue(0.4)
        self.transcription_anim.start()
        
        QTimer.singleShot(125, lambda: self._update_transcription_text(text))
    
    def _update_transcription_text(self, text: str):
        """Atualiza texto."""
        self.transcription_label.setText(text)
        self.transcription_anim.setStartValue(0.4)
        self.transcription_anim.setEndValue(1.0)
        self.transcription_anim.start()
    
    def set_suggestion(self, text: str):
        """Atualiza sugestão."""
        self.suggestion_anim.setStartValue(1.0)
        self.suggestion_anim.setEndValue(0.3)
        self.suggestion_anim.start()
        
        QTimer.singleShot(150, lambda: self._update_suggestion_text(text))
    
    def _update_suggestion_text(self, text: str):
        """Atualiza texto."""
        self.suggestion_label.setText(text)
        self.suggestion_anim.setStartValue(0.3)
        self.suggestion_anim.setEndValue(1.0)
        self.suggestion_anim.start()
    
    def set_status(self, status: str):
        """Atualiza status com cores Material Design."""
        self.status_label.setText(status)
        
        # Cores limpas
        if "Ready" in status or "🟢" in status:
            color, bg = "#4CAF50", "rgba(76, 175, 80, 0.1)"
        elif "Paused" in status or "⏸️" in status:
            color, bg = "#FF9800", "rgba(255, 152, 0, 0.1)"
        elif "Error" in status or "❌" in status:
            color, bg = "#F44336", "rgba(244, 67, 54, 0.1)"
        else:
            color, bg = "#2196F3", "rgba(33, 150, 243, 0.1)"
        
        self.status_label.setStyleSheet(f"""
            color: {color};
            background: {bg};
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None


# Compatibility alias
PrivateOverlay = ModernOverlay
