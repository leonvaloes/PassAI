// Main App - Component Orchestration

class App {
  constructor() {
    console.log('🚀 Initializing App...');
    
    // Initialize components
    this.components = {
      inputField: new InputField('inputFieldContainer'),
      controls: new ControlButtons('controlsContainer'),
      transcription: new TranscriptionPanel('transcriptionContainer'),
      audioMeters: new AudioMeters('audioMetersContainer'),
      actions: new ActionButtons('actionsContainer'),
      aiChat: new AIChat('aiChatContainer')
    };
    
    // Initialize WebSocket
    this.ws = new WebSocketClient();
    
    // Wire up component callbacks
    this.setupComponentCallbacks();
    
    // Wire up WebSocket handlers
    this.setupWebSocketHandlers();
    
    console.log('✅ App initialized');
  }
  
  setupComponentCallbacks() {
    // InputField
    this.components.inputField.onSubmit = (text) => {
      this.handleManualInput(text);
    };
    
    // ControlButtons
    this.components.controls.onStart = () => {
      this.ws.sendCommand('start_capture');
    };
    
    this.components.controls.onStop = () => {
      this.ws.sendCommand('stop_capture');
    };
    
    this.components.controls.onPause = () => {
      this.ws.sendCommand('pause');
    };
    
    this.components.controls.onClear = () => {
      this.ws.sendCommand('clear');
    };
    
    // TranscriptionPanel
    this.components.transcription.onClear = () => {
      this.ws.sendCommand('clear');
    };
    
    // ActionButtons
    this.components.actions.onAnalyze = () => {
      this.ws.sendCommand('analyze');
      this.components.actions.setAnalyzing(true);
    };
    
    // AIChat
    this.components.aiChat.onSend = (text) => {
      this.ws.sendAiChat(text);
    };
  }
  
  setupWebSocketHandlers() {
    // Conversation messages
    this.ws.on('conversation_message', (data) => {
      this.components.transcription.addMessage(
        data.speaker,
        data.text,
        data.timestamp
      );
      
      // Simulate audio meter activity
      const source = data.speaker === 'YOU' ? 'you' : 'other';
      this.components.audioMeters.simulateActivity(source);
    });
    
    // Audio level updates (real-time meters)
    this.ws.on('audio_level', (data) => {
      this.components.audioMeters.updateLevel(data.source, data.level);
    });
    
    // AI chat responses
    this.ws.on('ai_chat_response', (data) => {
      this.components.aiChat.addMessage(data.text, false);
      this.components.actions.setAnalyzing(false);
    });
    
    // Conversation cleared
    this.ws.on('conversation_cleared', () => {
      this.components.transcription.clear();
    });
    
    // Status updates
    this.ws.on('status', (data) => {
      console.log('Status:', data.status);
      
      if (data.status.includes('Ready')) {
        this.components.actions.setAnalyzing(false);
      }
    });
  }
  
  handleManualInput(text) {
    // Add as conversation message
    const timestamp = new Date().toISOString();
    this.components.transcription.addMessage('YOU', text, timestamp);
    
    // Could also send to backend if needed
    // this.ws.sendManualTranscription(text);
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
