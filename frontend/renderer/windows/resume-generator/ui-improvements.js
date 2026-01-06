/**
 * UI Improvements for Resume Generator
 * - Variant History Display
 * - AI Questions System
 * - Profile Selector
 */

// API_BASE is already declared in resume-generator.js
// const API_BASE = 'http://localhost:8000/api/resume';

// ============================================
// VARIANT HISTORY
// ============================================

/**
 * Show variant history for current job
 */
async function showVariantHistory(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/variants`);
        if (!response.ok) {
            console.warn('No variants found for this job');
            return;
        }
        
        const variants = await response.json();
        if (variants.length === 0) {
            console.log('No variants generated yet');
            return;
        }
        
        // Create history section if it doesn't exist
        let historySection = document.getElementById('variant-history-section');
        if (!historySection) {
            historySection = document.createElement('div');
            historySection.id = 'variant-history-section';
            historySection.className = 'section';
            historySection.innerHTML = `
                <div class="section-header">
                    <h2>📜 Histórico de Currículos</h2>
                    <span class="badge" id="history-count">${variants.length} versões</span>
                </div>
                <div id="history-list" class="history-list"></div>
            `;
            
            // Insert before results section
            const resultsSection = document.getElementById('step-results');
            resultsSection.parentNode.insertBefore(historySection, resultsSection);
        }
        
        // Update count
        document.getElementById('history-count').textContent = `${variants.length} versões`;
        
        // Render history list
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';
        
        variants.forEach((variant, index) => {
            const card = document.createElement('div');
            card.className = 'history-card';
            card.innerHTML = `
                <div class="history-card-header">
                    <h4>Versão ${index + 1}</h4>
                    <span class="badge ${getStatusClass(variant.status)}">${variant.status}</span>
                </div>
                <div class="history-card-body">
                    <div class="history-stat">
                        <span class="label">Score ATS:</span>
                        <span class="value">${variant.ats_score}%</span>
                    </div>
                    <div class="history-stat">
                        <span class="label">Gerado em:</span>
                        <span class="value">${new Date(variant.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                </div>
                <div class="history-card-actions">
                    <button onclick="downloadVariant('${variant.id}')" class="btn btn-sm btn-primary">
                        📥 Baixar DOCX
                    </button>
                    <button onclick="viewVariantDetails('${variant.id}')" class="btn btn-sm btn-secondary">
                        👁️ Visualizar
                    </button>
                </div>
            `;
            historyList.appendChild(card);
        });
        
        historySection.classList.remove('hidden');
        
    } catch (error) {
        console.error('Failed to load variant history:', error);
    }
}

function getStatusClass(status) {
    const statusMap = {
        'APPROVED': 'success',
        'RISK': 'warning',
        'REJECTED': 'danger',
        'PENDING': 'info'
    };
    return statusMap[status] || 'info';
}

async function downloadVariant(variantId) {
    try {
        const response = await fetch(`${API_BASE}/variants/${variantId}/download`);
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resume_${variantId}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('✅ Download started');
    } catch (error) {
        console.error('Download failed:', error);
        alert('Falha ao baixar currículo. Verifique os logs.');
    }
}

async function viewVariantDetails(variantId) {
    try {
        const response = await fetch(`${API_BASE}/variants/${variantId}`);
        if (!response.ok) throw new Error('Failed to load variant');
        
        const variant = await response.json();
        
        // Show modal with variant details
        alert(`
Variant ID: ${variant.id}
Status: ${variant.status}
ATS Score: ${variant.ats_score}%
Created: ${new Date(variant.created_at).toLocaleString('pt-BR')}
        `.trim());
        
    } catch (error) {
        console.error('Failed to load variant details:', error);
    }
}

// ============================================
// AI QUESTIONS SYSTEM
// ============================================

/**
 * Display AI questions to user
 */
function showAIQuestions(questions) {
    if (!questions || questions.length === 0) return;
    
    // Create questions section if it doesn't exist
    let questionsSection = document.getElementById('ai-questions-section');
    if (!questionsSection) {
        questionsSection = document.createElement('div');
        questionsSection.id = 'ai-questions-section';
        questionsSection.className = 'section';
        questionsSection.innerHTML = `
            <div class="section-header">
                <h2>🤔 A IA precisa de mais informações</h2>
                <span class="badge warning">${questions.length} perguntas</span>
            </div>
            <div id="questions-container"></div>
        `;
        
        // Insert before results section
        const resultsSection = document.getElementById('step-results');
        resultsSection.parentNode.insertBefore(questionsSection, resultsSection);
    }
    
    // Render questions
    const container = document.getElementById('questions-container');
    container.innerHTML = '';
    
    questions.forEach((question, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-item';
        questionDiv.innerHTML = `
            <div class="question-text">
                <strong>Pergunta ${index + 1}:</strong> ${question}
            </div>
            <textarea 
                id="answer-${index}" 
                class="question-answer" 
                placeholder="Digite sua resposta aqui..."
                rows="3"
            ></textarea>
        `;
        container.appendChild(questionDiv);
    });
    
    // Add submit button
    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn btn-primary';
    submitBtn.textContent = '📤 Enviar Respostas';
    submitBtn.onclick = () => submitAnswers(questions.length);
    container.appendChild(submitBtn);
    
    questionsSection.classList.remove('hidden');
}

function submitAnswers(questionCount) {
    const answers = [];
    
    for (let i = 0; i < questionCount; i++) {
        const answerEl = document.getElementById(`answer-${i}`);
        if (answerEl && answerEl.value.trim()) {
            answers.push(answerEl.value.trim());
        }
    }
    
    if (answers.length === 0) {
        alert('Por favor, responda pelo menos uma pergunta.');
        return;
    }
    
    console.log('📤 Sending answers:', answers);
    
    // TODO: Send answers back to backend to regenerate with new info
    // For now, just log
    alert(`Respostas enviadas! (${answers.length}/${questionCount})`);
    
    // Hide questions section
    document.getElementById('ai-questions-section').classList.add('hidden');
}

// ============================================
// PROFILE SELECTOR
// ============================================

/**
 * Initialize profile selector
 */
function initProfileSelector() {
    console.log('🔧 Initializing profile selector...');
    
    // Check if selector already exists
    if (document.getElementById('profile-selector')) {
        console.log('✅ Profile selector already exists');
        return;
    }
    
    // Wait for DOM
    const inputSection = document.getElementById('step-input');
    if (!inputSection) {
        console.warn('⚠️ step-input not found, retrying in 100ms...');
        setTimeout(initProfileSelector, 100);
        return;
    }
    
    // Create profile selector
    const selector = document.createElement('div');
    selector.id = 'profile-selector';
    selector.className = 'profile-selector';
    selector.innerHTML = `
        <label for="profile-select">👤 Perfil:</label>
        <select id="profile-select" class="form-control">
            <option value="Leonardo">Leonardo (Desenvolvedor Full-Stack)</option>
            <option value="Luan">Luan (Mercado)</option>
        </select>
    `;
    
    // Insert after section header
    const sectionHeader = inputSection.querySelector('.section-header');
    if (sectionHeader) {
        sectionHeader.after(selector);
    } else {
        inputSection.insertBefore(selector, inputSection.firstChild);
    }
    
    console.log('✅ Profile selector created and inserted');
}

function getSelectedProfile() {
    const select = document.getElementById('profile-select');
    return select ? select.value : 'Leonardo';
}

// ============================================
// INITIALIZATION
// ============================================

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProfileSelector);
} else {
    initProfileSelector();
}

console.log('✅ UI Improvements loaded');
