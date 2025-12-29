// Screenshot functionality
async function captureScreenshot() {
    try {
        console.log('Capturing screenshot...');
        
        // Hide window before capture
        if (window.electronAPI?.setOpacity) {
            window.electronAPI.setOpacity(0);
        }
        
        // Wait for window to become invisible
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Get monitor setting
        const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
        const monitor = parseInt(settings.screenshotMonitor || '0');
        
        // Call backend API
        const response = await fetch('http://localhost:8000/api/screenshot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ monitor })
        });
        
        const data = await response.json();
        
        // Show window again
        if (window.electronAPI?.setOpacity) {
            window.electronAPI.setOpacity(1);
        }
        
        if (data.success) {
            // Show success notification
            showNotification('Screenshot Capturado', {
                body: `Salvo: ${data.filename}`,
                icon: 'success'
            });
            
            // Add to chat
            addScreenshotToChat(data.filename);
            
            console.log('Screenshot saved:', data.filepath);
        } else {
            showNotification('Erro ao Capturar Screenshot', {
                body: data.error || 'Erro desconhecido',
                icon: 'error'
            });
            
            console.error('Screenshot failed:', data.error);
        }
        
    } catch (error) {
        // Make sure window is visible even on error
        if (window.electronAPI?.setOpacity) {
            window.electronAPI.setOpacity(1);
        }
        
        console.error('Screenshot error:', error);
        showNotification('Erro ao Capturar Screenshot', {
            body: 'Falha na comunicação com o backend',
            icon: 'error'
        });
    }
}

function showNotification(title, options = {}) {
    // Check if notifications are supported
    if (!('Notification' in window)) {
        console.warn('Notifications not supported');
        return;
    }
    
    // Request permission if needed
    if (Notification.permission === 'granted') {
        new Notification(title, options);
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification(title, options);
            }
        });
    }
}

// Listen for hotkey events from Electron
if (window.electronAPI && window.electronAPI.onHotkey) {
    window.electronAPI.onHotkey((action) => {
        if (action === 'screenshot') {
            captureScreenshot();
        }
    });
}

console.log('📸 Screenshot handler loaded');


function addScreenshotToChat(filename) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message screenshot-message';
    
    const imageUrl = `http://localhost:8000/screenshots/${filename}`;
    const timestamp = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="screenshot-container">
            <img src="${imageUrl}" alt="Screenshot" class="screenshot-preview" loading="lazy" onclick="openScreenshotModal('${imageUrl}')"/>
            <div class="screenshot-info">
                <span>📸 Screenshot capturado</span>
                <small>${timestamp}</small>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Modal para fullscreen
function openScreenshotModal(imageUrl) {
    let modal = document.getElementById('screenshotModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'screenshotModal';
        modal.className = 'screenshot-modal';
        modal.innerHTML = `<img src="" alt="Screenshot Fullscreen"/>`;
        modal.onclick = () => modal.classList.remove('active');
        document.body.appendChild(modal);
    }
    
    const img = modal.querySelector('img');
    img.src = imageUrl;
    modal.classList.add('active');
}
