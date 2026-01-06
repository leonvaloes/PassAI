// Profile Chat JavaScript
const API_BASE = 'http://localhost:8000/api/profile';

let conversationId = null;
let userId = 'leonardo'; // TODO: Get from session/auth

const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const startBtn = document.getElementById('startBtn');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

// Start conversation
async function startConversation() {
    try {
        startBtn.disabled = true;
        startBtn.textContent = '⏳ Iniciando...';
        
        const response = await fetch(`${API_BASE}/chat/start?user_id=${userId}`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to start conversation');
        
        const data = await response.json();
        conversationId = data.conversation_id;
        
        // Clear welcome message
        chatMessages.innerHTML = '';
        
        // Show AI's first message
        addMessage(data.message, 'ai');
        updateProgress(data.progress);
        
        // Enable input
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
        
        // Hide start button
        startBtn.style.display = 'none';
        
    } catch (error) {
        console.error('Error starting conversation:', error);
        alert('Erro ao iniciar conversa. Verifique se o servidor está rodando.');
        startBtn.disabled = false;
        startBtn.textContent = '🚀 Iniciar Conversa';
    }
}

// Send message
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || !conversationId) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.disabled = true;
    sendBtn.disabled = true;
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                conversation_id: conversationId
            })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // Add AI response
        addMessage(data.message, 'ai');
        updateProgress(data.progress);
        
        // Check if conversation is complete
        if (data.state === 'COMPLETO') {
            userInput.disabled = true;
            sendBtn.disabled = true;
            
            setTimeout(() => {
                if (confirm('Perfil salvo com sucesso! Deseja fechar esta janela?')) {
                    window.close();
                }
            }, 2000);
        } else {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(typingId);
        addMessage('❌ Erro ao enviar mensagem. Tente novamente.', 'ai');
        userInput.disabled = false;
        sendBtn.disabled = false;
    }
}

// Add message to chat
function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add typing indicator
function addTypingIndicator() {
const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai';
    typingDiv.id = 'typing-indicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(typingContent);
    chatMessages.appendChild(typingDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return 'typing-indicator';
}

// Remove typing indicator
function removeTypingIndicator(id) {
    const typing = document.getElementById(id);
    if (typing) typing.remove();
}

// Update progress
function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
}

// Enter to send
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !userInput.disabled) {
        sendMessage();
    }
});
