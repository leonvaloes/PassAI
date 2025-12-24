"""
LLM Router Component

Roteamento inteligente entre LLMs locais (Ollama) e cloud (OpenAI/Anthropic).
Gera sugestões persuasivas baseadas no contexto da conversação.
"""

import os
import logging
import requests
import time
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Provedores de LLM disponíveis"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuração do LLM Router"""
    # Provider padrão
    default_provider: LLMProvider = LLMProvider.OLLAMA
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"  # Modelo que você tem instalado
    ollama_timeout: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 500
    openai_temperature: float = 0.7
    
    # Fallback
    enable_fallback: bool = True
    fallback_order: List[LLMProvider] = None
    
    # Geração
    max_retries: int = 3
    
    def __post_init__(self):
        if self.fallback_order is None:
            self.fallback_order = [
                LLMProvider.OLLAMA,
                LLMProvider.OPENAI
            ]
        
        # Carregar API keys de env se não fornecidas
        if not self.openai_api_key:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')


class LLMRouter:
    """
    Router para gerenciar múltiplos provedores de LLM.
    
    Tenta provider padrão, faz fallback se necessário.
    
    Usage:
        config = LLMConfig(default_provider=LLMProvider.OLLAMA)
        router = LLMRouter(config=config)
        
        suggestion = router.generate_suggestion(
            conversation_history=[...],
            current_intent="objection"
        )
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Inicializa LLM Router.
        
        Args:
            config: Configuração (usa padrão se None)
        """
        self.config = config or LLMConfig()
        
        # Clients
        self.ollama_client = None
        self.openai_client = None
        
        # Inicializar clients
        self._init_clients()
        
        # Estatísticas
        self.stats = {
            'total_requests': 0,
            'ollama_requests': 0,
            'openai_requests': 0,
            'fallbacks': 0,
            'errors': 0,
            'total_tokens': 0
        }
        
        logger.info(
            f"LLM Router initialized (default: {self.config.default_provider.value})"
        )
    
    def _init_clients(self):
        """Inicializa clients dos provedores."""
        # Ollama (sempre disponível - HTTP direto)
        try:
            # Testar conexão com Ollama
            response = requests.get(
                f"{self.config.ollama_base_url}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                logger.info("✅ Ollama available")
            else:
                logger.warning("⚠️ Ollama not responding correctly")
        except Exception as e:
            logger.warning(f"⚠️ Ollama not available: {e}")
        
        # OpenAI
        if self.config.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client error: {e}")
        else:
            logger.info("ℹ️ OpenAI API key not provided")
    
    def generate_suggestion(
        self,
        conversation_history: List[Dict],
        current_intent: str = "neutral",
        user_goal: str = "sales",
        screen_context: Optional[str] = None,
        provider: Optional[LLMProvider] = None
    ) -> Dict[str, Any]:
        """
        Gera sugestão persuasiva baseada no contexto.
        
        Args:
            conversation_history: Histórico de mensagens
            current_intent: Intenção da última mensagem (question, objection, etc)
            user_goal: Objetivo do usuário (sales, pitch, etc)
            screen_context: Contexto da tela (opcional)
            provider: Provider específico (usa padrão se None)
            
        Returns:
            Dict com:
                - suggestion: Texto da sugestão
                - provider: Provider usado
                - tokens: Tokens usados
                - latency: Tempo de resposta
        """
        self.stats['total_requests'] += 1
        
        # Determinar provider
        target_provider = provider or self.config.default_provider
        
        # Tentar gerar
        for attempt in range(self.config.max_retries):
            try:
                result = self._generate_with_provider(
                    provider=target_provider,
                    conversation_history=conversation_history,
                    current_intent=current_intent,
                    user_goal=user_goal,
                    screen_context=screen_context
                )
                
                return result
            
            except Exception as e:
                logger.error(
                    f"Error with {target_provider.value} (attempt {attempt + 1}): {e}"
                )
                
                # Tentar fallback
                if self.config.enable_fallback and attempt < self.config.max_retries - 1:
                    target_provider = self._get_fallback_provider(target_provider)
                    if target_provider:
                        self.stats['fallbacks'] += 1
                        logger.info(f"Falling back to {target_provider.value}")
                        continue
                
                # Último attempt falhou
                if attempt == self.config.max_retries - 1:
                    self.stats['errors'] += 1
                    raise
        
        raise RuntimeError("All providers failed")
    
    def _generate_with_provider(
        self,
        provider: LLMProvider,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str]
    ) -> Dict[str, Any]:
        """Gera com provider específico."""
        start_time = time.time()
        
        if provider == LLMProvider.OLLAMA:
            result = self._generate_ollama(
                conversation_history, current_intent, user_goal, screen_context
            )
        elif provider == LLMProvider.OPENAI:
            result = self._generate_openai(
                conversation_history, current_intent, user_goal, screen_context
            )
        else:
            raise ValueError(f"Provider not supported: {provider}")
        
        latency = time.time() - start_time
        
        # Adicionar metadata
        result['provider'] = provider.value
        result['latency'] = latency
        
        logger.info(
            f"Generated suggestion with {provider.value} "
            f"({latency:.2f}s, {result.get('tokens', 0)} tokens)"
        )
        
        return result
    
    def _generate_ollama(
        self,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str]
    ) -> Dict[str, Any]:
        """Gera com Ollama (local)."""
        # Construir messages no formato chat
        messages = self._build_messages(
            conversation_history, current_intent, user_goal, screen_context
        )
        
        # Fazer request usando /api/chat (nova API)
        response = requests.post(
            f"{self.config.ollama_base_url}/api/chat",
            json={
                "model": self.config.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 150  # Limitar tokens de resposta
                }
            },
            timeout=self.config.ollama_timeout
        )
        
        response.raise_for_status()
        data = response.json()
        
        self.stats['ollama_requests'] += 1
        
        # Extrair resposta do formato chat
        suggestion = data.get('message', {}).get('content', '').strip()
        
        return {
            'suggestion': suggestion,
            'tokens': data.get('eval_count', 0),
            'model': self.config.ollama_model
        }
    
    def _generate_openai(
        self,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str]
    ) -> Dict[str, Any]:
        """Gera com OpenAI (cloud)."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Construir messages
        messages = self._build_messages(
            conversation_history, current_intent, user_goal, screen_context
        )
        
        # Fazer request
        response = self.openai_client.chat.completions.create(
            model=self.config.openai_model,
            messages=messages,
            max_tokens=self.config.openai_max_tokens,
            temperature=self.config.openai_temperature
        )
        
        self.stats['openai_requests'] += 1
        self.stats['total_tokens'] += response.usage.total_tokens
        
        return {
            'suggestion': response.choices[0].message.content.strip(),
            'tokens': response.usage.total_tokens,
            'model': self.config.openai_model
        }
    
    def _build_prompt(
        self,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str]
    ) -> str:
        """Constrói prompt para modelos que não usam chat format."""
        # System prompt
        system = self._get_system_prompt(user_goal)
        
        # Histórico
        history = "\n".join([
            f"{msg['speaker'].upper()}: {msg['text']}"
            for msg in conversation_history[-5:]  # Últimas 5 mensagens
        ])
        
        # Contexto de tela
        screen = f"\n\nCURRENT SCREEN:\n{screen_context}" if screen_context else ""
        
        # Intent
        intent_note = f"\n\nCURRENT INTENT: {current_intent}"
        
        prompt = f"""{system}

CONVERSATION:
{history}{screen}{intent_note}

Generate a brief, persuasive suggestion (1-2 sentences) for what the user should say next:"""
        
        return prompt
    
    def _build_messages(
        self,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str]
    ) -> List[Dict[str, str]]:
        """Constrói messages para chat models (OpenAI)."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(user_goal)
            }
        ]
        
        # Adicionar histórico
        for msg in conversation_history[-5:]:
            role = "user" if msg['speaker'] == 'user' else "assistant"
            messages.append({
                "role": role,
                "content": msg['text']
            })
        
        # User message final pedindo sugestão
        user_msg = f"Current intent: {current_intent}."
        if screen_context:
            user_msg += f"\n\nScreen context: {screen_context}"
        user_msg += "\n\nGenerate a brief persuasive suggestion (1-2 sentences) for what I should say next."
        
        messages.append({
            "role": "user",
            "content": user_msg
        })
        
        return messages
    
    def _get_system_prompt(self, user_goal: str) -> str:
        """Retorna system prompt baseado no objetivo."""
        base = """You are an AI sales coach helping in real-time during a conversation.
Your role is to suggest persuasive, natural responses based on the conversation context."""
        
        if user_goal == "sales":
            return base + """
Focus on:
- Building trust and rapport
- Addressing objections with empathy
- Highlighting value and ROI
- Moving towards closing
Keep suggestions conversational and authentic."""
        
        elif user_goal == "pitch":
            return base + """
Focus on:
- Clear value proposition
- Confidence and expertise
- Storytelling
- Call to action
Keep suggestions impactful and memorable."""
        
        else:
            return base + " Keep suggestions helpful and natural."
    
    def _get_fallback_provider(
        self,
        failed_provider: LLMProvider
    ) -> Optional[LLMProvider]:
        """Retorna próximo provider no fallback order."""
        try:
            current_idx = self.config.fallback_order.index(failed_provider)
            if current_idx + 1 < len(self.config.fallback_order):
                return self.config.fallback_order[current_idx + 1]
        except ValueError:
            pass
        
        return None
    
    def check_providers(self) -> Dict[str, bool]:
        """Verifica disponibilidade dos providers."""
        status = {}
        
        # Ollama
        try:
            response = requests.get(
                f"{self.config.ollama_base_url}/api/tags",
                timeout=2
            )
            status['ollama'] = response.status_code == 200
        except:
            status['ollama'] = False
        
        # OpenAI
        status['openai'] = self.openai_client is not None
        
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reseta estatísticas."""
        for key in self.stats:
            self.stats[key] = 0
