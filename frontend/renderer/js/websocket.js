// WebSocket Client with Event Emitter

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectInterval = null;
    this.listeners = {};
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws');
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.emit('connected');
      
      if (this.reconnectInterval) {
        clearInterval(this.reconnectInterval);
        this.reconnectInterval = null;
      }
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const { type, data } = message;
      
      console.log('📨', type, data);
      this.emit(type, data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected');
      
      if (!this.reconnectInterval) {
        this.reconnectInterval = setInterval(() => {
          console.log('Reconnecting...');
          this.connect();
        }, 3000);
      }
    };
  }
  
  // Event emitter pattern
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }
  
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }
  
  // Send methods
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  sendCommand(action, extraData = {}) {
    this.send({
      type: 'command',
      data: { action, ...extraData }
    });
    console.log('Command sent:', action, extraData);
  }
  
  sendAiChat(question) {
    this.send({
      type: 'ai_chat',
      data: { question }
    });
  }
}
