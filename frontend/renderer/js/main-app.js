// Main App - Connects everything together

let captureActive = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Initializing AI Copilot...');
  
  // Initialize WebSocket
  window.ws = new WebSocketClient();
  
  // Setup WebSocket handlers
  setupWebSocketHandlers();
  
  // Setup UI event listeners
  setupUIListeners();
  
  console.log('✅ AI Copilot ready!');
});

function setupWebSocketHandlers() {
  // AI Chat responses
  window.ws.on('ai_chat_response', (data) => {
    console.log('AI Response:', data.text);
    addChatMessage(data.text, false);
  });
  
  // Conversation messages (transcriptions)
  window.ws.on('conversation_message', (data) => {
    console.log('Transcription:', data.speaker, data.text);
    addTranscription(data.speaker, data.text);
  });
  
  // Audio levels - FIXED
  window.ws.on('audio_level', (data) => {
    console.log('Audio level:', data.source, data.level);
    updateMeter(data.source, data.level);
  });
  
  // Status updates
  window.ws.on('status', (data) => {
    console.log('Status:', data.status);
  });
  
  // Conversation cleared
  window.ws.on('conversation_cleared', () => {
    clearTranscriptions();
  });
}

function setupUIListeners() {
  // Chat input
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  
  sendBtn.addEventListener('click', sendChatMessage);
  
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      sendChatMessage();
    } else if (e.key === 'Enter') {
      sendChatMessage();
    }
  });
  
  // Capture buttons
  const startBtn = document.getElementById('startCaptureBtn');
  const stopBtn = document.getElementById('stopCaptureBtn');
  
  startBtn.addEventListener('click', () => {
    window.ws.sendCommand('start_capture');
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    captureActive = true;
  });
  
  stopBtn.addEventListener('click', () => {
    window.ws.sendCommand('stop_capture');
    stopBtn.classList.add('hidden');
    startBtn.classList.remove('hidden');
    captureActive = false;
  });
}

function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  
  if (!text) return;
  
  // Add user message to UI
  addChatMessage(text, true);
  
  // Send to backend
  window.ws.sendAiChat(text);
  
  // Clear input
  input.value = '';
}
