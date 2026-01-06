// Job Search - PassAI
const API_BASE = 'http://localhost:8000/api/jobs';

let currentJob = null;

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active from all tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active to clicked tab
        tab.classList.add('active');
        const tabName = tab.dataset.tab;
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// Extract job from URL or text
async function extractJob() {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    
    let url, text;
    
    if (activeTab === 'url') {
        url = document.getElementById('job-url').value.trim();
        if (!url) {
            alert('Please enter a job URL');
            return;
        }
    } else {
        text = document.getElementById('job-text').value.trim();
        if (!text) {
            alert('Please paste job description');
            return;
        }
    }
    
    // Show loading
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('btn-extract').disabled = true;
    
    try {
        let response;
        
        if (url) {
            // Scrape from URL
            response = await fetch(`${API_BASE}/scrape`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
        } else {
            // Create from text (manual)
            response = await fetch(`${API_BASE}/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: "Manual Entry",
                    company: "Unknown",
                    description: text
                })
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to extract job');
        }
        
        const jobData = await response.json();
        
        // Get full details
        const detailsResponse = await fetch(`${API_BASE}/${jobData.id}`);
        const fullJob = await detailsResponse.json();
        
        currentJob = fullJob;
        
        // Display preview
        displayPreview(fullJob);
        
    } catch (error) {
        console.error('Error extracting job:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Hide loading
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('btn-extract').disabled = false;
    }
}

// Display job preview
function displayPreview(job) {
    // Populate fields
    document.getElementById('preview-title').textContent = job.title || 'No title';
    document.getElementById('preview-company').textContent = `🏢 ${job.company || 'Unknown'}`;
    
    // Location
    const location = job.location;
    let locationText = '📍 Not specified';
    if (location) {
        if (location.remote) {
            locationText = '📍 Remote';
        } else if (location.city) {
            locationText = `📍 ${location.city}${location.state ? ', ' + location.state : ''}`;
        }
    }
    document.getElementById('preview-location').textContent = locationText;
    
    // Seniority
    const seniorityBadge = document.getElementById('preview-seniority');
    seniorityBadge.textContent = job.seniority || 'N/A';
    
    // Tech stack
    const stackContainer = document.getElementById('preview-stack');
    stackContainer.innerHTML = '';
    if (job.techKeywords && job.techKeywords.length > 0) {
        job.techKeywords.forEach(tech => {
            const tag = document.createElement('span');
            tag.className = 'tech-tag';
            tag.textContent = tech;
            stackContainer.appendChild(tag);
        });
    } else {
        stackContainer.innerHTML = '<span class="hint">No keywords extracted</span>';
    }
    
    // Must have
    const mustHaveList = document.getElementById('preview-must-have');
    mustHaveList.innerHTML = '';
    if (job.mustHave && job.mustHave.length > 0) {
        job.mustHave.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            mustHaveList.appendChild(li);
        });
    } else {
        mustHaveList.innerHTML = '<li class="hint">Not specified</li>';
    }
    
    // Nice to have
    const niceHaveList = document.getElementById('preview-nice-have');
    niceHaveList.innerHTML = '';
    if (job.niceToHave && job.niceToHave.length > 0) {
        job.niceToHave.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            niceHaveList.appendChild(li);
        });
    } else {
        niceHaveList.innerHTML = '<li class="hint">Not specified</li>';
    }
    
    // Show preview section
    document.getElementById('preview-section').classList.remove('hidden');
    
    // Scroll to preview
    document.getElementById('preview-section').scrollIntoView({ behavior: 'smooth' });
}

// Save job (already saved via API, just refresh list)
async function saveJob() {
    alert('✅ Job saved successfully!');
    await loadJobs();
    resetForm();
}

// Reset form
function resetForm() {
    document.getElementById('job-url').value = '';
    document.getElementById('job-text').value = '';
    document.getElementById('preview-section').classList.add('hidden');
    currentJob = null;
}

// Load saved jobs
async function loadJobs() {
    try {
        const response = await fetch(`${API_BASE}?limit=50`);
        const jobs = await response.json();
        
        displayJobsList(jobs);
        
        // Update count
        document.getElementById('jobs-count').textContent = `${jobs.length} jobs`;
        
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

// Display jobs list
function displayJobsList(jobs) {
    const container = document.getElementById('jobs-list');
    
    if (jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📭 No jobs yet</p>
                <p class="hint">Extract a job from URL or text to get started</p>
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

// Create job card element
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.dataset.jobId = job.id;
    
    // Location text
    let locationText = 'Location not specified';
    if (job.location) {
        if (job.location.remote) {
            locationText = 'Remote';
        } else if (job.location.city) {
            locationText = `${job.location.city}${job.location.state ? ', ' + job.location.state : ''}`;
        }
    }
    
    // Tech stack HTML
    let techStackHTML = '';
    if (job.techKeywords && job.techKeywords.length > 0) {
        const topTech = job.techKeywords.slice(0, 5);
        techStackHTML = topTech.map(tech => 
            `<span class="tech-tag">${tech}</span>`
        ).join('');
    }
    
    card.innerHTML = `
        <div class="job-card-header">
            <h3>${job.title || 'Untitled'}</h3>
            ${job.seniority ? `<span class="job-badge">${job.seniority}</span>` : ''}
        </div>
        <div class="job-meta">
            <span>🏢 ${job.company || 'Unknown'}</span>
            <span>📍 ${locationText}</span>
        </div>
        ${techStackHTML ? `
            <div class="job-tech-stack">
                <div>${techStackHTML}</div>
            </div>
        ` : ''}
        <div class="job-actions">
            <button class="btn btn-secondary" onclick="viewJobDetails('${job.id}')">
                👁️ View Details
            </button>
            <button class="btn btn-secondary" onclick="deleteJob('${job.id}')">
                🗑️ Delete
            </button>
        </div>
    `;
    
    return card;
}

// View job details
async function viewJobDetails(jobId) {
    try {
        const response = await fetch(`${API_BASE}/${jobId}`);
        const job = await response.json();
        
        currentJob = job;
        displayPreview(job);
        
    } catch (error) {
        console.error('Error loading job details:', error);
        alert('Failed to load job details');
    }
}

// Delete job
async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('✅ Job deleted');
            await loadJobs();
        }
        
    } catch (error) {
        console.error('Error deleting job:', error);
        alert('Failed to delete job');
    }
}

// Filter jobs
function filterJobs() {
    const searchTerm = document.getElementById('search-filter').value.toLowerCase();
    const cards = document.querySelectorAll('.job-card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Refresh jobs
async function refreshJobs() {
    await loadJobs();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
});
