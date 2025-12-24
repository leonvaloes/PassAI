# 🚀 AI Copilot - Frontend/Backend Setup

**New Architecture:** Electron Frontend + Python Backend

---

## 📦 Setup

### 1. Install Backend Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```powershell
cd frontend
npm install
```

---

## ▶️ Running the Application

### Option A: Two Terminals (Recommended)

**Terminal 1 - Backend:**
```powershell
.\start_backend.bat
```

**Terminal 2 - Frontend:**
```powershell
.\start_frontend.bat
```

### Option B: Manual

**Backend:**
```powershell
cd backend
..\venv\Scripts\python.exe server.py
```

**Frontend:**
```powershell
cd frontend
npm start
```

---

## ✅ Verification

1. Backend should start on `http://localhost:8000`
2. Frontend window appears (top-right corner)
3. Status shows "🟢 Ready - Connected"
4. Speak to test transcription

---

## 🎯 Features

- **Backend (Port 8000):**
  - FastAPI + WebSocket
  - Audio capture + VAD
  - ASR (Whisper + GPU)
  - LLM routing (Ollama)
  - Session export

- **Frontend (Electron):**
  - Frameless window
  - Always on top
  - Global hotkeys
  - Real-time updates
  - Perssua-style UI

---

## ⌨️ Hotkeys

- `Ctrl+Shift+P` - Pause/Resume
- `Ctrl+Shift+C` - Clear context
- `Ctrl+Shift+S` - Save session

---

## 🔧 Troubleshooting

**Backend won't start:**
- Check if GPU/CUDA is available
- Verify Python 3.10
- Install missing deps: `pip install -r backend/requirements.txt`

**Frontend won't connect:**
- Ensure backend is running first
- Check WebSocket at `ws://localhost:8000/ws`
- Look for errors in DevTools (F12)

**No transcription:**
- Check microphone permissions
- Verify audio capture in backend logs
- Test with louder speech

---

## 📊 API Endpoints

- `GET /health` - Health check
- `GET /stats` - Statistics
- `WS /ws` - WebSocket connection

---

**Ready to use!** 🎉
