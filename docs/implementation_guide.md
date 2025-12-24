# Guia de Implementação e Deployment

## 1. ROADMAP DE DESENVOLVIMENTO

### 1.1 Fase 1: Proof of Concept (4-6 semanas)

**Objetivo**: Validar viabilidade técnica dos componentes críticos.

#### Semana 1-2: Foundation
- [ ] Setup ambiente de desenvolvimento
  - Python 3.11+ venv
  - CUDA toolkit (se GPU)
  - Ollama instalado e configurado
- [ ] Audio Pipeline MVP
  - Captura de microfone com `sounddevice`
  - VAD básico (WebRTC)
  - Teste de latência <100ms
- [ ] ASR Integration
  - Faster Whisper instalado
  - Testes de precisão em português
  - Benchmark de latência (target: <500ms)

**Deliverable**: Script que transcreve áudio do microfone em tempo real.

#### Semana 3-4: Intelligence Layer
- [ ] Objection Detection MVP
  - Regex patterns básicos
  - Teste com dataset sintético
- [ ] LLM Router
  - Integração Ollama
  - Prompts iniciais
  - Teste local vs API
- [ ] Context Manager
  - Estrutura de dados
  - Sliding window

**Deliverable**: Sistema que detecta objeção e gera sugestão via LLM.

#### Semana 5-6: UI & Integration
- [ ] Overlay UI (Electron ou PyQt)
  - Layout básico
  - Exclusão de screen capture
  - Hotkeys
- [ ] Integration
  - Pipeline end-to-end
  - Testes de latência total
  - Ajustes de performance

**Deliverable**: Demo funcional que pode ser testado em reunião real.

---

### 1.2 Fase 2: MVP Production-Ready (8-10 semanas)

#### Componentes
- [ ] Screen Capture + OCR
  - DXGI integration (Windows)
  - Tesseract OCR
  - Change detection
- [ ] Advanced Objection Classifier
  - Fine-tune DistilBERT
  - Dataset de vendas (1000+ exemplos)
  - Accuracy >85%
- [ ] Persuasion Engine
  - Estratégias mapeadas
  - Prompt engineering refinado
  - A/B testing de respostas
- [ ] Privacy Features
  - Encryption opt-in
  - Session management
  - GDPR compliance
- [ ] Packaging & Installation
  - PyInstaller build
  - Instalador Windows
  - Auto-update

**Deliverable**: Aplicação instalável, pronta para testes de usuário.

---

### 1.3 Fase 3: Enterprise Features (12+ semanas)

- [ ] Multi-language support
- [ ] Speaker diarization
- [ ] VLM integration (GPT-4V)
- [ ] CRM integration
- [ ] Team analytics
- [ ] Admin dashboard

---

## 2. STACK TECNOLÓGICO - DECISÕES

### 2.1 Core Backend

**Linguagem**: Python 3.11+
- **Justificativa**: 
  - Ecossistema ML rico (transformers, whisper)
  - Rápido desenvolvimento
  - Asyncio para concorrência
- **Trade-offs**:
  - Performance inferior a Rust/C++
  - GIL pode ser limitante (mitigado com multiprocessing)

**Alternativa considerada**: Rust
- **Prós**: Performance, memory safety
- **Contras**: Ecosistema ML menos maduro, curva de aprendizado

**Decisão**: Python para MVP, migrar componentes críticos para Rust se necessário.

---

### 2.2 ASR Engine

**Escolha**: Faster Whisper
- **Justificativa**:
  - Código aberto
  - Offline (privacidade)
  - Boa precisão em português
  - CTranslate2 = 2-4x speedup vs Whisper base
- **Trade-offs**:
  - Latência ~300-800ms (vs Deepgram ~100ms)
  - Requer GPU para performance ideal

**Fallback**: Deepgram API
- Para casos onde latência <200ms é crítica
- Custo: ~$0.0125/min

**Configuração Recomendada**:
```yaml
asr:
  engine: faster-whisper
  model: large-v3
  device: cuda
  compute_type: int8  # Quantizado
  beam_size: 5
  language: pt
  vad_filter: true
```

---

### 2.3 LLM Selection

| Modelo | Uso Recomendado | RAM | Latência (RTX 3060) | Qualidade |
|--------|-----------------|-----|---------------------|-----------|
| **Phi-3-mini-4k** | Ultra-low latency | 4GB | ~100ms | 7/10 |
| **Llama-3.2-3B** | Budget-friendly | 4GB | ~120ms | 7.5/10 |
| **Mistral-7B-Instruct** | Balanced | 8GB | ~300ms | 9/10 |
| **Llama-3.1-8B** | Best quality (local) | 10GB | ~350ms | 9.5/10 |
| **GPT-4o-mini** | Cloud fallback | - | ~800ms | 9.5/10 |

**Decisão Recomendada**:
- **Padrão**: Llama-3.1-8B (Q4_K_M)
- **Low-end hardware**: Phi-3-mini
- **Fallback**: GPT-4o-mini (Anthropic Claude-3-haiku como alternativa)

**Teste de Latência**:
```bash
# Ollama
time ollama run llama3.1:8b-instruct-q4_K_M "Respond to: 'Too expensive'"

# Esperado: 200-400ms em GPU moderna
```

---

### 2.4 UI Framework

**Opções**:

1. **Electron** (escolha recomendada)
   - **Prós**:
     - Cross-platform
     - Web stack familiar (HTML/CSS/JS)
     - `setContentProtection()` para privacidade
   - **Contras**:
     - Tamanho do bundle (~150MB)
     - Maior consumo de RAM (~100MB)

2. **PyQt6/PySide6**
   - **Prós**:
     - Nativo, mais leve
     - Melhor performance
   - **Contras**:
     - Curva de aprendizado
     - UI menos moderna (sem CSS fácil)

3. **WPF** (Windows-only)
   - **Prós**:
     - Melhor integração Windows
     - Exclusão de captura mais confiável
   - **Contras**:
     - Requer C#, não cross-platform

**Decisão**: Electron para MVP (web stack), migrar para Qt se performance for crítica.

---

## 3. DEPLOYMENT

### 3.1 Packaging (Windows)

**PyInstaller** (backend):
```bash
pyinstaller \
  --onefile \
  --windowed \
  --name AICoilot \
  --icon assets/icon.ico \
  --add-data "models:models" \
  --add-data "config:config" \
  --add-binary "C:/Program Files/Tesseract-OCR/tesseract.exe:tesseract" \
  --hidden-import=faster_whisper \
  --hidden-import=transformers \
  main.py
```

**Electron Builder** (frontend):
```json
{
  "build": {
    "appId": "com.aicopilot.app",
    "productName": "AI Copilot",
    "win": {
      "target": ["nsis"],
      "icon": "assets/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true
    }
  }
}
```

**Tamanho Final Estimado**:
- Backend Python: ~500MB (com models)
- Electron UI: ~150MB
- **Total**: ~650MB

**Otimizações**:
- Modelos quantizados (Q4 em vez de FP16): -70% tamanho
- Download de modelos sob demanda: -400MB inicial
- NSIS compression: -20%

---

### 3.2 Installation Flow

```
1. Installer executa
   ↓
2. Verifica requisitos
   - Windows 10+ (build 1903+)
   - 8GB RAM mínimo
   - (Opcional) NVIDIA GPU
   ↓
3. Instala componentes
   - Aplicação principal
   - Tesseract OCR
   - Visual C++ Redistributable
   ↓
4. Download de modelos (opcional)
   - Whisper large-v3
   - Llama-3.1-8B
   ↓
5. Configuração inicial
   - Selecionar microfone
   - Calibrar ruído de fundo
   - Escolher LLM (local/cloud)
   - API keys (se cloud)
   ↓
6. Setup completo
```

---

### 3.3 System Requirements

**Mínimo**:
- Windows 10 (build 1903+)
- CPU: Intel i5 8ª geração ou AMD Ryzen 5
- RAM: 8GB
- Disco: 5GB disponível
- Microfone

**Recomendado**:
- Windows 11
- CPU: Intel i7 10ª geração ou AMD Ryzen 7
- RAM: 16GB
- GPU: NVIDIA RTX 3060 ou superior (6GB VRAM)
- Disco: 10GB SSD
- Headset com microfone de qualidade

**Performance Esperada**:

| Config | ASR Latency | LLM Latency | Total |
|--------|-------------|-------------|-------|
| Mínimo (CPU-only) | 1-2s | 3-5s | 4-7s |
| Recomendado (GPU) | 300-500ms | 200-400ms | <1s |

---

## 4. PERFORMANCE OPTIMIZATION

### 4.1 Profiling

**Identificar Bottlenecks**:
```python
import cProfile
import pstats
from pstats import SortKey

profiler = cProfile.Profile()
profiler.enable()

# Executar pipeline completo
run_full_pipeline()

profiler.disable()

# Análise
stats = pstats.Stats(profiler)
stats.sort_stats(SortKey.CUMULATIVE)
stats.print_stats(20)
```

**Métricas Esperadas**:
- Audio capture: <5% CPU
- ASR (GPU): 40-60% GPU, 10-15% CPU
- LLM (GPU): 60-90% GPU, 5-10% CPU
- OCR: 10-20% CPU (intermitente)
- UI: <5% CPU

---

### 4.2 Otimizações Específicas

#### A. Audio Pipeline
```python
# Usar thread nativa (sem GIL)
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

def audio_callback(indata, frames, time, status):
    # Processar em thread separada
    executor.submit(process_audio, indata.copy())
```

#### B. ASR Batching
```python
# Processar múltiplos chunks em batch (se aplicável)
class BatchedASR:
    def __init__(self, batch_size=4):
        self.batch_size = batch_size
        self.queue = []
    
    def add(self, audio):
        self.queue.append(audio)
        
        if len(self.queue) >= self.batch_size:
            return self.process_batch()
    
    def process_batch(self):
        # Faster Whisper não suporta batch nativamente
        # mas podemos processar em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(asr.transcribe, self.queue)
        
        self.queue.clear()
        return list(results)
```

#### C. LLM Inference
```python
# Pre-warming (evitar cold start)
def warmup_llm():
    """Executa inferência dummy para carregar modelo."""
    router.generate("hello", max_tokens=10)

warmup_llm()  # No startup
```

#### D. Caching
```python
from functools import lru_cache
import hashlib

class ResponseCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    
    def get_or_generate(self, context_hash, generator_fn):
        if context_hash in self.cache:
            return self.cache[context_hash]
        
        response = generator_fn()
        
        if len(self.cache) >= self.max_size:
            # Remove oldest
            self.cache.pop(next(iter(self.cache)))
        
        self.cache[context_hash] = response
        return response

# Uso
cache = ResponseCache()

def generate_response(objection):
    ctx_hash = hashlib.md5(objection.encode()).hexdigest()
    return cache.get_or_generate(
        ctx_hash,
        lambda: llm_router.generate(objection)
    )
```

---

### 4.3 Memory Management

**Problemas Comuns**:
- Modelos ML consomem muita RAM/VRAM
- Histórico conversacional cresce indefinidamente
- Screenshots não são liberados

**Soluções**:
```python
import gc

class MemoryManager:
    def __init__(self, max_history_mb=500):
        self.max_history_mb = max_history_mb
    
    def cleanup_old_data(self, context):
        """Remove dados antigos."""
        # Limitar mensagens
        if len(context.messages) > 100:
            context.messages = context.messages[-50:]
        
        # Limitar screenshots em memória
        if hasattr(context, 'screen_history'):
            context.screen_history = context.screen_history[-5:]
        
        # Forçar garbage collection
        gc.collect()
    
    def check_memory_usage(self):
        """Monitora uso de memória."""
        import psutil
        
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        
        if mem_mb > self.max_history_mb:
            print(f"Memory high: {mem_mb:.0f}MB, cleaning up...")
            gc.collect()
            
            # Se GPU, limpar cache CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

# Executar periodicamente
import threading

def memory_monitor():
    manager = MemoryManager()
    while True:
        manager.check_memory_usage()
        time.sleep(30)

threading.Thread(target=memory_monitor, daemon=True).start()
```

---

## 5. TESTING

### 5.1 Unit Tests

```python
# tests/test_objection_detector.py
import pytest
from src.intelligence.objection_detector import ObjectionDetector

@pytest.fixture
def detector():
    return ObjectionDetector()

def test_price_objection(detector):
    result = detector.classify("Isso está muito caro")
    assert result.type == "price"
    assert result.confidence > 0.7

def test_authority_objection(detector):
    result = detector.classify("Preciso falar com meu gerente")
    assert result.type == "authority"

def test_no_objection(detector):
    result = detector.classify("Entendi, obrigado")
    assert result.type == "none"

# Executar
# pytest tests/ -v
```

### 5.2 Integration Tests

```python
# tests/test_pipeline.py
import pytest
import asyncio
from src.main import MainPipeline

@pytest.mark.asyncio
async def test_end_to_end():
    pipeline = MainPipeline()
    
    # Simular áudio
    audio = load_test_audio("tests/fixtures/price_objection.wav")
    
    # Processar
    result = await pipeline.process(audio)
    
    # Validar
    assert result['transcription'] is not None
    assert result['objection_detected'] == True
    assert result['objection_type'] == 'price'
    assert len(result['suggestion']) > 0
    assert result['latency_ms'] < 2000

@pytest.mark.asyncio
async def test_screen_integration():
    pipeline = MainPipeline()
    
    # Simular screenshot
    screenshot = load_test_image("tests/fixtures/slide.png")
    
    result = await pipeline.process_screen(screenshot)
    
    assert 'extracted_text' in result
    assert len(result['extracted_text']) > 0
```

### 5.3 Performance Benchmarks

```python
# tests/benchmark.py
import time
import numpy as np

def benchmark_component(component, test_fn, n_runs=100):
    latencies = []
    
    for _ in range(n_runs):
        start = time.time()
        test_fn(component)
        latencies.append((time.time() - start) * 1000)
    
    return {
        'mean': np.mean(latencies),
        'p50': np.percentile(latencies, 50),
        'p95': np.percentile(latencies, 95),
        'p99': np.percentile(latencies, 99)
    }

# Benchmark ASR
asr = ASRPipeline()
audio = load_test_audio()

stats = benchmark_component(
    asr,
    lambda asr: asr.transcribe(audio),
    n_runs=50
)

print(f"ASR Latency:")
print(f"  Mean: {stats['mean']:.0f}ms")
print(f"  P95: {stats['p95']:.0f}ms")
```

### 5.4 User Acceptance Testing

**Protocolo**:
1. Recrutar 10 usuários (sales, customer success)
2. Setup: Reunião simulada de 30min
3. Metrics:
   - Objeções detectadas corretamente (recall)
   - Sugestões relevantes (avaliação 1-5)
   - Latência percebida (<1s = bom)
   - Usabilidade geral (SUS score)

**Critérios de Sucesso**:
- Recall de objeções >80%
- Relevância média >3.5/5
- Latência p95 <1.5s
- SUS score >70

---

## 6. CHALLENGES & SOLUTIONS

### 6.1 Latência Excessiva

**Problema**: Pipeline total >2s

**Diagnóstico**:
```python
import time

class LatencyTracker:
    def __init__(self):
        self.timings = {}
    
    def measure(self, component):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                
                if component not in self.timings:
                    self.timings[component] = []
                self.timings[component].append(elapsed)
                
                return result
            return wrapper
        return decorator
    
    def report(self):
        for component, timings in self.timings.items():
            print(f"{component}: {np.mean(timings):.0f}ms")

tracker = LatencyTracker()

@tracker.measure("asr")
def transcribe(audio):
    return asr.transcribe(audio)
```

**Soluções**:
1. **ASR lento**: Usar modelo menor (medium vs large)
2. **LLM lento**: Quantização Q4, modelo menor (3B vs 8B)
3. **OCR lento**: Cache, processamento incremental
4. **Network lento** (cloud LLM): Timeout menor, fallback rápido

---

### 6.2 Falsos Positivos (Detecção de Objeções)

**Problema**: Sistema detecta objeção onde não há

**Exemplos**:
- "Não tenho dúvidas" → classificado como objeção
- "Preço está ok" → classificado como objeção de preço

**Soluções**:
1. **Fine-tune melhor**: Dataset balanceado (50% objeções, 50% não-objeções)
2. **Threshold de confiança**: Só alertar se confidence >0.7
3. **Context-aware**: Verificar sentimento geral (positivo vs negativo)

```python
class SmartObjectionDetector:
    def __init__(self):
        self.classifier = load_objection_model()
        self.sentiment_analyzer = load_sentiment_model()
    
    def detect(self, text):
        # Classificação de objeção
        obj_result = self.classifier(text)
        
        # Análise de sentimento
        sentiment = self.sentiment_analyzer(text)
        
        # Se sentimento positivo, reduzir confiança
        if sentiment['label'] == 'positive' and obj_result.confidence < 0.9:
            obj_result.confidence *= 0.5
        
        return obj_result
```

---

### 6.3 Hardware Insuficiente (Sem GPU)

**Problema**: Usuário não tem GPU, latência >5s

**Soluções**:
1. **CPU-optimized models**:
   - Phi-3-mini (3.8B)
   - Quantização Q4
   - ONNX Runtime (2x speedup em CPU)
   
2. **Cloud fallback automático**:
```python
class AdaptiveLLMRouter:
    def __init__(self):
        self.hardware = detect_hardware()
        
        if self.hardware == 'cpu':
            # Forçar cloud
            self.default_provider = 'cloud'
        else:
            self.default_provider = 'local'
```

3. **Cached responses**:
   - Objeções comuns → respostas pré-geradas
   - Semantic search (embeddings) para retrieval

---

### 6.4 Privacidade (Screen Capture Visível)

**Problema**: Em alguns setups, overlay aparece em screen sharing

**Diagnóstico**:
```python
def test_capture_visibility():
    """Teste se overlay é capturado."""
    # 1. Abrir overlay
    # 2. Iniciar screen sharing (Zoom/OBS)
    # 3. Capturar tela via OBS
    # 4. Verificar se overlay aparece
    
    # Se sim, configuração incorreta
```

**Soluções**:
1. **Windows**: `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`
2. **Electron**: `win.setContentProtection(true)`
3. **Fallback**: Minimizar overlay durante screen sharing (auto-detect)

---

### 6.5 Eco/Ruído em Reuniões

**Problema**: ASR transcreve áudio de outros participantes

**Soluções**:
1. **Seleção correta de dispositivo**: Apenas microfone, nunca "Stereo Mix"
2. **VAD rigoroso**: Mode 3 (mais agressivo)
3. **Noise suppression**: RNNoise
4. **Sugerir headset**: Melhor isolamento

---

## 7. MAINTENANCE & UPDATES

### 7.1 Model Updates

**Whisper**:
- Verificar novas versões: https://github.com/openai/whisper
- Testar accuracy em dataset de validação
- Deploy gradual (A/B test)

**LLMs**:
- Ollama: `ollama pull <new_model>`
- Auto-update opcional (usuário decide)

### 7.2 Monitoring

**Métricas a Coletar** (opt-in):
```python
class TelemetryCollector:
    def log_event(self, event_type, data):
        # Local logging (não enviar para servidor)
        with open('telemetry.log', 'a') as f:
            f.write(json.dumps({
                'timestamp': time.time(),
                'event': event_type,
                'data': data
            }) + '\n')

# Eventos
telemetry.log_event('objection_detected', {
    'type': 'price',
    'confidence': 0.87,
    'latency_ms': 450
})

telemetry.log_event('suggestion_shown', {
    'text_length': 120,
    'user_accepted': True  # Se usuário clicou
})
```

**Análise**:
- Latência média/p95
- Taxa de detecção de objeções
- Taxa de aceitação de sugestões
- Crashes/erros

---

## 8. CONCLUSÃO E RECOMENDAÇÕES

### 8.1 Prioridades de Implementação

**Alta Prioridade** (MVP):
1. Audio capture + ASR (Faster Whisper)
2. Objection detection (regex + simple classifier)
3. LLM router (Ollama + OpenAI fallback)
4. Basic overlay UI
5. End-to-end integration

**Média Prioridade** (V1):
6. Screen capture + OCR
7. Advanced objection classifier (fine-tuned)
8. Privacy features
9. Packaging & installer

**Baixa Prioridade** (V2+):
10. Speaker diarization
11. VLM integration
12. CRM integration

---

### 8.2 Risk Mitigation

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Latência alta | Média | Alto | LLM menor, GPU recomendado, cloud fallback |
| Falsos positivos | Alta | Médio | Fine-tuning, threshold ajustável |
| Privacidade | Baixa | Crítico | Exclusão de captura, encryption, opt-in |
| Hardware insuficiente | Média | Médio | Cloud fallback, modelos CPU-optimized |

---

### 8.3 Success Metrics

**Técnicas**:
- Latência p95 <1s
- Recall de objeções >80%
- Precision >75%
- Crash rate <1%

**Usuário**:
- NPS >50
- Uso semanal >3x
- Conversão (trial→paid) >20%

---

### 8.4 Próximos Passos Imediatos

1. **Setup ambiente**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install faster-whisper transformers sounddevice webrtcvad
   ```

2. **Instalar Ollama**:
   ```bash
   # Windows
   winget install Ollama.Ollama
   ollama pull llama3.1:8b-instruct-q4_K_M
   ```

3. **POC de Audio→ASR**:
   ```python
   # test_audio_asr.py
   from audio_capture import AudioCapture
   from asr_pipeline import ASRPipeline
   
   asr = ASRPipeline()
   
   def on_speech(audio, sr):
       result = asr.transcribe(audio, sr)
       print(f"[{result['latency_ms']:.0f}ms] {result['text']}")
   
   capture = AudioCapture(callback=on_speech)
   capture.start()
   
   print("Speak now...")
   input("Press Enter to stop")
   ```

4. **Validar latência**:
   - Target: <500ms em GPU
   - Aceitável: <1s em GPU, <3s em CPU

5. **Iterar**:
   - Se latência ok → adicionar LLM
   - Se latência alta → trocar modelo/hardware

---

**Este guia fornece um caminho claro de implementação, com foco em:**
- Viabilidade técnica
- Performance real
- Deployment prático
- Manutenibilidade

**Documentação técnica completa, pronta para desenvolvimento.**
