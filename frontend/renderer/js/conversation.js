// Conversation and AI Chat UI

console.log('🎨 UI loaded');

const messagesList = document.getElementById('messagesList');
const messagesScroll = document.getElementById('messagesScroll');
const aiChatHistory = document.getElementById('aiChatHistory');
const aiChatInput = document.getElementById('aiChatInput');
const sendAiChatBtn = document.getElementById('sendAiChatBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsPanel = document.getElementById('settingsPanel');
const pauseToggle = document.getElementById('pauseToggle');
const clearConvBtn = document.getElementById('clearConvBtn');
const saveConvBtn = document.getElementById('saveConvBtn');
const closeBtn = document.getElementById('closeBtn');

let hasConvMessages = false;
let hasAiChatMessages = false;

// Close button
closeBtn.addEventListener('click', () => {
  window.close();
});

// Settings toggle
settingsBtn.addEventListener('click', () => {
  const isVisible = settingsPanel.style.display !== 'none';
  settingsPanel.style.display = isVisible ? 'none' : 'block';
});

// Pause toggle
pauseToggle.addEventListener('change', (e) => {
  const action = e.target.checked ? 'pause' : 'resume';
  if (window.wsClient) {
    window.wsClient.sendCommand(action);
  }
});

// Clear conversation
clearConvBtn.addEventListener('click', () => {
  if (window.wsClient) {
    window.wsClient.sendCommand('clear');
  }
});

// Save conversation
saveConvBtn.addEventListener('click', () => {
  if (window.wsClient) {
    window.wsClient.sendCommand('save');
  }
});

// Add conversation message (YOU/OTHER)
function addConversationMessage(message) {
  const { timestamp, speaker, text } = message;
  
  if (!hasConvMessages) {
    messagesList.innerHTML = '';
    hasConvMessages = true;
  }
  
  const time = new Date(timestamp).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  
  const messageEl = document.createElement('div');
  messageEl.className = `message ${speaker.toLowerCase()}`;
  
  messageEl.innerHTML = `
    <span class="time">${time}</span>
    <span class="speaker">${speaker}:</span>
    <span class="text">${text}</span>
  `;
  
  messagesList.appendChild(messageEl);
  messagesScroll.scrollTop = messagesScroll.scrollHeight;
  
  console.log(`💬 Conv: [${speaker}] ${text.substring(0, 30)}...`);
}

// Add AI chat message
function addAiChatMessage(text, isUser = false) {
  if (!hasAiChatMessages) {
    aiChatHistory.innerHTML = '';
    hasAiChatMessages = true;
  }
  
  const messageEl = document.createElement('div');
  messageEl.className = `ai-chat-message ${isUser ? 'user' : 'ai'}`;
  messageEl.textContent = text;
  
  aiChatHistory.appendChild(messageEl);
  aiChatHistory.scrollTop = aiChatHistory.scrollHeight;
  
  console.log(`🤖 Chat: [${isUser ? 'User' : 'AI'}] ${text.substring(0, 30)}...`);
}

// Send AI chat message
sendAiChatBtn.addEventListener('click', () => {
  const question = aiChatInput.value.trim();
  if (question && window.wsClient) {
    // Add user message to chat
    addAiChatMessage(question, true);
    
    // Send to backend
    window.wsClient.sendAiChat(question);
    
    // Clear input
    aiChatInput.value = '';
  }
});

aiChatInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendAiChatBtn.click();
  }
});

// Analyze button
analyzeBtn.addEventListener('click', () => {
  if (window.wsClient) {
    window.wsClient.sendCommand('analyze');
  }
});

// Clear conversation
function clearConversation() {
  messagesList.innerHTML = '<div class="placeholder">Start speaking...</div>';
  hasConvMessages = false;
  console.log('🧹 Conversation cleared');
}

// Export functions
window.addConversationMessage = addConversationMessage;
window.addAiChatMessage = addAiChatMessage;
window.clearConversation = clearConversation;

console.log('✅ UI ready');
