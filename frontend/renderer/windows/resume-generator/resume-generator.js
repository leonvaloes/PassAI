// Resume Generator - JavaScript Logic
// Integrates with PassAI backend API

const API_BASE = 'http://localhost:8000/api/resume';
let currentJob = null;
let websocket = null;

// DOM Elements
const sections = {
    input: document.getElementById('step-input'),
    preview: document.getElementById('step-preview'),
    progress: document.getElementById('step-progress'),
    results: document.getElementById('step-results')
};

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        // Update tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// Extract Job
document.getElementById('btn-extract').addEventListener('click', async () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    let inputType, content;
    
    if (activeTab === 'text') {
        inputType = 'text';
        content = document.getElementById('job-text').value.trim();
    } else if (activeTab === 'url') {
        inputType = 'url';
        content = document.getElementById('job-url').value.trim();
    } else if (activeTab === 'file') {
        // Handle file upload (to be implemented)
        alert('File upload coming soon!');
        return;
    }
    
    if (!content) {
        alert('Please provide job information');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_type: inputType, content })
        });
        
        if (!response.ok) throw new Error('Extraction failed');
        
        currentJob = await response.json();
        showJobPreview(currentJob);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Show Job Preview
function showJobPreview(job) {
    document.getElementById('preview-cargo').textContent = job.cargo;
    document.getElementById('preview-empresa').textContent = job.empresa;
    document.getElementById('preview-ats').textContent = job.ats_detectado;
    document.getElementById('preview-local').textContent = job.local || 'N/A';
    
    const techTags = document.getElementById('preview-tech');
    techTags.innerHTML = '';
    job.requisitos_tecnicos.forEach(req => {
        const tag = document.createElement('span');
        tag.className = 'tag-item';
        tag.textContent = req;
        techTags.appendChild(tag);
    });
    
    sections.input.classList.add('hidden');
    sections.preview.classList.remove('hidden');
}

// Generate Resumes
document.getElementById('btn-generate').addEventListener('click', async () => {
    if (!currentJob) return;
    
    // Hide preview, show progress
    sections.preview.classList.add('hidden');
    sections.progress.classList.remove('hidden');
    
    // Connect WebSocket
    connectWebSocket(currentJob.id);
    
    // Start generation
    try {
        const response = await fetch(`${API_BASE}/jobs/${currentJob.id}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_resume: {
                    nome: 'Leonardo Valões',
                    email: 'leonardo@example.com'
                    // TODO: Get from user profile
                }
            })
        });
        
        if (!response.ok) throw new Error('Generation failed to start');
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// WebSocket Connection
function connectWebSocket(jobId) {
    websocket = new WebSocket(`ws://localhost:8000/api/resume/ws/${jobId}`);
    
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
            updateProgress(data);
        } else if (data.type === 'complete') {
            onGenerationComplete(jobId);
        } else if (data.type === 'error') {
            alert(data.message);
        }
    };
    
    websocket.onerror = () => {
        console.error('WebSocket error');
    };
}

// Update Progress
function updateProgress(data) {
    document.getElementById('progress-round').textContent = `${data.round}/10`;
    document.getElementById('progress-variants').textContent = data.variants_total;
    document.getElementById('progress-approved').textContent = data.variants_approved;
    document.getElementById('progress-score').textContent = data.best_score.toFixed(1);
    
    const progress = (data.round / 10) * 100;
    document.getElementById('progress-fill').style.width = `${progress}%`;
}

// Generation Complete
async function onGenerationComplete(jobId) {
    websocket.close();
    
    // Fetch variants
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/variants`);
        const variants = await response.json();
        
        displayVariants(variants);
        
        sections.progress.classList.add('hidden');
        sections.results.classList.remove('hidden');
    } catch (error) {
        alert(`Error loading results: ${error.message}`);
    }
}

// Display Variants
function displayVariants(variants) {
    const list = document.getElementById('variants-list');
    list.innerHTML = '';
    
    document.getElementById('results-count').textContent = `${variants.length} variants`;
    
    variants.forEach((variant, index) => {
        const card = document.createElement('div');
        card.className = 'variant-card';
        card.dataset.status = variant.ats_status;
        
        card.innerHTML = `
            <div class="score-badge">${variant.ats_score.toFixed(1)}</div>
            <div class="variant-info">
                <div class="variant-title">Variant #${index + 1}</div>
                <div class="variant-tags">
                    <span class="tag ${variant.ats_status.toLowerCase()}">${variant.ats_status}</span>
                    <span class="tag">Ranking: ${variant.ranking_score.toFixed(1)}</span>
                </div>
            </div>
            <div class="variant-actions">
                <button class="btn-icon" onclick="downloadVariant('${variant.id}')">
                    💾 Download
                </button>
            </div>
        `;
        
        list.appendChild(card);
    });
}

// Download Variant
async function downloadVariant(variantId) {
    window.open(`${API_BASE}/variants/${variantId}/download`, '_blank');
}

// Filters
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        document.querySelectorAll('.variant-card').forEach(card => {
            if (filter === 'all' || card.dataset.status === filter) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// Drop zone
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        // TODO: Handle file upload
        console.log('File selected:', file.name);
    }
});

console.log('✅ Resume Generator loaded');
