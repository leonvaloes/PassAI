# AI Copilot - Guia de Início Rápido

## 🚀 Como Iniciar (Método Mais Simples)

### Opção 1: Script Automático (Recomendado)
```bash
.\start_all.bat
```

Este script irá:
1. Parar processos antigos
2. Iniciar o backend
3. Iniciar o frontend
4. Abrir a aplicação

### Opção 2: Manual

**Terminal 1 - Backend:**
```bash
venv\Scripts\python.exe backend\server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## ✅ Como Saber que Está Funcionando

### Backend (Terminal 1)
Você deve ver:
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: ✅ WebSocket connected
```

### Frontend (Electron Window)
- Janela do Electron abre
- Layout com 2 colunas visível:
  - Esquerda: Transcrição
  - Direita: AI Chat
- Console mostra: `✅ WebSocket connected`

## ⚠️ Solucionando Problemas

### "WebSocket connection failed"
**Causa:** Backend não está rodando
**Solução:**
1. Verifique se o backend está rodando no Terminal 1
2. Procure por erros no terminal do backend
3. Reinicie usando `start_all.bat`

### "LLM não disponível"
**Causa:** Ollama não está configurado
**Solução:**
1. **Opção A:** Instale e inicie o Ollama:
   ```
   ollama serve
   ```
2. **Opção B:** Configure OpenAI no `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```

### Múltiplas Instâncias Rodando
**Solução:**
```bash
taskkill /F /IM python.exe
taskkill /F /IM electron.exe
```
Depois execute `start_all.bat`

## 🎯 Testando a Aplicação

### 1. Teste de Transcrição (SEM precisar de LLM)
- Fale no microfone
- Veja mensagens aparecerem no painel esquerdo: "YOU: [sua fala]"
- Medidores de áudio (VOCÊ) devem se mover

### 2. Teste de AI Chat (REQUER Ollama/OpenAI)
- Digite pergunta no chat à direita
- Clique 📤 ou pressione Enter
- Aguarde resposta da IA

### 3. Teste de Análise de Conversa
- Fale várias frases
- Clique "📊 Analisar Transcrição"
- IA analisa toda a conversa capturada

## 📊 Status Esperado

**Funcionando Corretamente:**
- 🟢 Backend: `INFO: Uvicorn running on http://0.0.0.0:8000`
- 🟢 WebSocket: `✅ WebSocket connected`
- 🟢 Transcrição: Mensagens aparecem ao falar
- ⚠️ AI Chat: Requer Ollama/OpenAI configurado

## 🔧 Arquitetura

```
Frontend (Electron)
    ↓ WebSocket (ws://localhost:8000/ws)
Backend (FastAPI)
    ↓
┌─────────────┬──────────────┬─────────────┐
│ Whisper ASR │ Conversation │ LLM Router  │
│   (base)    │   Manager    │  (Ollama)   │
└─────────────┴──────────────┴─────────────┘
```

## 📝 Componentes Frontend

1. **InputField** - Entrada manual de texto
2. **ControlButtons** - Capturar, Pausar, Encerrar
3. **TranscriptionPanel** - Histórico YOU/OTHER
4. **AudioMeters** - Níveis de áudio visuais
5. **ActionButtons** - Ctrl+B, Analisar
6. **AIChat** - Chat com assistente IA
