# 🚀 PassAI - AI-Powered Development Assistant

Assistente de desenvolvimento com transcrição em tempo real, Vision AI e chat inteligente.

## ✨ Features

- 🎙️ **Captura de Microfone** - Transcrição instantânea em PT-BR
- 🔊 **Captura de Áudio do Sistema** - Transcrição de apps/YouTube/reuniões
- 👁️ **Vision AI** - Análise de screenshots com LLaVA
- 🤖 **Chat Inteligente** - Integração com Ollama/OpenAI
- 🪟 **Interface Flutuante** - Always-on-top, transparente
- 📊 **Medidores em Tempo Real** - Visualização de áudio

## 🚀 Quick Start

### Método Rápido (Recomendado)
```bash
.\start.bat
```

### Manual

**Backend:**
```bash
cd d:\p2\ai-copilot
venv\Scripts\activate
python backend\server.py
```

**Frontend:**
```bash
cd frontend
npm start
```

## ⚙️ Configuração

- **Config:** `backend/config/config.yaml`
- **Modelo ASR:** Whisper Large
- **Vision AI:** LLaVA (via Ollama)
- **Ganho Áudio Sistema:** Adaptativo (8-20x)

## 📝 Documentação

Ver `PROJECT_STATUS.md` para documentação completa.

## 🔧 Troubleshooting

**Porta 8000 em uso:**
```bash
taskkill /F /IM python.exe
```

**Ollama não conecta:**
- Verificar se Ollama está rodando: `http://localhost:11434`
- Instalar modelos: `ollama pull llama3.1:8b` e `ollama pull llava`

## 📊 Stack

- **Backend:** Python, FastAPI, Whisper, PyAudioWPatch, LLaVA
- **Frontend:** Electron, JavaScript
- **IA:** Ollama (Llama 3.1, LLaVA) / OpenAI

---

**PassAI** - Desenvolvido com foco em produtividade e IA multimodal em tempo real.
