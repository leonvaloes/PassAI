# 🎙️ ASR Pipeline Component - Documentação

## ✅ Componente Implementado

Módulo completo de ASR (Speech-to-Text) com:
- ✅ Integração com OpenAI Whisper
- ✅ Suporte a múltiplos modelos (tiny, base, small, medium, large)
- ✅ Transcrição com timestamps
- ✅ Detecção automática de idioma
- ✅ Word-level timestamps
- ✅ Modo streaming
- ✅ Estatísticas de performance

---

## 📁 Arquivos Criados

- `src/processing/asr_pipeline.py` - Módulo principal (400+ linhas)
- `scripts/test_asr.py` - Teste completo com áudio ao vivo

---

## 🎯 Funcionalidades

### 1. ASRConfig
```python
@dataclass
class ASRConfig:
    model_size: str = "tiny"  # tiny, base, small, medium, large
    device: str = "cpu"  # cpu ou cuda
    language: Optional[str] = "pt"  # Idioma
    word_timestamps: bool = True  # Timestamps por palavra
```

### 2. ASRPipeline
- Transcrição completa de áudio
- Suporte a numpy arrays ou arquivos
- Normalização automática de áudio
- Resampling para 16kHz
- Estatísticas de performance (RTF - Real Time Factor)

### 3. StreamingASR
- Processa áudio em chunks
- Ideal para áudio contínuo
- Menor latência

---

## 📊 Modelos Disponíveis

| Modelo | Parâmetros | VRAM | Velocidade | Uso Recomendado |
|--------|-----------|------|------------|-----------------|
| **tiny** | 39M | ~1GB | ~32x | Testes rápidos |
| **base** | 74M | ~1GB | ~16x | Desenvolvimento |
| **small** | 244M | ~2GB | ~6x | Produção (boa qualidade) |
| **medium** | 769M | ~5GB | ~2x | Alta qualidade |
| **large** | 1550M | ~10GB | ~1x | Máxima qualidade |

**Para este projeto, use:**
- **Desenvolvimento**: `tiny` (rápido para testes)
- **Produção**: `small` ou `base` (bom equilíbrio)

---

## 🧪 Como Testar

### Teste Completo (Recomendado)
```powershell
venv\Scripts\python.exe scripts\test_asr.py
```

**Escolha opção 2** - Transcrição ao vivo

**O que vai acontecer:**
1. Carrega modelo Whisper (pode demorar 10-30s na primeira vez)
2. Inicia captura de áudio
3. Quando você **falar**, sistema:
   - Detecta fala (VAD)
   - Transcreve com Whisper
   - Mostra texto + estatísticas

**Exemplo de saída:**
```
============================================================
🎤 Transcription #1
============================================================

📝 Text: Olá, este é um teste do sistema de transcrição.
🌐 Language: pt
⏱️  Duration: 3.84s
⚡ Processing: 2.15s
📊 RTF: 0.56x

📍 Segments:
   [0.0s - 3.8s] Olá, este é um teste do sistema de transcrição.

============================================================
```

---

## 💻 Uso no Código

### Exemplo 1: Transcrição Básica
```python
from src.processing.asr_pipeline import ASRPipeline, ASRConfig

# Configurar ASR
config = ASRConfig(model_size="tiny", language="pt")
asr = ASRPipeline(config=config)

# Transcrever áudio (numpy array)
result = asr.transcribe(audio_array, sample_rate=16000)

# Resultado
print(result['text'])  # Texto transcrito
print(result['language'])  # Idioma detectado
print(result['processing_time'])  # Tempo de processamento
```

### Exemplo 2: Integração com Audio Capture
```python
from src.capture.audio_capture import AudioCapture
from src.processing.asr_pipeline import ASRPipeline, ASRConfig

# Setup ASR
asr = ASRPipeline(config=ASRConfig(model_size="tiny"))

def on_speech(audio, sample_rate):
    """Transcreve quando detecta fala."""
    result = asr.transcribe(audio, sample_rate)
    print(f"Você disse: {result['text']}")

# Captura com callback
capture = AudioCapture(callback=on_speech)
capture.start()
```

### Exemplo 3: Modo Streaming
```python
from src.processing.asr_pipeline import ASRPipeline, StreamingASR

asr = ASRPipeline()
streaming = StreamingASR(asr)

def on_speech(audio, sample_rate):
    result = streaming.process_chunk(audio, sample_rate)
    if result:
        print(result['text'])

capture = AudioCapture(callback=on_speech)
capture.start()
```

### Exemplo 4: Transcrever Arquivo
```python
from src.processing.asr_pipeline import ASRPipeline

asr = ASRPipeline()

# Transcrever arquivo de áudio
result = asr.transcribe_file("audio.wav")
print(result['text'])
```

---

## ⚙️ Configuração Avançada

### Alta Qualidade
```python
config = ASRConfig(
    model_size="small",  # Modelo melhor
    language="pt",
    word_timestamps=True,  # Timestamps detalhados
    beam_size=5,  # Beam search
    best_of=5  # Melhores candidatos
)
```

### Máxima Velocidade
```python
config = ASRConfig(
    model_size="tiny",  # Modelo mais rápido
    language="pt",  # Fixar idioma (mais rápido)
    word_timestamps=False,  # Desabilitar timestamps
    beam_size=1,  # Sem beam search
    best_of=1
)
```

### GPU (se disponível)
```python
config = ASRConfig(
    model_size="base",
    device="cuda",  # Usar GPU
    fp16=True  # Precisão reduzida (mais rápido)
)
```

---

## 📊 Performance Típica

**Com modelo `tiny` (CPU)**:
- Áudio de 3s → ~1-2s de processamento
- RTF: ~0.3-0.7x (mais rápido que tempo real)

**Com modelo `base` (CPU)**:
- Áudio de 3s → ~2-4s de processamento
- RTF: ~0.7-1.3x

**Com modelo `small` (GPU)**:
- Áudio de 3s → ~0.5-1s de processamento
- RTF: ~0.2-0.3x

**RTF (Real Time Factor)**:
- RTF < 1.0 = Mais rápido que tempo real ✅
- RTF = 1.0 = Mesmo tempo que áudio
- RTF > 1.0 = Mais lento que tempo real ⚠️

---

## 🔧 Troubleshooting

### Modelo demora para carregar
**Normal na primeira vez**:
- Whisper baixa modelos (~40MB-3GB dependendo do tamanho)
- Salvos em cache para próximas vezes
- Localização: `~/.cache/whisper/`

### Transcrição muito lenta
1. Use modelo menor (`tiny` ou `base`)
2. Fixe o idioma (`language="pt"`)
3. Desabilite word_timestamps
4. Use GPU se disponível

### Transcrição em branco ou incorreta
1. Verifique se áudio tem fala (não apenas ruído)
2. Áudio deve ter pelo menos 1s
3. Use modelo maior para melhor qualidade
4. Certifique-se que áudio está normalizado

### Out of Memory
1. Use modelo menor
2. Processe áudios menores (<30s)
3. Aumente RAM disponível

---

## 🎯 Integração com Componentes

### Audio Capture → ASR
```python
# Pipeline completo
asr = ASRPipeline(config=ASRConfig(model_size="tiny"))

def process_speech(audio, sr):
    transcription = asr.transcribe(audio, sr)
    return transcription['text']

capture = AudioCapture(callback=lambda a, sr: print(process_speech(a, sr)))
capture.start()
```

---

## 📝 Estatísticas

ASRPipeline mantém estatísticas automáticas:

```python
asr = ASRPipeline()

# Usar ASR...

stats = asr.get_stats()
print(f"Total de transcrições: {stats['total_transcriptions']}")
print(f"Tempo médio: {stats['avg_processing_time']:.2f}s")
print(f"RTF médio: {stats['avg_rtf']:.2f}x")

# Reset
asr.reset_stats()
```

---

## 🚀 Status dos Componentes

1. ✅ **Audio Capture** - Completo
2. ✅ **ASR Pipeline** - Completo
3. ⏸️ **Context Manager** - Próximo
4. ⏸️ **LLM Router** - Depois
5. ⏸️ **UI Overlay** - Depois

---

## 📊 Próximos Passos

Agora que temos **Audio Capture + ASR**, o próximo é:

**Context Manager** - Gerenciar histórico de conversação e contexto

Teste agora o ASR:
```powershell
venv\Scripts\python.exe scripts\test_asr.py
```

Escolha opção **2** e fale algo em português! 🎤
