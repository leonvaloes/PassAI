# 🎙️ AI Copilot - Audio Transcription & AI Assistant

Aplicação Electron para transcrição em tempo real com IA integrada.

## ✨ Features

- 🎙️ **Captura de Microfone** - Transcrição instantânea
- 🔊 **Captura de Áudio do Sistema** - Transcrição de apps/YouTube
- 🤖 **IA Integrada** - Chat com Ollama/OpenAI
- 🪟 **Interface Flutuante** - Always-on-top, transparente
- 📊 **Medidores em Tempo Real** - Visualização de áudio

## 🚀 Quick Start

### Backend
```bash
cd d:\p2\ai-copilot
venv\Scripts\activate
python backend\server.py
```

### Frontend
```bash
cd frontend
npm start
```

## ⚙️ Configuração

- **Config:** `backend/config/config.yaml`
- **Modelo:** Whisper Large
- **Ganho Áudio Sistema:** 30x (ajustável em `backend/core/capture/system_audio_capture.py`)

## 📝 Documentação

Ver `PROJECT_STATUS.md` para documentação completa.

## 🔧 Troubleshooting

**Porta 8000 em uso:**
```bash
taskkill /F /IM python.exe
```

**Áudio baixo:**
- Aumentar `gain` em `system_audio_capture.py` (linha 77)

## 📊 Stack

- **Backend:** Python, FastAPI, Whisper, PyAudioWPatch
- **Frontend:** Electron, JavaScript
- **IA:** Ollama / OpenAI

---

Desenvolvido com foco em transcrição de alta qualidade e IA em tempo real.
