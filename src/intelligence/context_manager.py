"""
Context Manager Component

Gerencia histórico de conversação, contexto de tela e estado do sistema.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Mensagem individual na conversação"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    speaker: str = "user"  # 'user' ou 'other'
    text: str = ""
    confidence: float = 1.0
    
    # Classificação
    intent: str = "neutral"  # question, objection, agreement, neutral
    objection_type: Optional[str] = None  # price, authority, trust, etc
    
    # Metadata
    duration: Optional[float] = None  # Duração do áudio (se aplicável)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Cria mensagem a partir de dicionário."""
        data = data.copy()
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ScreenContext:
    """Contexto da tela (OCR, slides, etc)"""
    timestamp: datetime = field(default_factory=datetime.now)
    extracted_text: str = ""
    slide_number: Optional[int] = None
    key_entities: List[str] = field(default_factory=list)
    visual_summary: str = ""
    content_hash: str = ""
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScreenContext':
        """Cria contexto a partir de dicionário."""
        data = data.copy()
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class UserProfile:
    """Perfil do usuário/sessão"""
    goal: str = "sales"  # sales, pitch, interview, meeting
    style: str = "confident"  # confident, technical, empathetic
    name: Optional[str] = None
    company: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return asdict(self)


class ConversationContext:
    """
    Gerencia contexto completo da conversação.
    
    Mantém:
    - Histórico de mensagens (sliding window)
    - Contexto de tela atual
    - Perfil do usuário
    - Objeções detectadas
    - Estatísticas
    
    Usage:
        context = ConversationContext(window_size=10)
        
        # Adicionar mensagem
        msg = Message(text="Quanto custa?", intent="question")
        context.add_message(msg)
        
        # Obter contexto para LLM
        llm_context = context.get_llm_context()
    """
    
    def __init__(
        self,
        window_size: int = 10,
        max_history_minutes: int = 60,
        user_profile: Optional[UserProfile] = None
    ):
        """
        Inicializa gerenciador de contexto.
        
        Args:
            window_size: Número de mensagens no sliding window
            max_history_minutes: Tempo máximo de histórico (minutos)
            user_profile: Perfil do usuário (cria padrão se None)
        """
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # Configurações
        self.window_size = window_size
        self.max_history_minutes = max_history_minutes
        
        # Estado
        self.user_profile = user_profile or UserProfile()
        self.messages: List[Message] = []
        self.screen_context: Optional[ScreenContext] = None
        self.objections: List[Message] = []
        
        # Estatísticas
        self.stats = {
            'total_messages': 0,
            'questions_detected': 0,
            'objections_detected': 0,
            'agreements_detected': 0
        }
        
        logger.info(
            f"Context Manager initialized (session: {self.session_id[:8]}..., "
            f"window: {window_size}, max_time: {max_history_minutes}min)"
        )
    
    def add_message(self, message: Message):
        """
        Adiciona mensagem ao histórico.
        
        Args:
            message: Mensagem a adicionar
        """
        self.messages.append(message)
        self.stats['total_messages'] += 1
        
        # Atualizar estatísticas
        if message.intent == 'question':
            self.stats['questions_detected'] += 1
        elif message.intent == 'objection':
            self.stats['objections_detected'] += 1
            self.objections.append(message)
        elif message.intent == 'agreement':
            self.stats['agreements_detected'] += 1
        
        # Limpar histórico antigo
        self._cleanup_old_messages()
        
        logger.debug(
            f"Message added: '{message.text[:50]}...' "
            f"(intent: {message.intent}, speaker: {message.speaker})"
        )
    
    def add_transcription(
        self,
        text: str,
        speaker: str = "user",
        confidence: float = 1.0,
        duration: Optional[float] = None
    ) -> Message:
        """
        Adiciona transcrição como mensagem.
        
        Args:
            text: Texto transcrito
            speaker: Quem falou ('user' ou 'other')
            confidence: Confiança da transcrição
            duration: Duração do áudio
            
        Returns:
            Mensagem criada
        """
        # Detectar intenção básica (pode ser melhorado com NLP)
        intent = self._detect_intent(text)
        
        message = Message(
            text=text,
            speaker=speaker,
            confidence=confidence,
            intent=intent,
            duration=duration
        )
        
        self.add_message(message)
        return message
    
    def update_screen_context(self, screen: ScreenContext):
        """
        Atualiza contexto da tela.
        
        Args:
            screen: Novo contexto de tela
        """
        self.screen_context = screen
        logger.debug(f"Screen context updated: '{screen.extracted_text[:50]}...'")
    
    def get_recent_messages(self, n: Optional[int] = None) -> List[Message]:
        """
        Retorna últimas N mensagens.
        
        Args:
            n: Número de mensagens (usa window_size se None)
            
        Returns:
            Lista de mensagens
        """
        if n is None:
            n = self.window_size
        return self.messages[-n:]
    
    def get_llm_context(self, include_screen: bool = True) -> Dict[str, Any]:
        """
        Prepara contexto para enviar ao LLM.
        
        Args:
            include_screen: Incluir contexto de tela
            
        Returns:
            Dicionário com contexto formatado
        """
        recent_messages = self.get_recent_messages()
        
        context = {
            'session_id': self.session_id,
            'user_profile': self.user_profile.to_dict(),
            'conversation_history': [
                {
                    'speaker': msg.speaker,
                    'text': msg.text,
                    'intent': msg.intent,
                    'timestamp': msg.timestamp.isoformat()
                }
                for msg in recent_messages
            ],
            'recent_objections': [
                {
                    'type': obj.objection_type,
                    'text': obj.text,
                    'timestamp': obj.timestamp.isoformat()
                }
                for obj in self.objections[-3:]  # Últimas 3 objeções
            ],
            'stats': self.stats.copy()
        }
        
        # Adicionar contexto de tela se disponível
        if include_screen and self.screen_context:
            context['current_screen'] = {
                'text': self.screen_context.extracted_text,
                'summary': self.screen_context.visual_summary,
                'slide_number': self.screen_context.slide_number
            }
        
        return context
    
    def get_conversation_summary(self) -> str:
        """
        Gera resumo da conversação.
        
        Returns:
            Texto com resumo
        """
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        
        summary = f"""
Sessão: {self.session_id[:8]}...
Duração: {duration:.1f} minutos
Total de mensagens: {len(self.messages)}
Perguntas: {self.stats['questions_detected']}
Objeções: {self.stats['objections_detected']}
Acordos: {self.stats['agreements_detected']}
        """.strip()
        
        return summary
    
    def export_session(self, filepath: str):
        """
        Exporta sessão para arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo
        """
        data = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'user_profile': self.user_profile.to_dict(),
            'messages': [msg.to_dict() for msg in self.messages],
            'objections': [obj.to_dict() for obj in self.objections],
            'stats': self.stats
        }
        
        if self.screen_context:
            data['screen_context'] = self.screen_context.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session exported to {filepath}")
    
    @classmethod
    def import_session(cls, filepath: str) -> 'ConversationContext':
        """
        Importa sessão de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            ConversationContext restaurado
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        context = cls()
        context.session_id = data['session_id']
        context.start_time = datetime.fromisoformat(data['start_time'])
        context.user_profile = UserProfile(**data['user_profile'])
        context.messages = [Message.from_dict(m) for m in data['messages']]
        context.objections = [Message.from_dict(o) for o in data['objections']]
        context.stats = data['stats']
        
        if 'screen_context' in data:
            context.screen_context = ScreenContext.from_dict(data['screen_context'])
        
        logger.info(f"Session imported from {filepath}")
        return context
    
    def _detect_intent(self, text: str) -> str:
        """
        Detecta intenção básica do texto.
        
        Implementação simples baseada em palavras-chave.
        Para produção, usar modelo NLP treinado.
        """
        text_lower = text.lower()
        
        # Perguntas
        question_words = ['como', 'qual', 'quando', 'onde', 'por que', 'quanto', 'quem']
        if any(word in text_lower for word in question_words) or '?' in text:
            return 'question'
        
        # Objeções (palavras-chave simples)
        objection_words = ['caro', 'preço', 'não posso', 'impossível', 'difícil']
        if any(word in text_lower for word in objection_words):
            return 'objection'
        
        # Acordo
        agreement_words = ['sim', 'ok', 'concordo', 'perfeito', 'ótimo', 'excelente']
        if any(word in text_lower for word in agreement_words):
            return 'agreement'
        
        return 'neutral'
    
    def _cleanup_old_messages(self):
        """Remove mensagens antigas baseado em tempo."""
        if not self.messages:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=self.max_history_minutes)
        
        # Filtrar mensagens recentes
        self.messages = [
            msg for msg in self.messages
            if msg.timestamp > cutoff_time
        ]
    
    def clear(self):
        """Limpa todo o contexto (mantém perfil)."""
        self.messages.clear()
        self.objections.clear()
        self.screen_context = None
        
        # Reset estatísticas
        for key in self.stats:
            self.stats[key] = 0
        
        logger.info("Context cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do contexto."""
        return {
            **self.stats,
            'total_messages_in_memory': len(self.messages),
            'session_duration_minutes': (
                (datetime.now() - self.start_time).total_seconds() / 60
            )
        }
