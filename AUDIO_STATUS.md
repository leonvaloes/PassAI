# Guia Rápido - Sistema de Áudio

## Estado Atual

✅ **Funcionando:**
- Microfone (captura e transcrição)
- Medidores de áudio em tempo real
- Seleção de dispositivo de entrada
- WebSocket communication

⏳ **Em Desenvolvimento:**
- Captura de áudio do sistema (loopback)
- Speaker "OUTROS" para apps/música

## Próximos Passos para Áudio do Sistema

Para implementar a captura de áudio do sistema (checkbox "Capturar áudio do sistema"), será necessário:

1. **Instalar PyAudioWPatch** (Windows):
   ```bash
   pip install PyAudioWPatch
   ```

2. **Implementar DualAudioCapture**:
   - Usar `backend/core/capture/dual_audio_capture.py` (já existe mas desabilitado)
   - Capturar simultaneamente:
     - Microfone → "YOU"
     - Sistema (loopback) → "OUTROS"

3. **Ativar no Backend**:
   - Modificar `backend/server.py` para usar `DualAudioCapture` quando a opção estiver ativa
   - Processar ambos streams separadamente

4. **Testar**:
   - Tocar música/vídeo
   - Ver transcrições "OUTROS" aparecerem

## Limitações Conhecidas

- **PyAudioWPatch**: Só funciona no Windows
- **Sample Rate**: Dispositivo de sistema pode ter taxa diferente
- **Latência**: Dual capture pode aumentar latência

## Como Ativar (quando pronto)

1. Configurações → Áudio
2. ☑ Capturar áudio do sistema
3. Salvar configurações
4. Reiniciar captura
