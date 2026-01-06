// Resume Generator - CV History Interface
// Loads all jobs with generated CVs and displays variants

const API_BASE = 'http://localhost:8000/api/resume';

let jobHistory = [];
let selectedJobId = null;
let currentVariants = [];

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadJobHistory();
    
    // Listen for IPC messages to select specific job
    if (window.electronAPI) {
        // Future: handle 'select-job' IPC message
    }
});

// Load all jobs with CVs
async function loadJobHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        jobHistory = await response.json();
        
        displayJobList(jobHistory);
        
        // If there's a job, auto-select the first one
        if (jobHistory.length > 0 && !selectedJobId) {
            selectJob(jobHistory[0].job_id);
        }
        
    } catch (error) {
        console.error('Error loading job history:', error);
        showError('Failed to load job history');
    }
}

// Display job list in sidebar
function displayJobList(jobs) {
    const container = document.getElementById('job-list');
    const countBadge = document.getElementById('jobs-count');
    
    countBadge.textContent = jobs.length;
    
    if (jobs.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #9ca3af">
                <p style="font-size: 2rem; margin-bottom: 8px;">📭</p>
                <p>No jobs yet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    jobs.forEach(job => {
        const item = document.createElement('div');
        item.className = 'job-list-item';
        if (job.job_id === selectedJobId) {
            item.classList.add('selected');
        }
        
        // Score color
        let scoreClass = 'poor';
        if (job.best_score >= 90) scoreClass = 'excellent';
        else if (job.best_score >= 80) scoreClass = 'good';
        else if (job.best_score >= 70) scoreClass = 'fair';
        
        item.innerHTML = `
            <div class="job-item-header">
                <div class="job-item-title">${job.job_title}</div>
                <span class="score-badge ${scoreClass}">${job.best_score || 0}</span>
            </div>
            <div class="job-item-company">${job.company}</div>
            <div class="job-item-meta">
                <span class="variant-count">${job.variants_count} CV${job.variants_count !== 1 ? 's' : ''}</span>
                ${job.created_at ? `<span>${formatDate(job.created_at)}</span>` : ''}
            </div>
        `;
        
        item.onclick = () => selectJob(job.job_id);
        container.appendChild(item);
    });
}

// Select a job and load its variants
async function selectJob(jobId) {
    selectedJobId = jobId;
    
    // Update UI selection
    document.querySelectorAll('.job-list-item').forEach(item => {
        item.classList.remove('selected');
    });
    event?.target?.closest('.job-list-item')?.classList.add('selected');
    
    // Load variants for this job
    await loadVariants(jobId);
    
    // Show job panel
    document.getElementById('no-selection').classList.add('hidden');
    document.getElementById('job-panel').classList.remove('hidden');
}

// Load variants for selected job
async function loadVariants(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/variants`);
        currentVariants = await response.json();
        
        // Update panel header
        const job = jobHistory.find(j => j.job_id === jobId);
        if (job) {
            document.getElementById('job-title').textContent = job.job_title;
            document.getElementById('job-company').textContent = job.company;
            document.getElementById('variants-badge').textContent =`${currentVariants.length} CV${currentVariants.length !== 1 ? 's' : ''}`;
            
            const scoreBadge = document.getElementById('score-badge');
            if (currentVariants.length > 0) {
                scoreBadge.textContent = `Best: ${job.best_score}`;
            } else {
                scoreBadge.textContent = 'No CVs yet';
            }
            
            // Toggle buttons
            if (currentVariants.length > 0) {
                document.getElementById('btn-generate-more').classList.remove('hidden');
                document.getElementById('btn-generate-first').classList.add('hidden');
            } else {
                document.getElementById('btn-generate-more').classList.add('hidden');
                document.getElementById('btn-generate-first').classList.remove('hidden');
            }
        }
        
        // Display variants (or empty state)
        displayVariants(currentVariants);
        
    } catch (error) {
        console.error('Error loading variants:', error);
        showError('Failed to load variants');
    }
}

// Display variants in grid
function displayVariants(variants) {
    const grid = document.getElementById('variants-grid');
    
    if (variants.length === 0) {
        // Show empty state with Generate CV button
        grid.innerHTML = `
            <div class="empty-state-variants">
                <div class="empty-icon">📄</div>
                <h3>No CVs generated yet for this job</h3>
                <p>Generate your first CV to see it here</p>
                <button class="btn btn-primary" onclick="generateFirstCV()" style="margin-top: 20px;">
                    🚀 Generate CV
                </button>
            </div>
        `;
        
        // Hide Generate More button when no variants
        document.getElementById('btn-generate-more').style.display = 'none';
        return;
    }
    
    // Show Generate More button when variants exist
    document.getElementById('btn-generate-more').style.display = 'block';
    
    grid.innerHTML = '';
    
    // Sort by score (best first)
    const sorted = [...variants].sort((a, b) => b.ats_score - a.ats_score);
    
    sorted.forEach((variant, index) => {
        const card = document.createElement('div');
        card.className = 'variant-card';
        
        // Score badge color
        let scoreClass = 'poor';
        const score = variant.ats_score;
        if (score >= 90) scoreClass = 'excellent';
        else if (score >= 80) scoreClass = 'good';
        else if (score >= 70) scoreClass = 'fair';
        
        // Status icon and text
        let statusClass = variant.ats_status?.toLowerCase() || 'pending';
        let statusIcon = '⏳';
        let statusText = 'Pending';
        if (statusClass === 'approved') {
            statusIcon = '✅';
            statusText = 'Approved';
        } else if (statusClass === 'risk') {
            statusIcon = '⚠️';
            statusText = 'At Risk';
        } else if (statusClass === 'rejected') {
            statusIcon = '❌';
            statusText = 'Rejected';
        }
        
        card.innerHTML = `
            <div class="card-header-row">
                <span class="status-icon ${statusClass}" title="${statusText}">
                    ${statusIcon}
                </span>
                <span class="score-badge ${scoreClass}">${score.toFixed(1)}</span>
            </div>
            
            <div class="variant-preview">
                <div class="variant-number-large">
                    #${index + 1}
                </div>
                <strong>${variant.content?.nome || 'N/A'}</strong>
                <p>${variant.content?.cargo || 'N/A'}</p>
            </div>
            
            <div class="variant-actions">
                <button class="btn-icon" onclick="previewVariant('${variant.id}')">
                    👁️ Preview
                </button>
                <button class="btn-icon btn-download" onclick="downloadVariant('${variant.id}')">
                    💾 Download
                </button>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

// Preview variant in modal
async function previewVariant(variantId) {
    const variant = currentVariants.find(v => v.id === variantId);
    if (!variant) return;
    
    const modal = document.getElementById('preview-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const downloadBtn = document.getElementById('modal-download-btn');
    
    // Set title
    const variantIndex = currentVariants.indexOf(variant) + 1;
    modalTitle.textContent = `Variant #${variantIndex} - Score: ${variant.ats_score.toFixed(1)}`;
    
    // Set download button
    downloadBtn.onclick = () => downloadVariant(variantId);
    
    // Format content
    const content = variant.content;
    let html = `
        <div class="cv-preview">
            <div class="cv-header">
                <h1>${content.nome || 'N/A'}</h1>
                <p class="cv-title">${content.cargo || 'N/A'}</p>
                <div class="cv-contact">
                    ${content.email ? `<span>📧 ${content.email}</span>` : ''}
                    ${content.telefone ? `<span>📱 ${content.telefone}</span>` : ''}
                    ${content.linkedin ? `<span>🔗 ${content.linkedin}</span>` : ''}
                </div>
                ${content.cidade && content.estado ? `<p>📍 ${content.cidade}, ${content.estado}</p>` : ''}
            </div>
    `;
    
    // Experiences
    if (content.experiencias && content.experiencias.length > 0) {
        html += '<div class="cv-section"><h2>💼 Experiência Profissional</h2>';
        content.experiencias.forEach(exp => {
            html += `
                <div class="cv-experience">
                    <div class="exp-header">
                        <strong>${exp.cargo || 'N/A'}</strong>
                        <span>${exp.periodo || 'N/A'}</span>
                    </div>
                    <div class="exp-company">${exp.empresa || 'N/A'}</div>
                    ${exp.descricao ? `<p>${exp.descricao}</p>` : ''}
                    ${exp.realizacoes && exp.realizacoes.length > 0 ? `
                        <ul>
                            ${exp.realizacoes.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Education
    if (content.educacao && content.educacao.length > 0) {
        html += '<div class="cv-section"><h2>🎓 Educação</h2>';
        content.educacao.forEach(edu => {
            html += `
                <div class="cv-education">
                    <strong>${edu.curso || 'N/A'}</strong>
                    <p>${edu.instituicao || 'N/A'}</p>
                    ${edu.periodo ? `<span>${edu.periodo}</span>` : ''}
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Skills
    if (content.habilidades && content.habilidades.length > 0) {
        html += `
            <div class="cv-section">
                <h2>🛠️ Habilidades</h2>
                <div class="skills-grid">
                    ${content.habilidades.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    
    modalBody.innerHTML = html;
    modal.classList.remove('hidden');
}

// Download variant
function downloadVariant(variantId) {
    window.open(`${API_BASE}/variants/${variantId}/download`, '_blank');
}

// Format date
function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days === 0) return 'today';
        if (days === 1) return 'yesterday';
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString('pt-BR');
    } catch {
        return 'recent';
    }
}

// Show error
function showError(message) {
    console.error(message);
    // TODO: Better error UI
}

// Generate First CV for a job
async function generateFirstCV() {
    if (!selectedJobId) return;
    
    const job = jobHistory.find(j => j.job_id === selectedJobId);
    if (!job) return;
    
    if (confirm(`Generate CV for ${job.job_title} at ${job.company}?`)) {
        try {
            // Use the same endpoint as Jobs window
            const response = await fetch(`${API_BASE}/jobs/${selectedJobId}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            if (!response.ok) throw new Error('Generation failed');
            
            alert('CV generation started! Check back in 1-2 minutes.');
            
            // Poll for completion
            const checkInterval = setInterval(async () => {
                await loadVariants(selectedJobId);
                await loadJobHistory();
                
                if (currentVariants.length > 0) {
                    clearInterval(checkInterval);
                }
            }, 5000);
            
            setTimeout(() => clearInterval(checkInterval), 180000);
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// Make it available globally
window.generateFirstCV = generateFirstCV;

// Generate +N More Variants
async function generateMoreVariants() {
    if (!selectedJobId) return;
    
    const countInput = document.getElementById('variant-count');
    const count = parseInt(countInput.value) || 3;
    
    // Validate
    if (count < 1 || count > 10) {
        alert('Count must be between 1 and 10');
        countInput.value = 3;
        return;
    }
    
    const btn = document.getElementById('btn-generate-more');
    const statusEl = document.getElementById('generate-status');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '⏳ Generating...';
        statusEl.textContent = `Generating ${count} additional variant${count > 1 ? 's' : ''}...`;
        statusEl.classList.remove('hidden');
        
        const response = await fetch(`${API_BASE}/jobs/${selectedJobId}/generate-more?count=${count}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }
        
        const result = await response.json();
        
        // Show success message
        statusEl.textContent = `✅ ${result.new_variants} new variant${result.new_variants > 1 ? 's' : ''} generated! Total: ${result.total_variants}`;
        btn.innerHTML = '✅ Generated!';
        
        // Reload variants after a short delay
        setTimeout(async () => {
            await loadVariants(selectedJobId);
            await loadJobHistory(); // Update counts in sidebar
            
            btn.innerHTML = originalText;
            btn.disabled = false;
            statusEl.classList.add('hidden');
        }, 2000);
        
    } catch (error) {
        console.error('Error:', error);
        statusEl.textContent = `❌ Error: ${error.message}`;
        btn.innerHTML = '❌ Failed';
        
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 3000);
    }
}

// Make it available globally
window.generateMoreVariants = generateMoreVariants;

// Extract and Generate CV from modal
window.extractAndGenerateCVFromModal = async function() {
    const activeTab = document.querySelector('#new-cv-modal .tab.active').dataset.tab;
    const statusEl = document.getElementById('new-cv-status');
    const btn = document.getElementById('btn-extract-new-cv');
    
    let inputType, content;
    
    if (activeTab === 'text') {
        inputType = 'text';
        content = document.getElementById('new-cv-job-text').value.trim();
    } else if (activeTab === 'url') {
        inputType = 'url';
        content = document.getElementById('new-cv-job-url').value.trim();
    } else if (activeTab === 'file') {
        statusEl.textContent = 'File upload coming soon!';
        statusEl.classList.remove('hidden');
        return;
    }
    
    if (!content) {
        statusEl.textContent = 'Please provide job information';
        statusEl.classList.remove('hidden');
        return;
    }
    
    try {
        // Step 1: Extract job data
        btn.disabled = true;
        btn.textContent = 'Extracting job data...';
        statusEl.textContent = 'Analyzing job posting...';
        statusEl.classList.remove('hidden');
        
        const extractResponse = await fetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_type: inputType, content })
        });
        
        if (!extractResponse.ok) throw new Error('Extraction failed');
        
        const job = await extractResponse.json();
        const jobId = job.id;
        
        // Step 2: Start CV generation
        btn.textContent = 'Generating CVs...';
        statusEl.textContent = 'Generating resume variants...';
        
        const genResponse = await fetch(`${API_BASE}/jobs/${jobId}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Uses default base_resume
        });
        
        if (!genResponse.ok) throw new Error('Generation failed');
        
        // Step 3: Close modal and wait for generation to complete
        closeNewCVModal();
        
        // Show progress message
        alert('CV generation started! It will appear in the list when complete (usually 1-2 minutes).');
        
        // Reload history periodically to show the new job when ready
        const checkInterval = setInterval(async () => {
            await loadJobHistory();
            
            // Check if job exists in history
            const jobExists = jobHistory.some(j => j.job_id === jobId);
            if (jobExists) {
                clearInterval(checkInterval);
                selectJob(jobId);
            }
        }, 5000); // Check every 5 seconds
        
        // Stop checking after 3 minutes
        setTimeout(() => clearInterval(checkInterval), 180000);
        
    } catch (error) {
        console.error('Error:', error);
        statusEl.textContent = `Error: ${error.message}`;
        btn.disabled = false;
        btn.textContent = 'Extract & Generate →';
    }
};

console.log('✅ CV History loaded');
