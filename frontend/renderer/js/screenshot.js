// Screenshot Handler

async function captureScreenshot() {
    try {
        console.log('📸 Capturing screenshot...');
        
        // Call backend API
        const response = await fetch('http://localhost:8000/api/screenshot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                monitor: 0,  // All monitors
                analyze: false  // No vision analysis for now
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show success notification
            showNotification('Screenshot Capturado', {
                body: `Salvo: ${data.filename}\nTamanho: ${data.size.width}x${data.size.height}`,
                icon: 'success'
            });
            
            console.log('✅ Screenshot saved:', data.filepath);
        } else {
            showNotification('Erro ao Capturar Screenshot', {
                body: data.error || 'Erro desconhecido',
                icon: 'error'
            });
            
            console.error('❌ Screenshot failed:', data.error);
        }
        
    } catch (error) {
        console.error('❌ Screenshot capture error:', error);
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
