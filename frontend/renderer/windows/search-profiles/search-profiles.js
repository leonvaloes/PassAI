// Search Profiles - PassAI
const API_BASE = 'http://localhost:8000/api/jobs';

let currentProfileId = null;
let techStack = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProfiles();
    
    // Setup form submit
    document.getElementById('profile-form').addEventListener('submit', handleFormSubmit);
});

// ==================== AUTHENTICATION ====================

function toggleAuthFields() {
    const isChecked = document.getElementById('auth-use-custom').checked;
    const fields = document.getElementById('auth-fields');
    
    if (isChecked) {
        fields.style.display = 'block';
        fields.classList.remove('hidden');
    } else {
        fields.style.display = 'none';
        fields.classList.add('hidden');
    }
}

// ==================== FORM MANAGEMENT ====================

function showCreateForm() {
    currentProfileId = null;
    techStack = [];
    
    document.getElementById('form-title').textContent = 'Create Search Profile';
    document.getElementById('profile-form').reset();
    document.getElementById('stack-tags').innerHTML = '';
    
    // Reset Auth
    document.getElementById('auth-use-custom').checked = false;
    toggleAuthFields();
    
    document.getElementById('form-section').classList.remove('hidden');
    
    // Scroll to form
    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
}

function cancelForm() {
    document.getElementById('form-section').classList.add('hidden');
    currentProfileId = null;
    techStack = [];
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Gather auth config
    const useCustomAuth = document.getElementById('auth-use-custom').checked;
    let authConfig = null;
    
    if (useCustomAuth) {
        authConfig = {
            useCustomAuth: true,
            linkedinEmail: document.getElementById('auth-linkedin-email').value,
            linkedinPassword: document.getElementById('auth-linkedin-password').value
        };
    }
    
    // Gather form data
    const profileData = {
        name: document.getElementById('profile-name').value,
        filters: {
            title: document.getElementById('filter-title').value || null,
            seniority: document.querySelector('input[name="seniority"]:checked').value || null,
            stack: techStack,
            modality: document.getElementById('filter-modality').value || null,
            location: getLocationData(),
            minSalary: parseFloat(document.getElementById('filter-salary').value) || null,
            language: "PT-BR"
        },
        authConfig: authConfig,
        maxJobsPerRun: parseInt(document.getElementById('max-jobs').value)
    };
    
    try {
        let response;
        
        if (currentProfileId) {
            // Update existing
            response = await fetch(`${API_BASE}/profiles/${currentProfileId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });
        } else {
            // Create new
            response = await fetch(`${API_BASE}/profiles`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });
        }
        
        if (!response.ok) {
            throw new Error('Failed to save profile');
        }
        
        const result = await response.json();
        console.log('Profile saved:', result);
        
        alert('✅ Profile saved successfully!');
        cancelForm();
        loadProfiles();
        
    } catch (error) {
        console.error('Error saving profile:', error);
        alert(`Error: ${error.message}`);
    }
}

function getLocationData() {
    const city = document.getElementById('location-city').value.trim();
    const state = document.getElementById('location-state').value.trim().toUpperCase();
    const country = document.getElementById('location-country').value;
    const remote = document.getElementById('location-remote').checked;
    
    // ALWAYS return location with country (never null)
    return {
        city: city || null,
        state: state || null,
        country: country || "Brazil",  // Default Brazil
        remote: remote
    };
}

// ==================== TECH STACK INPUT ====================

function handleStackInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        
        const input = event.target;
        const tech = input.value.trim();
        
        if (tech && !techStack.includes(tech)) {
            techStack.push(tech);
            renderStackTags();
            input.value = '';
        }
    }
}

function removeStack(tech) {
    techStack = techStack.filter(t => t !== tech);
    renderStackTags();
}

function renderStackTags() {
    const container = document.getElementById('stack-tags');
    container.innerHTML = '';
    
    techStack.forEach(tech => {
        const tag = document.createElement('div');
        tag.className = 'stack-tag';
        tag.innerHTML = `
            ${tech}
            <button type="button" onclick="removeStack('${tech}')">×</button>
        `;
        container.appendChild(tag);
    });
}

// ==================== SLIDER ====================

function updateJobsLabel(value) {
    document.getElementById('jobs-label').textContent = value;
}

// ==================== LOAD PROFILES ====================

async function loadProfiles() {
    try {
        const response = await fetch(`${API_BASE}/profiles`);
        const profiles = await response.json();
        
        displayProfiles(profiles);
        document.getElementById('profiles-count').textContent = `${profiles.length} profile${profiles.length !== 1 ? 's' : ''}`;
        
    } catch (error) {
        console.error('Error loading profiles:', error);
    }
}

function displayProfiles(profiles) {
    const container = document.getElementById('profiles-list');
    
    if (profiles.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📭 No search profiles yet</p>
                <p class="hint">Create your first automated search profile</p>
                <button class="btn btn-primary" onclick="showCreateForm()">
                    ➕ Create Profile
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    profiles.forEach(profile => {
        const card = createProfileCard(profile);
        container.appendChild(card);
    });
}

function createProfileCard(profile) {
    const card = document.createElement('div');
    card.className = 'profile-card';
    
    // Filters preview
    const filters = profile.filters;
    let filtersHTML = '';
    
    if (filters.title) {
        filtersHTML += `<div class="filter-item"><strong>Title:</strong> ${filters.title}</div>`;
    }
    if (filters.seniority) {
        filtersHTML += `<div class="filter-item"><strong>Seniority:</strong> ${filters.seniority}</div>`;
    }
    if (filters.modality) {
        filtersHTML += `<div class="filter-item"><strong>Modality:</strong> ${filters.modality}</div>`;
    }
    if (filters.location && (filters.location.city || filters.location.remote)) {
        const loc = filters.location.remote ? 'Remote' : `${filters.location.city || ''}, ${filters.location.state || ''}`.trim();
        filtersHTML += `<div class="filter-item"><strong>Location:</strong> ${loc}</div>`;
    }
    if (filters.minSalary) {
        filtersHTML += `<div class="filter-item"><strong>Min Salary:</strong> R$ ${filters.minSalary.toLocaleString()}/month</div>`;
    }
    
    // Auth indicator
    if (profile.authConfig && profile.authConfig.useCustomAuth) {
        filtersHTML += `<div class="filter-item"><strong>🔒 Auth:</strong> Custom Credentials</div>`;
    }
    
    // Stack tags
    let stackHTML = '';
    if (filters.stack && filters.stack.length > 0) {
        stackHTML = filters.stack.map(tech => 
            `<span class="stack-tag">${tech}</span>`
        ).join('');
    }
    
    card.innerHTML = `
        <div class="profile-card-header">
            <h3>${profile.name}</h3>
        </div>
        
        ${filtersHTML ? `<div class="profile-filters">${filtersHTML}</div>` : ''}
        
        ${stackHTML ? `
            <div class="profile-stack">
                ${stackHTML}
            </div>
        ` : ''}
        
        <div class="profile-actions">
            <button class="btn btn-run" onclick="runSearch('${profile.id}', '${profile.name}')">
                ▶️ Run Now
            </button>
            <button class="btn btn-secondary" onclick="editProfile('${profile.id}')">
                ✏️ Edit
            </button>
            <button class="btn btn-danger" onclick="deleteProfile('${profile.id}')">
                🗑️ Delete
            </button>
        </div>
    `;
    
    return card;
}

// ==================== PROFILE ACTIONS ====================

async function editProfile(profileId) {
    try {
        const response = await fetch(`${API_BASE}/profiles/${profileId}`);
        const profile = await response.json();
        
        // Populate form
        currentProfileId = profileId;
        document.getElementById('form-title').textContent = 'Edit Search Profile';
        document.getElementById('profile-id').value = profileId;
        document.getElementById('profile-name').value = profile.name;
        
        // Filters
        document.getElementById('filter-title').value = profile.filters.title || '';
        
        // Seniority
        if (profile.filters.seniority) {
            const radio = document.querySelector(`input[name="seniority"][value="${profile.filters.seniority}"]`);
            if (radio) radio.checked = true;
        }
        
        // Stack
        techStack = profile.filters.stack || [];
        renderStackTags();
        
        // Modality
        document.getElementById('filter-modality').value = profile.filters.modality || '';
        
        // Location
        if (profile.filters.location) {
            document.getElementById('location-city').value = profile.filters.location.city || '';
            document.getElementById('location-state').value = profile.filters.location.state || '';
            document.getElementById('location-country').value = profile.filters.location.country || 'Brazil';
            document.getElementById('location-remote').checked = profile.filters.location.remote || false;
        }
        
        // Salary
        document.getElementById('filter-salary').value = profile.filters.minSalary || '';
        
        // Auth Config
        if (profile.authConfig && profile.authConfig.useCustomAuth) {
            document.getElementById('auth-use-custom').checked = true;
            document.getElementById('auth-linkedin-email').value = profile.authConfig.linkedinEmail || '';
            document.getElementById('auth-linkedin-password').value = profile.authConfig.linkedinPassword || '';
        } else {
            document.getElementById('auth-use-custom').checked = false;
            document.getElementById('auth-linkedin-email').value = '';
            document.getElementById('auth-linkedin-password').value = '';
        }
        toggleAuthFields();
        
        // Max jobs
        document.getElementById('max-jobs').value = profile.maxJobsPerRun;
        updateJobsLabel(profile.maxJobsPerRun);
        
        // Show form
        document.getElementById('form-section').classList.remove('hidden');
        document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error loading profile:', error);
        alert('Failed to load profile');
    }
}

async function deleteProfile(profileId) {
    if (!confirm('Are you sure you want to delete this profile?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/profiles/${profileId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('✅ Profile deleted');
            loadProfiles();
        }
        
    } catch (error) {
        console.error('Error deleting profile:', error);
        alert('Failed to delete profile');
    }
}

// ==================== SEARCH EXECUTION ====================

async function runSearch(profileId, profileName) {
    // Show modal
    document.getElementById('search-profile-name').textContent = profileName;
    document.getElementById('search-modal').classList.remove('hidden');
    document.getElementById('search-status').textContent = 'Starting search...';
    document.getElementById('progress-fill').style.width = '10%';
    
    // Reset stats
    document.getElementById('stat-found').textContent = '0';
    document.getElementById('stat-new').textContent = '0';
    document.getElementById('stat-failed').textContent = '0';
    
    try {
        const response = await fetch(`${API_BASE}/search/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profileId: profileId,
                sources: ['linkedin', 'gupy', 'indeed', 'glassdoor', 'catho']
            })
        });
        
        if (!response.ok) {
            throw new Error('Search failed');
        }
        
        const run = await response.json();
        
        // Update progress
        document.getElementById('progress-fill').style.width = '100%';
        document.getElementById('search-status').textContent = 'Search completed!';
        
        // Update stats
        document.getElementById('stat-found').textContent = run.stats.jobsFound;
        document.getElementById('stat-new').textContent = run.stats.jobsNew;
        document.getElementById('stat-failed').textContent = run.stats.jobsFailed;
        
        console.log('Search completed:', run);
        
    } catch (error) {
        console.error('Error running search:', error);
        document.getElementById('search-status').textContent = `Error: ${error.message}`;
        document.getElementById('progress-fill').style.width = '100%';
        document.getElementById('progress-fill').style.background = '#ef4444';
    }
}

function closeSearchModal() {
    document.getElementById('search-modal').classList.add('hidden');
    
    // Reload profiles to show updated "last run" info
    loadProfiles();
}
