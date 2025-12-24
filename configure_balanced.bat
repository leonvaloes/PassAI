@echo off
REM Balanced configuration - Best quality/speed ratio

echo ========================================
echo AI Copilot - BALANCED Config
echo ========================================
echo.

echo Creating BALANCED config.yaml...
echo (Base model + quality optimizations)
echo.

(
echo # AI Copilot - BALANCED Configuration
echo # Melhor equilíbrio qualidade/velocidade
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
echo   model: "base"
echo   language: "pt"
echo   word_timestamps: true
echo   temperature: 0.0
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

echo ✅ BALANCED Config created!
echo.
echo ========================================
echo Configuração:
echo ========================================
echo   Modelo: BASE (rápido)
echo   Beam size: 5 (melhor qualidade)
echo   Best of: 5 (melhores candidatos)
echo   VAD: 0.012 (sensível)
echo.
echo ✅ Equilíbrio perfeito:
echo   - Qualidade: ~85-90%% (MUITO BOM!)
echo   - Velocidade: ~1-2s (RÁPIDO!)
echo.
echo ========================================
pause
