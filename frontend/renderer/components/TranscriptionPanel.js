// TranscriptionPanel Component
// Displays live transcription messages

class TranscriptionPanel {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.messages = [];
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="transcription-scroll" id="transcriptionContent">
        <div class="placeholder">Aguardando transcrição...</div>
      </div>
    `;
    
    this.content = document.getElementById('transcriptionContent');
  }
  
  addMessage(speaker, text, timestamp) {
    // Remove placeholder if first message
    if (this.messages.length === 0) {
      this.content.innerHTML = '';
    }
    
    const message = { speaker, text, timestamp };
    this.messages.push(message);
    
    const time = new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    
    const messageEl = document.createElement('div');
    messageEl.className = `transcription-message ${speaker.toLowerCase()}`;
    messageEl.innerHTML = `
      <span class="message-time">${time}</span>
      <span class="message-speaker">${speaker}:</span>
      <span class="message-text">${text}</span>
    `;
    
    this.content.appendChild(messageEl);
    this.content.scrollTop = this.content.scrollHeight;
  }
  
  clear() {
    this.messages = [];
    this.content.innerHTML = '<div class="placeholder">Aguardando transcrição...</div>';
    if (this.onClear) this.onClear();
  }
  
  onClear() {
    // Override in app.js
  }
}
