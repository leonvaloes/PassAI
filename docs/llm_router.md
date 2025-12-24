# 🤖 LLM Router Component - Documentação

## ✅ Componente Implementado

Sistema completo de roteamento de LLMs:
- ✅ Suporte a Ollama (local)
- ✅ Suporte a OpenAI (cloud)
- ✅ Fallback automático entre providers
- ✅ Prompts context-aware
- ✅ Diferentes estratégias por objetivo (sales, pitch, etc)
- ✅ Estatísticas e monitoramento

---

## 📁 Arquivos Criados

- `src/llm/router.py` - Router completo (500+ linhas)
- `scripts/test_llm.py` - Testes com modo interativo

---

## 🎯 Classes Principais

### 1. LLMProvider (Enum)
```python
class LLMProvider(Enum):
    OLLAMA = "ollama"      # Local (Ollama)
    OPENAI = "openai"      # Cloud (OpenAI)
    ANTHROPIC = "anthropic"  # TODO
```

### 2. LLMConfig
```python
@dataclass
class LLMConfig:
    default_provider: LLMProvider = OLLAMA
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Fallback
    enable_fallback: bool = True
    fallback_order: List[LLMProvider] = [OLLAMA, OPENAI]
```

### 3. LLMRouter
Router principal que:
- Gerencia múltiplos providers
- Fallback automático
- Constrói prompts context-aware
- Rastreia estatísticas

---

## 💻 Uso no Código

### Exemplo 1: Básico
```python
from src.llm.router import LLMRouter

# Criar router (padrão: Ollama)
router = LLMRouter()

# Gerar sugestão
result = router.generate_suggestion(
    conversation_history=[
        {"speaker": "user", "text": "Quanto custa?"}
    ],
    current_intent="question",
    user_goal="sales"
)

print(result['suggestion'])  # "I'd be happy to discuss pricing..."
```

### Exemplo 2: Com OpenAI
```python
from src.llm.router import LLMRouter, LLMConfig, LLMProvider

config = LLMConfig(
    default_provider=LLMProvider.OPENAI,
    openai_api_key="sk-..."
)

router = LLMRouter(config=config)
result = router.generate_suggestion(...)
```

### Exemplo 3: Fallback Automático
```python
config = LLMConfig(
    default_provider=LLMProvider.OLLAMA,
    enable_fallback=True,
    fallback_order=[LLMProvider.OLLAMA, LLMProvider.OPENAI]
)

router = LLMRouter(config=config)

# Tenta Ollama primeiro
# Se falhar, tenta OpenAI automaticamente
result = router.generate_suggestion(...)
```

### Exemplo 4: Integrado com Context Manager
```python
from src.intelligence.context_manager import ConversationContext
from src.llm.router import LLMRouter

context = ConversationContext()
router = LLMRouter()

# Adicionar mensagens ao contexto
context.add_transcription("O preço está muito alto")

# Obter contexto para LLM
llm_ctx = context.get_llm_context()

# Gerar sugestão
result = router.generate_suggestion(
    conversation_history=llm_ctx['conversation_history'],
    current_intent=llm_ctx['conversation_history'][-1]['intent'],
    user_goal=llm_ctx['user_profile']['goal']
)

print(result['suggestion'])
```

### Exemplo 5: Com Screen Context
```python
# Incluir contexto da tela (OCR, slide)
result = router.generate_suggestion(
    conversation_history=[...],
    current_intent="objection",
    user_goal="sales",
    screen_context="Current slide: ROI Calculator showing 300% return"
)
```

---

## 🧪 Como Testar

### Pré-requisito: Instalar Ollama

```powershell
# Instalar
winget install Ollama.Ollama

# Baixar modelo
ollama pull llama3.1:8b-instruct-q4_K_M

# Verificar
ollama list
```

### Testar LLM Router

```powershell
venv\Scripts\python.exe scripts\test_llm.py
```

**Escolha opção 2** - Simple suggestion

**O que vai acontecer:**
1. Router tenta conectar ao Ollama
2. Exemplo de conversação
3. Gera sugestão persuasiva
4. Mostra metadata (latência, tokens, etc)

**Exemplo de saída:**
```
💬 Conversation:
  👤 Olá, gostaria de saber mais sobre o produto.
  🤖 Claro! Nosso produto oferece...
  👤 Quanto custa?

🤔 Generating suggestion...

✅ Suggestion generated!

💡 SUGGESTION:
   Great question! Let me walk you through our pricing tiers 
   and show you the ROI you can expect in the first 3 months.

📊 Metadata:
   Provider: ollama
   Model: llama3.1:8b-instruct-q4_K_M
   Latency: 1.23s
   Tokens: 45
```

---

## 📊 System Prompts por Objetivo

### Sales
```
Focus on:
- Building trust and rapport
- Addressing objections with empathy
- Highlighting value and ROI
- Moving towards closing
Keep suggestions conversational and authentic.
```

### Pitch
```
Focus on:
- Clear value proposition
- Confidence and expertise
- Storytelling
- Call to action
Keep suggestions impactful and memorable.
```

---

## ⚙️ Configuração Avançada

### Apenas Local (Ollama)
```python
config = LLMConfig(
    default_provider=LLMProvider.OLLAMA,
    enable_fallback=False  # Sem fallback
)
```

### Apenas Cloud (OpenAI)
```python
import os

config = LLMConfig(
    default_provider=LLMProvider.OPENAI,
    openai_api_key=os.getenv('OPENAI_API_KEY'),
    openai_model="gpt-4",  # Modelo melhor
    openai_max_tokens=1000,  # Respostas mais longas
    openai_temperature=0.9  # Mais criativo
)
```

### Custom Fallback Order
```python
config = LLMConfig(
    fallback_order=[
        LLMProvider.OLLAMA,   # Tenta local primeiro
        LLMProvider.OPENAI    # Depois cloud
    ]
)
```

---

## 📈 Monitoramento

### Verificar Providers
```python
router = LLMRouter()
status = router.check_providers()

print(status)
# {'ollama': True, 'openai': False}
```

### Estatísticas
```python
stats = router.get_stats()

# Retorna:
{
    'total_requests': 10,
    'ollama_requests': 8,
    'openai_requests': 2,
    'fallbacks': 2,
    'errors': 0,
    'total_tokens': 450
}
```

---

## 🔧 Métodos Principais

| Método | Descrição |
|--------|-----------|
| `generate_suggestion()` | Gera sugestão baseada em contexto |
| `check_providers()` | Verifica status dos providers |
| `get_stats()` | Retorna estatísticas |
| `reset_stats()` | Reseta estatísticas |

---

## 🚀 Modelos Recomendados

### Ollama (Local)
```bash
# Desenvolvimento (rápido)
ollama pull llama3.1:8b-instruct-q4_K_M

# Produção (melhor qualidade)
ollama pull llama3.1:70b-instruct-q4_K_M

# Alternativa rápida
ollama pull phi3:medium
```

### OpenAI (Cloud)
- **Desenvolvimento**: `gpt-4o-mini` (barato, rápido)
- **Produção**: `gpt-4` (melhor qualidade)

---

## 💰 Custos Estimados

### Ollama (Local)
- **Custo**: R$ 0 (100% grátis)
- **Latência**: ~1-3s (CPU), ~0.5-1s (GPU)
- **Privacidade**: 100% local

### OpenAI (Cloud)
- **gpt-4o-mini**: ~$0.15/1M tokens input, ~$0.60/1M output
- **gpt-4**: ~$30/1M tokens input, ~$60/1M output
- **Latência**: ~1-2s
- **Exemplo**: 1000 sugestões/dia (~50 tokens cada) = ~$2-5/mês

---

## 🔒 Privacidade

### Ollama
- ✅ 100% local, nada sai da máquina
- ✅ Sem rastreamento
- ✅ Ideal para dados sensíveis

### OpenAI
- ⚠️ Dados enviados para cloud
- ⚠️ Siga política de privacidade da OpenAI
- ⚠️ Não envie dados confidenciais

---

## 🎯 Status dos Componentes

1. ✅ **Audio Capture** - Completo
2. ✅ **ASR Pipeline** - Completo
3. ✅ **Context Manager** - Completo
4. ✅ **LLM Router** - Completo
5. ⏸️ **UI Overlay** - Último!

---

## 📝 Próximos Passos

**Agora temos o CÉREBRO do sistema:**
- Audio → ASR → Context → **LLM** ✅

**Falta apenas:** UI Overlay (interface visual)

**Teste o LLM Router:**
```powershell
# 1. Instale Ollama
winget install Ollama.Ollama
ollama pull llama3.1:8b-instruct-q4_K_M

# 2. Teste
venv\Scripts\python.exe scripts\test_llm.py
```

Escolha **opção 2** ou **4** (modo interativo)! 🎉
