# ⚠️ Nota sobre Dependências

## Problema com Compilação no Windows

Alguns pacotes Python requerem ferramentas de compilação (Rust, C++) que não estão disponíveis por padrão no Windows:

### Pacotes que requerem compilação:
- ❌ `transformers` → requer Rust (tokenizers)
- ❌ `anthropic` → requer Rust
- ❌ `webrtcvad` → requer C/C++
- ❌ `spacy` → requer C++
- ❌ `noisereduce` → requer compilação

### Soluções:

#### Opção 1: Usar `requirements.txt` Simplificado (Recomendado)
```bash
pip install -r requirements.txt
```

**O que funciona:**
- ✅ Faster Whisper (ASR)
- ✅ PyTorch
- ✅ OpenCV, Tesseract (Vision)
- ✅ OpenAI client
- ✅ PyQt6 (UI)
- ✅ Configuração e utils

**O que está desabilitado temporariamente:**
- ⏸️ Transformers (para objection detection)
- ⏸️ Anthropic client
- ⏸️ WebRTC VAD (pode usar alternativa Silero VAD)
- ⏸️ SpaCy NLP

#### Opção 2: Instalar Ferramentas de Compilação
```bash
# Instalar Rust
winget install Rustlang.Rustup

# Instalar Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# Depois instalar tudo
pip install -r requirements.txt
pip install -r requirements-full.txt
```

#### Opção 3: Usar Wheels Pré-compilados
```bash
# Site com wheels pré-compilados para Windows
# https://www.lfd.uci.edu/~gohlke/pythonlibs/

# Baixar e instalar manualmente
``` 

#### Opção 4: Usar WSL/Linux
```bash
# No WSL Ubuntu
sudo apt-get install python3-dev build-essential
pip install -r requirements.txt
pip install -r requirements-full.txt
```

## Funcionalidades Afetadas

### ✅ Funcionam sem compilação:
- Audio capture
- ASR (Whisper)
- Screen capture
- OCR
- LLM local (Ollama)
- LLM cloud (OpenAI)
- UI overlay

### ⚠️ Requerem compilação:
- Objection detection avançado (fine-tuned BERT)
  - **Alternativa**: Usar regexes + GPT para classificação
- WebRTC VAD
  - **Alternativa**: Usar Silero VAD (PyTorch-based)
- Anthropic Claude
  - **Alternativa**: Usar apenas OpenAI

## Roadmap

1. **MVP atual**: Funciona com `requirements.txt` simplificado
2. **Próximo**: Implementar alternativas sem compilação
   - Silero VAD em vez de WebRTC
   - LLM-based objection detection em vez de BERT
3. **Futuro**: Fornecer wheels pré-compilados

## Para Desenvolvedores

Se você tem um ambiente de desenvolvimento completo (com Rust e MSVC):

```bash
# Instalar tudo
pip install -r requirements.txt
pip install -r requirements-full.txt
pip install -r requirements-dev.txt
```

Isso permitirá usar todas as funcionalidades.
