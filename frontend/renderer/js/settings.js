// Settings Manager

async function refreshAudioDevices() {
  const micSelect = document.getElementById('micDeviceSelect');
  const outputSelect = document.getElementById('outputDeviceSelect');
  if (!micSelect || !outputSelect) return;
  
  micSelect.innerHTML = '<option value="default">Carregando...</option>';
  outputSelect.innerHTML = '<option value="default">Carregando...</option>';
  
  try {
    const response = await fetch('http://localhost:8000/api/audio-devices');
    const data = await response.json();
    
    // Populate inputs (microphones)
    micSelect.innerHTML = '';
    const defaultMicOption = document.createElement('option');
    defaultMicOption.value = 'default';
    defaultMicOption.textContent = 'Dispositivo Padrão do Sistema';
    micSelect.appendChild(defaultMicOption);
    
    data.inputs.forEach((device, index) => {
      const option = document.createElement('option');
      option.value = device.index || index;
      option.textContent = device.name || `Dispositivo ${index}`;
      micSelect.appendChild(option);
    });
    
    // Populate loopback devices (for system audio capture)
    outputSelect.innerHTML = '';
    const defaultOutputOption = document.createElement('option');
    defaultOutputOption.value = 'default';
    defaultOutputOption.textContent = 'Padrão do Sistema';
    outputSelect.appendChild(defaultOutputOption);
    
    // Use loopback devices if available
    const loopbackDevices = data.loopbacks || [];
    if (loopbackDevices.length > 0) {
      loopbackDevices.forEach((device) => {
        const option = document.createElement('option');
        option.value = device.index;
        option.textContent = device.name;
        outputSelect.appendChild(option);
      });
    } else {
      // Fallback to outputs if no loopbacks
      data.outputs.forEach((device) => {
        const option = document.createElement('option');
        option.value = device.index;
        option.textContent = device.name + ' (Loopback)';
        outputSelect.appendChild(option);
      });
    }
    
  } catch (error) {
    console.error('Failed to load audio devices:', error);
    micSelect.innerHTML = '<option value="default">Dispositivo Padrão (erro)</option>';
    outputSelect.innerHTML = '<option value="default">Desativado (erro)</option>';
  }
}

async function testOutputDevice() {
  const outputSelect = document.getElementById('outputDeviceSelect');
  const selectedDevice = outputSelect?.value || 'default';
  const selectedName = outputSelect?.options[outputSelect.selectedIndex]?.text || 'Desconhecido';
  
  console.log('Testing output device:', selectedDevice, selectedName);
  
  if (selectedDevice === 'default') {
    alert('⚠️ Nenhum dispositivo selecionado!\n\nSelecione um dispositivo de saída primeiro.');
    return;
  }
  
  // Create a simple beep sound using Web Audio API
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800; // 800 Hz beep
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
    
    // Show info
    alert(`🔊 Tocando som de teste!\n\nDispositivo: ${selectedName}\n\nSe você OUVIU o beep, este é o dispositivo correto!\nSe NÃO OUVIU, selecione outro dispositivo.`);
    
  } catch (error) {
    console.error('Failed to play test audio:', error);
    alert('❌ Erro ao tocar som de teste.\n\nVerifique o console para detalhes.');
  }
}

function toggleSystemAudio(enabled) {
  console.log('='.repeat(50));
  console.log('toggleSystemAudio CALLED!');
  console.log('Enabled:', enabled);
  console.log('='.repeat(50));
  
  localStorage.setItem('enableSystemAudio', enabled);
  
  const outputSelect = document.getElementById('outputDeviceSelect');
  const outputDevice = outputSelect?.value || 'default';
  console.log('Output device select element:', outputSelect);
  console.log('Selected output device:', outputDevice);
  
  console.log('window.ws exists?', !!window.ws);
  console.log('window.ws.sendCommand exists?', !!(window.ws && window.ws.sendCommand));
  
  if (window.ws && window.ws.sendCommand) {
    console.log('Attempting to send command...');
    window.ws.sendCommand('toggle_system_audio', { 
      enabled: enabled,
      output_device: outputDevice 
    });
    console.log('✅ Command sent successfully!');
  } else {
    console.error('❌ WebSocket not ready or sendCommand not available');
    console.error('window.ws:', window.ws);
  }
  console.log('='.repeat(50));
}

function toggleAlwaysOnTop(enabled) {
  console.log('Always on top:', enabled);
  localStorage.setItem('alwaysOnTop', enabled);
}

function toggleClickThrough(enabled) {
  console.log('Click-through:', enabled);
  localStorage.setItem('clickThrough', enabled);
  
  if (!enabled && window.electronAPI && window.electronAPI.setIgnoreMouseEvents) {
    window.electronAPI.setIgnoreMouseEvents(false);
  }
}

function saveSettings() {
  const settings = {
    alwaysOnTop: document.getElementById('alwaysOnTopCheck')?.checked,
    clickThrough: document.getElementById('clickThroughCheck')?.checked,
    micDevice: document.getElementById('micDeviceSelect')?.value,
    outputDevice: document.getElementById('outputDeviceSelect')?.value,
    enableSystemAudio: document.getElementById('enableSystemAudio')?.checked,
    autoStartCapture: document.getElementById('autoStartCapture')?.checked,
    llmProvider: document.getElementById('llmProviderSelect')?.value,
    autoAnalyze: document.getElementById('autoAnalyze')?.checked
  };
  
  localStorage.setItem('appSettings', JSON.stringify(settings));
  
  alert('✅ Configurações salvas!');
  
  console.log('Settings saved:', settings);
}

function loadSettings() {
  const saved = localStorage.getItem('appSettings');
  if (!saved) {
    // Load devices on first run
    setTimeout(refreshAudioDevices, 500);
    return;
  }
  
  try {
    const settings = JSON.parse(saved);
    
    if (document.getElementById('alwaysOnTopCheck')) {
      document.getElementById('alwaysOnTopCheck').checked = settings.alwaysOnTop !== false;
    }
    if (document.getElementById('clickThroughCheck')) {
      document.getElementById('clickThroughCheck').checked = settings.clickThrough !== false;
    }
    if (document.getElementById('enableSystemAudio')) {
      document.getElementById('enableSystemAudio').checked = settings.enableSystemAudio || false;
    }
    if (document.getElementById('autoStartCapture')) {
      document.getElementById('autoStartCapture').checked = settings.autoStartCapture || false;
    }
    if (document.getElementById('llmProviderSelect')) {
      document.getElementById('llmProviderSelect').value = settings.llmProvider || 'ollama';
    }
    if (document.getElementById('autoAnalyze')) {
      document.getElementById('autoAnalyze').checked = settings.autoAnalyze || false;
    }
    
    // Load devices and restore selections
    setTimeout(() => {
      refreshAudioDevices().then(() => {
        if (settings.micDevice && document.getElementById('micDeviceSelect')) {
          document.getElementById('micDeviceSelect').value = settings.micDevice;
        }
        if (settings.outputDevice && document.getElementById('outputDeviceSelect')) {
          document.getElementById('outputDeviceSelect').value = settings.outputDevice;
          console.log('Restored output device:', settings.outputDevice);
        }
      });
    }, 500);
    
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
});
