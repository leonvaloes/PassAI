# 🚀 Como Testar e Rodar - AI Copilot

## Método 1: Executar Aplicação Principal (Rápido)

```powershell
# No diretório do projeto
cd d:\p2\ai-copilot

# Executar diretamente (sem ativar venv)
venv\Scripts\python.exe src\main.py
```

**O que você verá:**
```
2025-12-22 17:22:57 - __main__ - INFO - Starting AI Copilot v0.1.0
2025-12-22 17:22:57 - __main__ - INFO - Configuration loaded
2025-12-22 17:22:57 - __main__ - INFO - Initializing components...
2025-12-22 17:22:57 - __main__ - INFO - AI Copilot is running. Press Ctrl+C to exit.
```

**Para parar:** Pressione `Ctrl+C`

---

## Método 2: Ativar Ambiente Virtual (Recomendado)

```powershell
# Ativar venv
venv\Scripts\activate

# Seu prompt mudará para:
(venv) PS D:\p2\ai-copilot>

# Executar
python src\main.py

# Quando terminar, desativar
deactivate
```

---

## 🧪 Testar Componentes Individuais

### 1. Testar Whisper (ASR)

```powershell
# Criar arquivo de teste
venv\Scripts\python.exe -c "import whisper; print('Whisper OK:', whisper.__version__)"
```

### 2. Testar PyTorch

```powershell
venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

**Saída esperada:**
```
PyTorch: 2.9.1
CUDA available: True  # Se você tem GPU NVIDIA
```

### 3. Testar OpenAI Client

```powershell
venv\Scripts\python.exe -c "import openai; print('OpenAI client OK:', openai.__version__)"
```

### 4. Testar Configuração

```powershell
venv\Scripts\python.exe -c "from src.utils.config import load_config; import json; print(json.dumps(load_config(), indent=2))"
```

### 5. Testar PyQt6 (UI)

```powershell
venv\Scripts\python.exe -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

---

## 🧪 Executar Testes Automatizados

```powershell
# Executar todos os testes
venv\Scripts\pytest tests\ -v

# Executar teste específico
venv\Scripts\pytest tests\test_basic.py -v

# Com coverage
venv\Scripts\pytest tests\ --cov=src --cov-report=html
```

**Saída esperada:**
```
tests/test_basic.py::test_import PASSED
tests/test_basic.py::test_config_loading PASSED
```

---

## 🔍 Verificar Instalação Completa

Crie um script de verificação:

```powershell
# Criar script de verificação
@"
import sys
print('=' * 50)
print('AI Copilot - Verification')
print('=' * 50)

packages = {
    'whisper': 'Whisper (ASR)',
    'torch': 'PyTorch',
    'openai': 'OpenAI API',
    'PyQt6': 'PyQt6 UI',
    'cv2': 'OpenCV',
    'PIL': 'Pillow',
    'mss': 'Screen Capture',
    'sounddevice': 'Audio',
    'yaml': 'Configuration',
    'pydantic': 'Validation'
}

for pkg, name in packages.items():
    try:
        __import__(pkg)
        print(f'✅ {name:20} OK')
    except ImportError as e:
        print(f'❌ {name:20} FAILED: {e}')

print('=' * 50)
print('Verification complete!')
"@ | venv\Scripts\python.exe
```

---

## 🎯 Teste Interativo (Python REPL)

```powershell
# Entrar no Python com venv ativo
venv\Scripts\python.exe

# Dentro do Python:
>>> from src.utils.config import load_config
>>> config = load_config()
>>> print(config['llm']['default_provider'])
local

>>> # Testar Whisper
>>> import whisper
>>> model = whisper.load_model("tiny")  # Modelo pequeno para teste
>>> print("Whisper loaded successfully!")

>>> # Sair
>>> exit()
```

---

## 📊 Benchmark de Performance (Opcional)

```powershell
# Criar script de benchmark
@"
import time
import whisper

print('Loading Whisper model...')
start = time.time()
model = whisper.load_model('tiny')
print(f'Model loaded in {time.time() - start:.2f}s')

# Simular transcrição
print('Testing transcription...')
# (necessário arquivo de áudio para teste real)
"@ | venv\Scripts\python.exe
```

---

## 🐛 Troubleshooting

### Erro: "python: command not found"
```powershell
# Use o caminho completo
venv\Scripts\python.exe src\main.py
```

### Erro: "ModuleNotFoundError"
```powershell
# Reinstalar dependências
venv\Scripts\pip install -r requirements.txt
```

### Erro: "Config file not found"
```powershell
# Copiar config exemplo
copy config\config.example.yaml config\config.yaml
```

---

## 📝 Logs

Os logs são salvos em:
```
logs/ai-copilot.log
```

Ver logs em tempo real:
```powershell
# Em outro terminal
Get-Content logs\ai-copilot.log -Wait -Tail 50
```

---

## ✅ Checklist de Teste

Antes de começar desenvolvimento:

- [ ] `venv\Scripts\python.exe src\main.py` executa sem erros
- [ ] Whisper importa corretamente
- [ ] PyTorch detecta GPU (se aplicável)
- [ ] OpenAI client funciona
- [ ] PyQt6 importa sem erros
- [ ] Config carrega corretamente
- [ ] Logs são criados em `logs/`

---

## 🚀 Próximos Passos Após Testes

1. **Implementar Audio Capture**
   ```powershell
   # Testar captura de áudio
   venv\Scripts\python.exe -c "import sounddevice; print(sounddevice.query_devices())"
   ```

2. **Testar Whisper com Áudio Real**
   - Gravar um áudio de teste
   - Transcrever com Whisper
   - Validar latência

3. **Implementar LLM Router**
   - Instalar Ollama
   - Testar conexão local/cloud

4. **Implementar UI**
   - Criar janela PyQt6
   - Testar overlay privado
   - Validar hotkeys

---

**Comando único para verificar tudo:**
```powershell
venv\Scripts\python.exe -c "import whisper, torch, openai, PyQt6, cv2, sounddevice; print('✅ Todos os componentes OK!')"
```

Se isso funcionar sem erros, está tudo pronto! 🎉
