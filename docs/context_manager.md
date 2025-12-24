# 🧠 Context Manager Component - Documentação

## ✅ Componente Implementado

Sistema completo de gerenciamento de contexto:
- ✅ Histórico de mensagens com sliding window
- ✅ Detecção de intenção (question, objection, agreement)
- ✅ Contexto de tela (OCR, slides)
- ✅ Perfil do usuário
- ✅ Estatísticas de conversação
- ✅ Export/Import de sessões
- ✅ Preparação de contexto para LLM

---

## 📁 Arquivos Criados

- `src/intelligence/context_manager.py` - Módulo principal (450+ linhas)
- `scripts/test_integrated.py` - Teste do pipeline completo

---

## 🎯 Classes Principais

### 1. Message
```python
@dataclass
class Message:
    id: str  # UUID único
    timestamp: datetime
    speaker: str  # 'user' ou 'other'
    text: str
    confidence: float
    intent: str  # question, objection, agreement, neutral
    objection_type: Optional[str]
    duration: Optional[float]
```

### 2. ScreenContext
```python
@dataclass
class ScreenContext:
    timestamp: datetime
    extracted_text: str  # Texto do OCR
    slide_number: Optional[int]
    key_entities: List[str]
    visual_summary: str
    content_hash: str
```

### 3. UserProfile
```python
@dataclass
class UserProfile:
    goal: str  # sales, pitch, interview, meeting
    style: str  # confident, technical, empathetic
    name: Optional[str]
    company: Optional[str]
```

### 4. ConversationContext
Gerencia tudo:
- Sliding window de mensagens
- Detecção de intenção
- Cleanup automático
- Export/Import
- Estatísticas

---

## 💻 Uso no Código

### Exemplo 1: Básico
```python
from src.intelligence.context_manager import ConversationContext

# Criar contexto
context = ConversationContext(window_size=10)

# Adicionar mensagens
context.add_transcription("Quanto custa?", speaker="user")
context.add_transcription("R$ 1.000", speaker="other")

# Ver histórico
for msg in context.get_recent_messages():
    print(f"[{msg.speaker}] {msg.text}")
```

### Exemplo 2: Integrado com ASR
```python
from src.capture.audio_capture import AudioCapture
from src.processing.asr_pipeline import ASRPipeline
from src.intelligence.context_manager import ConversationContext

# Setup
context = ConversationContext()
asr = ASRPipeline()

def on_speech(audio, sr):
    # Transcrever
    result = asr.transcribe(audio, sr)
    
    # Adicionar ao contexto
    message = context.add_transcription(
        text=result['text'],
        speaker="user",
        duration=result['duration']
    )
    
    print(f"Intent detected: {message.intent}")

# Capturar
capture = AudioCapture(callback=on_speech)
capture.start()
```

### Exemplo 3: Contexto para LLM
```python
# Obter contexto formatado para enviar ao LLM
llm_context = context.get_llm_context()

# Exemplo de uso com LLM
prompt = f"""
User profile: {llm_context['user_profile']}

Recent conversation:
{llm_context['conversation_history']}

Detected objections:
{llm_context['recent_objections']}

Generate a persuasive response.
"""
```

### Exemplo 4: Screen Context
```python
from src.intelligence.context_manager import ScreenContext

# Criar contexto de tela (do OCR)
screen = ScreenContext(
    extracted_text="Product Features: A, B, C\nPrice: $1000",
    slide_number=5,
    key_entities=["Product", "Features", "Price"],
    visual_summary="Product presentation slide"
)

# Adicionar ao contexto
context.update_screen_context(screen)

# LLM terá acesso ao slide atual
llm_ctx = context.get_llm_context(include_screen=True)
```

### Exemplo 5: Export/Import
```python
# Exportar sessão
context.export_session("session_2024.json")

# Importar depois
context2 = ConversationContext.import_session("session_2024.json")
```

---

## 🧪 Como Testar

### Teste Completo Integrado (RECOMENDADO)
```powershell
venv\Scripts\python.exe scripts\test_integrated.py
```

**Escolha opção 2** - Pipeline completo

**O que vai acontecer:**
1. Inicializa Audio + ASR + Context
2. Você fala
3. Sistema:
   - Captura áudio
   - Transcreve
   - Detecta intenção
   - Adiciona ao contexto
   - Mostra histórico
   - Estatísticas

**Exemplo de saída:**
```
============================================================
🎤 Speech detected, processing...
============================================================

📝 Transcription: Quanto custa o produto?
🎯 Intent detected: question
⏱️  Processing: 1.23s

💬 Recent conversation (1 total):
  👤 Quanto custa o produto?

📊 Session stats:
  Questions: 1
  Objections: 0
  Agreements: 0
============================================================
```

---

## 📊 Detecção de Intenção

O sistema detecta automaticamente:

### Questions (Perguntas)
- Palavras-chave: como, qual, quando, onde, por que, quanto, quem
- Símbolo: `?`
- Exemplo: "Como funciona?", "Quanto custa?"

### Objections (Objeções)
- Palavras-chave: caro, preço, não posso, impossível, difícil
- Exemplo: "Está muito caro", "Não tenho certeza"

### Agreement (Acordo)
- Palavras-chave: sim, ok, concordo, perfeito, ótimo
- Exemplo: "Ok, concordo", "Perfeito!"

### Neutral
- Tudo que não se encaixa acima

**Para produção:** Substituir por modelo NLP treinado (BERT fine-tuned)

---

## 📈 Estatísticas Rastreadas

```python
stats = context.get_stats()

# Retorna:
{
    'total_messages': 10,
    'questions_detected': 3,
    'objections_detected': 2,
    'agreements_detected': 1,
    'total_messages_in_memory': 10,
    'session_duration_minutes': 5.5
}
```

---

## ⚙️ Configurações

### Sliding Window
```python
# Mantém últimas 10 mensagens
context = ConversationContext(window_size=10)

# Obter janela
recent = context.get_recent_messages()  # Últimas 10
recent_5 = context.get_recent_messages(5)  # Últimas 5
```

### Cleanup Automático
```python
# Remove mensagens com mais de 60 minutos
context = ConversationContext(max_history_minutes=60)
```

### Perfil Personalizado
```python
from src.intelligence.context_manager import UserProfile

profile = UserProfile(
    goal="sales",
    style="confident",
    name="João",
    company="Acme Corp"
)

context = ConversationContext(user_profile=profile)
```

---

## 🔧 Métodos Principais

| Método | Descrição |
|--------|-----------|
| `add_message()` | Adiciona mensagem manual |
| `add_transcription()` | Adiciona transcrição (detecta intenção) |
| `update_screen_context()` | Atualiza contexto de tela |
| `get_recent_messages()` | Retorna sliding window |
| `get_llm_context()` | Prepara contexto para LLM |
| `get_conversation_summary()` | Gera resumo da sessão |
| `export_session()` | Salva em JSON |
| `import_session()` | Carrega de JSON |
| `clear()` | Limpa contexto |
| `get_stats()` | Estatísticas |

---

## 📋 Formato de Contexto para LLM

```python
llm_context = {
    'session_id': '...',
    'user_profile': {
        'goal': 'sales',
        'style': 'confident'
    },
    'conversation_history': [
        {
            'speaker': 'user',
            'text': 'Quanto custa?',
            'intent': 'question',
            'timestamp': '2024-01-15T10:30:00'
        }
    ],
    'recent_objections': [
        {
            'type': 'price',
            'text': 'Muito caro',
            'timestamp': '...'
        }
    ],
    'current_screen': {
        'text': 'Slide text...',
        'summary': '...',
        'slide_number': 5
    },
    'stats': {...}
}
```

---

## 🚀 Status dos Componentes

1. ✅ **Audio Capture** - Completo
2. ✅ **ASR Pipeline** - Completo
3. ✅ **Context Manager** - Completo
4. ⏸️ **LLM Router** - Próximo (usar contexto para gerar sugestões)
5. ⏸️ **UI Overlay** - Depois

---

## 📝 Próximos Passos

Agora temos o **pipeline de entrada completo**:
- Audio → ASR → Context

**Próximo:** LLM Router
- Pegar contexto
- Enviar para LLM (Ollama/OpenAI)
- Gerar sugestão persuasiva

**Teste o pipeline integrado:**
```powershell
venv\Scripts\python.exe scripts\test_integrated.py
```

Escolha **opção 2** e veja tudo funcionando junto! 🎉
