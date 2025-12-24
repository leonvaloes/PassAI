@echo off
REM Quick configuration script for better transcription quality

echo ========================================
echo AI Copilot - Quick Config
echo ========================================
echo.

echo Creating optimized config.yaml...

(
echo # AI Copilot Configuration - OTIMIZADO
echo # Melhor qualidade de transcrição
echo.
echo llm:
echo   default_provider: "local"
echo   local:
echo     base_url: "http://localhost:11434"
echo     model: "llama3.1:8b"
echo.
echo audio:
echo   sample_rate: 16000
echo   vad_threshold: 0.015
echo   min_speech_duration_ms: 500
echo   max_speech_gap_ms: 1000
echo.
echo asr:
echo   model: "base"
echo   language: "pt"
echo   word_timestamps: true
echo.
echo context:
echo   window_size: 10
echo.
echo ui:
echo   width: 450
echo   height: 350
echo   opacity: 0.95
echo.
echo logging:
echo   level: "INFO"
echo   file: "logs/ai-copilot.log"
) > config\config.yaml

echo ✅ Config created!
echo.
echo Changes made:
echo   - ASR model: tiny → base (MELHOR QUALIDADE)
echo   - VAD threshold: 0.02 → 0.015 (mais sensível)
echo   - Min speech: 300ms → 500ms (fala mais longa)
echo.
echo ========================================
echo Ready to run!
echo ========================================
echo.
echo Run: venv\Scripts\python.exe src\main.py
echo.
pause
