// Drag & Drop Image Analysis

// Initialize drag & drop on chat window
function initializeDragAndDrop() {
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) return;
    
    const dropZone = document.createElement('div');
    dropZone.id = 'dropZone';
    dropZone.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(37, 99, 235, 0.9);
        border: 3px dashed #fff;
        border-radius: 8px;
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        pointer-events: none;
    `;
    
    const dropText = document.createElement('div');
    dropText.style.cssText = `
        color: #fff;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
    `;
    dropText.innerHTML = '📸 Solte a imagem aqui<br><small style="font-size: 16px;">para análise com IA</small>';
    dropZone.appendChild(dropText);
    chatWindow.appendChild(dropZone);
    
    // Drag events
    chatWindow.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.display = 'flex';
    });
    
    chatWindow.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        // Only hide if leaving chat window entirely
        if (e.target === chatWindow) {
            dropZone.style.display = 'none';
        }
    });
    
    chatWindow.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.display = 'none';
        
        const files = Array.from(e.dataTransfer.files);
        const imageFiles = files.filter(f => f.type.startsWith('image/'));
        
        if (imageFiles.length === 0) {
            showNotification('Arquivo Inválido', {
                body: 'Por favor, solte apenas imagens (PNG, JPG, etc.)'
            });
            return;
        }
        
        // Process first image
        const imageFile = imageFiles[0];
        await analyzeDroppedImage(imageFile);
    });
    
    console.log('✅ Drag & drop initialized');
}

async function analyzeDroppedImage(file) {
    try {
        // Show processing notification
        showNotification('Processando Imagem...', {
            body: `Analisando ${file.name} com Vision AI`
        });
        
        // Read file as base64
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Data = e.target.result.split(',')[1]; // Remove data:image/...;base64,
            
            // Send to backend for analysis
            const response = await fetch('http://localhost:8000/api/vision/analyze-upload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_data: base64Data,
                    filename: file.name
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show analysis in chat
                showImageAnalysisResult(file.name, result.analysis);
                
                showNotification('Análise Completa!', {
                    body: 'Veja o resultado no chat'
                });
            } else {
                showNotification('Erro na Análise', {
                    body: result.error || 'Verifique se Ollama está rodando'
                });
            }
        };
        
        reader.onerror = () => {
            showNotification('Erro ao Ler Imagem', {
                body: 'Falha ao processar arquivo'
            });
        };
        
        reader.readAsDataURL(file);
        
    } catch (error) {
        console.error('Drop image analysis error:', error);
        showNotification('Erro', {
            body: 'Falha ao analisar imagem'
        });
    }
}

function showImageAnalysisResult(filename, analysis) {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message ai';
        messageDiv.innerHTML = `
            <strong>📸 Análise de Imagem:</strong><br>
            <small style="color: #999;">Arquivo: ${filename}</small><br><br>
            ${analysis.replace(/\n/g, '<br>')}
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeDragAndDrop();
});

console.log('📎 Drag & drop module loaded');
