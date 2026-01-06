// Jobs List - PassAI
const API_BASE = 'http://localhost:8000/api/jobs';

let allJobs = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
});

// Load jobs from API
async function loadJobs() {
    try {
        // Call ranked endpoint to get scored jobs
        const response = await fetch(`${API_BASE}/ranked?limit=100`);
        allJobs = await response.json();
        
        displayJobs(allJobs);
        updateStats();
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs');
    }
}

// Display jobs
function displayJobs(jobs) {
    const container = document.getElementById('jobs-list');
    
    if (jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📭 No jobs found</p>
                <p class="hint">Run a search profile to find opportunities</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    jobs.forEach(job => {
        const card = createJobCard(job);
        container.appendChild(card);
    });
}

// Create job card
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.onclick = () => openJob(job.url);
    
    // Get score data
    const score = job.score || {};
    const hasScore = score.overall !== undefined;
    
    // Location
    const location = job.location || {};
    let locationText = '';
    if (location.remote) {
        locationText = '🌍 Remote';
    } else if (location.city && location.state) {
        locationText = `📍 ${location.city}, ${location.state}`;
    } else if (location.city) {
        locationText = `📍 ${location.city}`;
    } else if (location.country) {
        locationText = `📍 ${location.country}`;
    }
    
    // Keywords with matched highlighting
    let keywordsHTML = '';
    if (job.techKeywords && job.techKeywords.length > 0) {
        const matched = score.matched_skills || [];
        keywordsHTML = `
            <div class="job-keywords">
                ${job.techKeywords.slice(0, 5).map(k => {
                    const isMatched = matched.includes(k);
                    return `<span class="keyword-tag ${isMatched ? 'matched' : ''}">${k}</span>`;
                }).join('')}
            </div>
        `;
    }
    
    // Match score badge
    let scoreBadgeHTML = '';
    if (hasScore) {
        const scoreValue = Math.round(score.overall);
        let scoreClass = 'poor';
        if (scoreValue >= 80) scoreClass = 'excellent';
        else if (scoreValue >= 60) scoreClass = 'good';
        else if (scoreValue >= 40) scoreClass = 'fair';
        
        scoreBadgeHTML = `<div class="match-score ${scoreClass}">${scoreValue}%</div>`;
    }
    
    // Salary estimate
    let salaryHTML = '';
    if (score.salary_estimate) {
        const sal = score.salary_estimate;
        salaryHTML = `
            <div class="job-salary">
                💰 R$ ${sal.min?.toLocaleString()} - ${sal.max?.toLocaleString()}/mês
            </div>
        `;
    }
    
    // Match reasons
    let reasonsHTML = '';
    if (hasScore && (score.match_reasons?.length > 0 || score.concerns?.length > 0)) {
        reasonsHTML = `
            <div class="job-reasons">
                ${score.match_reasons?.length > 0 ? `
                    <div class="reasons-pros">
                        <strong>✅ Why good match:</strong>
                        <ul>
                            ${score.match_reasons.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${score.concerns?.length > 0 ? `
                    <div class="reasons-cons">
                        <strong>⚠️ Concerns:</strong>
                        <ul>
                            ${score.concerns.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    const country = location.country || 'Unknown';
    
    card.innerHTML = `
        <div class="job-header">
            <div>
                <div class="job-title">${job.title || 'No title'}</div>
                <div class="job-company">${job.company || 'Unknown company'}</div>
            </div>
            <div class="header-badges">
                ${scoreBadgeHTML}
                <span class="job-badge badge-country">${country}</span>
            </div>
        </div>
        
        ${locationText ? `<div class="job-location">${locationText}</div>` : ''}
        ${salaryHTML}
        
        ${keywordsHTML}
        ${reasonsHTML}
        
        <div class="job-footer">
            <span class="job-date">
                📅 ${job.createdAt ? formatDate(job.createdAt) : 'Publicado recentemente'}
            </span>
            <button class="btn-view" onclick="event.stopPropagation(); openJob('${job.url}')">
                View Job →
            </button>
        </div>
        
        <div class="job-actions">
            <button class="btn-action btn-analyze" onclick="event.stopPropagation(); analyzeJob('${job.id || job._id}')">
                📊 Analyzes Match
            </button>
            <button class="btn-action btn-cv" onclick="event.stopPropagation(); generateCV('${job.id || job._id}')">
                📄 Generate CV
            </button>
        </div>
    `;
    
    return card;
}

// Analyze Job
async function analyzeJob(jobId) {
    if (!jobId) return;
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Analyzing...';
    
    try {
        const response = await fetch(`${API_BASE}/${jobId}/analyze`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const result = await response.json();
        
        btn.innerHTML = '✅ Done!';
        setTimeout(() => {
            loadJobs(); // Reload to show new score
        }, 1000);
        
    } catch (error) {
        console.error('Error:', error);
        btn.innerHTML = '❌ Error';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
    }
}

// Generate CV
async function generateCV(jobId) {
    if (!jobId) return;
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Generating...';
    
    try {
        // Call resume API
        const response = await fetch(`http://localhost:8000/api/resume/jobs/${jobId}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({}) // Empty body required by some frameworks
        });
        
        if (!response.ok) throw new Error('Generation failed');
        
        // Show success
        btn.innerHTML = '⚙️ Generating...';
        
        // Poll for completion (simple version)
        let attempts = 0;
        const maxAttempts = 30; // 60 seconds
        
        const interval = setInterval(async () => {
            attempts++;
            try {
                const vResponse = await fetch(`http://localhost:8000/api/resume/jobs/${jobId}/variants`);
                const variants = await vResponse.json();
                
                if (variants && variants.length > 0) {
                    clearInterval(interval);
                    
                    // Find best variant
                    const best = variants.sort((a, b) => b.ats_score - a.ats_score)[0];
                    
                    btn.className = 'btn-action btn-download';
                    btn.innerHTML = '💾 Download CV';
                    btn.disabled = false; // Fix: Re-enable button so it can be clicked!
                    btn.onclick = (e) => {
                        e.stopPropagation();
                        window.open(`http://localhost:8000/api/resume/variants/${best.id}/download`, '_blank');
                    };
                    
                    // Auto-download first time? Maybe annoying. Let user click.
                    // Notify
                    if (window.electronAPI && window.electronAPI.send) {
                         // window.electronAPI.send('notification', 'CV Ready!'); 
                    }
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    btn.innerHTML = '⚠️ Timeout';
                    btn.disabled = false;
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 2000);
        
    } catch (error) {
        console.error('Error:', error);
        btn.innerHTML = '❌ Error';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
    }
}

// Filter jobs
function filterJobs() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const country = document.getElementById('country-filter').value;
    
    let filtered = allJobs;
    
    // Filter by search term
    if (searchTerm) {
        filtered = filtered.filter(job => {
            const title = (job.title || '').toLowerCase();
            const company = (job.company || '').toLowerCase();
            const keywords = (job.techKeywords || []).join(' ').toLowerCase();
            
            return title.includes(searchTerm) || 
                   company.includes(searchTerm) || 
                   keywords.includes(searchTerm);
        });
    }
    
    // Filter by country
    if (country) {
        filtered = filtered.filter(job => {
            const jobCountry = job.location?.country || '';
            return jobCountry === country;
        });
    }
    
    displayJobs(filtered);
    updateStats(filtered.length);
}

// Update stats
function updateStats(count = null) {
    const total = count !== null ? count : allJobs.length;
    document.getElementById('jobs-count').textContent = 
        `${total} job${total !== 1 ? 's' : ''}`;
}

// Open job in browser
function openJob(url) {
    if (url) {
        if (window.electronAPI && window.electronAPI.openExternal) {
            window.electronAPI.openExternal(url);
        } else {
            window.open(url, '_blank');
        }
    }
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
        
        if (minutes < 60) return `há ${minutes} minuto${minutes !== 1 ? 's' : ''}`;
        if (hours < 24) return `há ${hours} hora${hours !== 1 ? 's' : ''}`;
        if (days === 0) return 'hoje';
        if (days === 1) return 'ontem';
        if (days < 7) return `há ${days} dias`;
        if (days < 30) {
            const weeks = Math.floor(days / 7);
            return `há ${weeks} semana${weeks !== 1 ? 's' : ''}`;
        }
        
        return date.toLocaleDateString('pt-BR');
    } catch {
        return 'Recente';
    }
}

// Show error
function showError(message) {
    document.getElementById('jobs-list').innerHTML = `
        <div class="empty-state">
            <p>❌ ${message}</p>
        </div>
    `;
}
