@echo off
REM Best quality configuration - Small model

echo ========================================
echo AI Copilot - BEST QUALITY Config
echo ========================================
echo.

echo Creating PREMIUM config.yaml...
echo (Using SMALL model - best quality!)
echo.

(
echo # AI Copilot - PREMIUM Configuration
echo # Máxima qualidade de transcrição
echo.
echo llm:
echo   default_provider: "local"
echo   local:
echo     base_url: "http://localhost:11434"
echo     model: "llama3.1:8b"
echo.
echo audio:
echo   sample_rate: 16000
echo   vad_threshold: 0.012
echo   min_speech_duration_ms: 600
echo   max_speech_gap_ms: 1200
echo.
echo asr:
echo   model: "small"
echo   language: "pt"
echo   word_timestamps: true
echo   beam_size: 5
echo   best_of: 5
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

echo ✅ PREMIUM Config created!
echo.
echo ========================================
echo Changes:
echo ========================================
echo   Model: base → SMALL (MUITO MELHOR!)
echo   VAD: 0.015 → 0.012 (ainda + sensível)
echo   Min speech: 500ms → 600ms
echo   Beam size: 5 (máxima qualidade)
echo.
echo ⚠️ ATENÇÃO:
echo   - Modelo SMALL é ~3-4x mais lento
echo   - Mas a qualidade é MUITO superior
echo   - Recomendado para produção
echo.
echo ========================================
pause
