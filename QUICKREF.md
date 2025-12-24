# ✅ GUIA RÁPIDO - Como Testar e Rodar

## 🚀 Forma Mais Simples (1 comando)

### Opção 1: Usar script automático
```powershell
.\run.bat
```
Isso vai iniciar o AI Copilot automaticamente!

### Opção 2: Verificar componentes
```powershell
.\verify.bat
```
Mostra status de todos os componentes instalados.

---

## 📋 Comandos Manuais

### Executar Aplicação Principal
```powershell
venv\Scripts\python.exe src\main.py
```

**Para parar**: `Ctrl+C`

### Verificar PyTorch
```powershell
venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

**Saída esperada:**
```
PyTorch: 2.9.1+cpu
CUDA: False  # Normal se não tiver GPU NVIDIA
```

### Listar Dispositivos de Áudio
```powershell
venv\Scripts\python.exe -c "import sounddevice; print(sounddevice.query_devices())"
```

---

## ✅ Status Atual

**Componentes Verificados:**
- ✅ whisper (ASR)
- ✅ torch (PyTorch 2.9.1+cpu)
- ✅ openai (API client)
- ✅ PyQt6 (UI)
- ✅ cv2 (OpenCV)
- ✅ sounddevice (Audio)
- ✅ yaml (Config)
- ✅ pydantic (Validation)
- ✅ mss (Screen capture)

**Status**: Tudo funcionando! 🎉

---

## 🧪 Testes Rápidos

### 1. Teste de Configuração
```powershell
venv\Scripts\python.exe -c "from src.utils.config import load_config; c = load_config(); print('Provider LLM:', c['llm']['default_provider'])"
```

### 2. Teste de Logging
```powershell
venv\Scripts\python.exe -c "from src.utils.logger import setup_logging; from src.utils.config import load_config; setup_logging(load_config()); import logging; logging.info('Test OK')"
```

### 3. Teste Whisper (Carrega modelo - pode demorar)
```powershell
venv\Scripts\python.exe -c "import whisper; print('Loading tiny model...'); m = whisper.load_model('tiny'); print('OK!')"
```

---

## 📝 Executar com Logs Visíveis

```powershell
# Terminal 1: Executar app
venv\Scripts\python.exe src\main.py

# Terminal 2: Ver logs em tempo real
Get-Content logs\ai-copilot.log -Wait -Tail 20
```

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| "python não encontrado" | Use `venv\Scripts\python.exe` |
| "ModuleNotFoundError" | Execute `venv\Scripts\pip install -r requirements.txt` |
| "Config not found" | Execute `copy config\config.example.yaml config\config.yaml` |
| Whisper muito lento | Normal na primeira vez (baixa modelos) |

---

## 📊 Próximos Passos

1. **Testar Whisper** com áudio real
2. **Instalar Ollama** (opcional - LLMs locais)
3. **Implementar** componentes core:
   - Audio Capture (`src/capture/audio_capture.py`)
   - ASR Pipeline (`src/processing/asr_pipeline.py`)
   - LLM Router (`src/llm/router.py`)
   - UI Overlay (`src/ui/overlay.py`)

---

## ⚡ Comandos Essenciais

```powershell
# Rodar
.\run.bat

# Verificar
.\verify.bat

# Executar manual
venv\Scripts\python.exe src\main.py

# Ver logs
type logs\ai-copilot.log

# Testes
venv\Scripts\pytest tests\ -v
```

**Tudo pronto para desenvolvimento!** 🚀
