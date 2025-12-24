// AIChat Component
// AI chat interface with history

class AIChat {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.history = [];
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="ai-chat-messages" id="aiChatMessages">
        <div class="placeholder">Faça uma pergunta...</div>
      </div>
      <div class="ai-chat-input">
        <input 
          type="text" 
          id="aiChatInput" 
          placeholder="Pergunte à IA..."
        />
        <button id="aiChatSend" class="btn-send">📤</button>
      </div>
    `;
    
    this.messagesContainer = document.getElementById('aiChatMessages');
    this.input = document.getElementById('aiChatInput');
    this.attachListeners();
  }
  
  attachListeners() {
    const sendBtn = document.getElementById('aiChatSend');
    
    sendBtn.addEventListener('click', () => {
      this.send();
    });
    
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.send();
      }
    });
  }
  
  send() {
    const text = this.input.value.trim();
    if (text) {
      this.addMessage(text, true);
      this.onSend(text);
      this.input.value = '';
    }
  }
  
  addMessage(text, isUser) {
    // Remove placeholder if first message
    if (this.history.length === 0) {
      this.messagesContainer.innerHTML = '';
    }
    
    this.history.push({ text, isUser });
    
    const messageEl = document.createElement('div');
    messageEl.className = `ai-chat-message ${isUser ? 'user' : 'ai'}`;
    messageEl.textContent = text;
    
    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
  
  clear() {
    this.history = [];
    this.messagesContainer.innerHTML = '<div class="placeholder">Faça uma pergunta para começar...</div>';
  }
  
  onSend(text) {
    // Override in app.js
    console.log('AI Chat send:', text);
  }
}
