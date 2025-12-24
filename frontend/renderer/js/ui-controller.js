// UI Controller - Handles UI interactions

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('hidden-sidebar');
}

function toggleAudioPanel() {
  const panel = document.getElementById('audioPanel');
  const toggle = document.getElementById('audioToggle');
  
  panel.classList.toggle('hidden');
  toggle.textContent = panel.classList.contains('hidden') ? '▶' : '▼';
}

function toggleMeters() {
  const meters = document.getElementById('metersContent');
  const toggle = document.getElementById('metersToggle');
  
  meters.classList.toggle('hidden');
  toggle.textContent = meters.classList.contains('hidden') 
    ? 'Clique para mostrar' 
    : 'Clique para ocultar';
}

function clearTranscriptions() {
  const list = document.getElementById('transcriptionList');
  list.innerHTML = '<div class="placeholder-small">Nenhuma transcrição</div>';
}

// Add chat message to UI
function addChatMessage(text, isUser) {
  const messagesContainer = document.getElementById('chatMessages');
  
  // Remove placeholder
  const placeholder = messagesContainer.querySelector('.placeholder');
  if (placeholder) {
    placeholder.remove();
  }
  
  const messageEl = document.createElement('div');
  messageEl.className = `chat-message ${isUser ? 'user' : 'ai'}`;
  messageEl.textContent = text;
  
  messagesContainer.appendChild(messageEl);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add transcription to sidebar
function addTranscription(speaker, text) {
  const list = document.getElementById('transcriptionList');
  
  // Remove placeholder
  const placeholder = list.querySelector('.placeholder-small');
  if (placeholder) {
    placeholder.remove();
  }
  
  const item = document.createElement('div');
  item.className = `transcription-item ${speaker === 'OTHER' ? 'other' : ''}`;
  item.innerHTML = `
    <div class="transcription-speaker">${speaker}</div>
    <div class="transcription-text">${text}</div>
  `;
  
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

// Update audio meters
function updateMeter(source, level) {
  const meterId = source === 'you' ? 'meterYou' : 'meterOther';
  const meter = document.getElementById(meterId);
  if (meter) {
    meter.style.width = `${level}%`;
  }
}

function analyzeTranscription() {
  if (window.ws) {
    window.ws.sendCommand('analyze');
  }
}
