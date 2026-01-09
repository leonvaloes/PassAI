// User Management JavaScript
const API_BASE = 'http://localhost:8000/api/users';

let users = [];
let activeUserId = null;
let editingUserId = null;

// DOM Elements
const usersGrid = document.getElementById('users-grid');
const userModal = document.getElementById('user-modal');
const userForm = document.getElementById('user-form');
const addUserBtn = document.getElementById('add-user-btn');
const closeModalBtn = document.getElementById('close-modal');
const cancelBtn = document.getElementById('cancel-btn');
const modalTitle = document.getElementById('modal-title');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    setupEventListeners();
    setupDynamicListListeners();
});

function setupEventListeners() {
    if (addUserBtn) addUserBtn.addEventListener('click', () => openModal());
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (userForm) userForm.addEventListener('submit', handleSubmit);
    
    // AI extraction
    const toggleAIBtn = document.getElementById('toggle-ai-btn');
    const extractAIBtn = document.getElementById('extract-ai-btn');
    
    if (toggleAIBtn) {
        toggleAIBtn.addEventListener('click', toggleAIPanel);
    } else {
        console.warn('Toggle AI button not found');
    }
    
    if (extractAIBtn) {
        extractAIBtn.addEventListener('click', extractWithAI);
    }
    
    // Close modal on outside click
    if (userModal) {
        userModal.addEventListener('click', (e) => {
            if (e.target === userModal) closeModal();
        });
    }
}

// Load all users
async function loadUsers() {
    try {
        const response = await fetch(API_BASE);
        const data = await response.json();
        
        users = data.users;
        activeUserId = data.active_user_id;
        
        renderUsers();
    } catch (error) {
        console.error('Failed to load users:', error);
        usersGrid.innerHTML = '<div class="loading">Erro ao carregar usuários</div>';
    }
}

// Render users grid
// Render users grid
function renderUsers() {
    if (users.length === 0) {
        usersGrid.innerHTML = '<div class="loading">Nenhum usuário cadastrado. Clique em "Adicionar Usuário" para começar.</div>';
        return;
    }
    
    usersGrid.innerHTML = users.map(user => `
        <div class="user-card ${user.id === activeUserId ? 'active' : ''}" 
             onclick="handleCardClick(event, '${user.id}')"
             title="${user.id === activeUserId ? 'Voltar para o Painel' : 'Selecionar este usuário'}"
        >
            ${user.id === activeUserId ? '<span class="active-badge">✓ Ativo</span>' : ''}
            
            <button class="card-menu-btn" onclick="toggleUserMenu(event, '${user.id}')" title="Opções">⋮</button>
            <div id="menu-${user.id}" class="card-dropdown">
                <button class="menu-item" onclick="handleMenuAction(event, 'edit', '${user.id}')">
                    ✏️ Editar Perfil
                </button>
                <button class="menu-item delete" onclick="handleMenuAction(event, 'delete', '${user.id}')">
                    🗑️ Excluir
                </button>
            </div>

            <div class="user-name">${user.nome}</div>
            <div class="user-email">${user.email}</div>
            
            <div style="font-size: 0.875rem; color: var(--text-muted); margin: 0.5rem 0;">
                <div><strong>Cargo:</strong> ${user.cargo_atual}</div>
                <div><strong>Local:</strong> ${user.cidade}, ${user.estado}</div>
            </div>
        </div>
    `).join('');
}

// Interaction Handlers
function toggleUserMenu(e, userId) {
    e.stopPropagation();
    const menu = document.getElementById(`menu-${userId}`);
    const isHidden = !menu.classList.contains('show');
    
    // Close all others
    document.querySelectorAll('.card-dropdown').forEach(el => el.classList.remove('show'));
    
    if (isHidden) {
        menu.classList.add('show');
    }
}

async function handleCardClick(e, userId) {
    // Check if clicked on menu
    if (e.target.closest('.card-menu-btn') || e.target.closest('.card-dropdown')) return;
    
    try {
        if (userId !== activeUserId) {
            await setActiveUser(userId);
        }
        
        // Navigate to main dashboard (HUD)
        window.location.href = '../../index.html';
    } catch (error) {
        console.error('Navigation error:', error);
    }
}

function handleMenuAction(e, action, userId) {
    e.stopPropagation();
    // Close menu
    document.querySelectorAll('.card-dropdown').forEach(el => el.classList.remove('show'));
    
    if (action === 'edit') {
        editUser(userId);
    } else if (action === 'delete') {
        const user = users.find(u => u.id === userId);
        deleteUser(userId, user ? user.nome : 'Usuário');
    }
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.card-menu-btn')) {
        document.querySelectorAll('.card-dropdown').forEach(el => el.classList.remove('show'));
    }
});

// Open modal (add or edit)
function openModal(user = null) {
    editingUserId = user?.id || null;
    modalTitle.textContent = user ? 'Editar Usuário' : 'Adicionar Usuário';
    
    if (user) {
        // Fill form with user data
        document.getElementById('user-id').value = user.id;
        document.getElementById('profile-name').value = user.profile_name;
        document.getElementById('nome').value = user.nome;
        document.getElementById('cargo-atual').value = user.cargo_atual;
        document.getElementById('email').value = user.email;
        document.getElementById('telefone').value = user.telefone;
        document.getElementById('linkedin').value = user.linkedin;
        document.getElementById('github').value = user.github || '';
        document.getElementById('cidade').value = user.cidade;
        document.getElementById('estado').value = user.estado;
        
        // Populate dynamic lists
        clearDynamicLists();
        (user.experiencias || []).forEach(exp => addExperienceItem(exp));
        (user.educacao || []).forEach(edu => addEducationItem(edu));
        (user.habilidades || []).forEach(skill => addSkillItem(skill));
        (user.idiomas || []).forEach(lang => addLanguageItem(lang));
        
    } else {
        modalTitle.textContent = 'Novo Perfil';
        submitBtn.textContent = 'Criar Perfil';
        clearDynamicLists();
    }
    
    // Reset AI input and status
    const aiStatus = document.getElementById('ai-status');
    if (aiStatus) {
        aiStatus.className = 'ai-status hidden';
        aiStatus.textContent = '';
    }
    document.getElementById('ai-input').value = '';
    
    userModal.classList.remove('hidden');
}

function closeModal() {
    userModal.classList.add('hidden');
    userForm.reset();
    editingUserId = null;
}

// Handle form submit
async function handleSubmit(e) {
    e.preventDefault();
    
    const formData = {
        profile_name: document.getElementById('profile-name').value.toLowerCase().trim(),
        nome: document.getElementById('nome').value.trim(),
        cargo_atual: document.getElementById('cargo-atual').value.trim(),
        email: document.getElementById('email').value.trim(),
        telefone: document.getElementById('telefone').value.trim(),
        linkedin: document.getElementById('linkedin').value.trim(),
        github: document.getElementById('github').value.trim() || null,
        cidade: document.getElementById('cidade').value.trim(),
        estado: document.getElementById('estado').value.trim(),
        
        // Collect data from dynamic lists
        experiencias: Array.from(document.querySelectorAll('#experiences-list .dynamic-item')).map(item => ({
            empresa: item.querySelector('.exp-empresa').value.trim(),
            cargo: item.querySelector('.exp-cargo').value.trim(),
            periodo: item.querySelector('.exp-periodo').value.trim(),
            descricao: item.querySelector('.exp-descricao').value.trim()
        })),
        educacao: Array.from(document.querySelectorAll('#education-list .dynamic-item')).map(item => ({
            instituicao: item.querySelector('.edu-instituicao').value.trim(),
            curso: item.querySelector('.edu-curso').value.trim(),
            periodo: item.querySelector('.edu-periodo').value.trim()
        })),
        habilidades: Array.from(document.querySelectorAll('#skills-list .skill-name')).map(span => span.textContent),
        idiomas: Array.from(document.querySelectorAll('#languages-list .dynamic-item')).map(item => ({
            idioma: item.querySelector('.lang-idioma').value.trim(),
            nivel: item.querySelector('.lang-nivel').value.trim()
        }))
    };
    
    try {
        let response;
        
        if (editingUserId) {
            // Update existing user
            response = await fetch(`${API_BASE}/${editingUserId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
        } else {
            // Create new user
            response = await fetch(API_BASE, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao salvar usuário');
        }
        
        closeModal();
        await loadUsers();
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Set active user
async function setActiveUser(userId) {
    try {
        const response = await fetch(`${API_BASE}/active/set`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId})
        });
        
        if (!response.ok) throw new Error('Erro ao ativar usuário');
        
        await loadUsers();
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Edit user
function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (user) openModal(user);
}

// Event Listeners for Dynamic Lists
// Event Listeners for Dynamic Lists
function setupDynamicListListeners() {
    const addExpBtn = document.getElementById('add-exp-btn');
    const addEduBtn = document.getElementById('add-edu-btn');
    const addLangBtn = document.getElementById('add-lang-btn');
    const addSkillBtn = document.getElementById('add-skill-btn');

    if (addExpBtn) addExpBtn.addEventListener('click', () => addExperienceItem());
    if (addEduBtn) addEduBtn.addEventListener('click', () => addEducationItem());
    if (addLangBtn) addLangBtn.addEventListener('click', () => addLanguageItem());
    
    if (addSkillBtn) {
        addSkillBtn.addEventListener('click', () => {
            const input = document.getElementById('new-skill-input');
            if (input && input.value.trim()) {
                addSkillItem(input.value.trim());
                input.value = '';
            }
        });
    }

    // Remove buttons delegation
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-btn')) {
            e.target.closest('.dynamic-item').remove();
        }
        if (e.target.classList.contains('skill-remove')) {
            e.target.closest('.skill-tag').remove();
        }
    });
}

function addExperienceItem(data = null) {
    const template = document.getElementById('exp-template');
    const clone = template.content.cloneNode(true);
    
    if (data) {
        clone.querySelector('.exp-empresa').value = data.empresa || '';
        clone.querySelector('.exp-cargo').value = data.cargo || '';
        clone.querySelector('.exp-periodo').value = data.periodo || '';
        clone.querySelector('.exp-descricao').value = data.descricao || '';
    }
    
    document.getElementById('experiences-list').appendChild(clone);
}

function addEducationItem(data = null) {
    const template = document.getElementById('edu-template');
    const clone = template.content.cloneNode(true);
    
    if (data) {
        clone.querySelector('.edu-instituicao').value = data.instituicao || '';
        clone.querySelector('.edu-curso').value = data.curso || '';
        clone.querySelector('.edu-periodo').value = data.periodo || '';
    }
    
    document.getElementById('education-list').appendChild(clone);
}

function addLanguageItem(data = null) {
    const template = document.getElementById('lang-template');
    const clone = template.content.cloneNode(true);
    
    if (data) {
        clone.querySelector('.lang-idioma').value = data.idioma || '';
        clone.querySelector('.lang-nivel').value = data.nivel || '';
    }
    
    document.getElementById('languages-list').appendChild(clone);
}

function addSkillItem(skill) {
    const container = document.getElementById('skills-list');
    const skillTag = document.createElement('div');
    skillTag.className = 'skill-tag';
    skillTag.innerHTML = `
        <span class="skill-name">${skill}</span>
        <span class="skill-remove">&times;</span>
    `;
    container.appendChild(skillTag);
}

function clearDynamicLists() {
    document.getElementById('experiences-list').innerHTML = '';
    document.getElementById('education-list').innerHTML = '';
    document.getElementById('skills-list').innerHTML = '';
    document.getElementById('languages-list').innerHTML = '';
}

// Delete user
async function deleteUser(userId, userName) {
    if (!confirm(`Tem certeza que deseja excluir o usuário "${userName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/${userId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Erro ao excluir usuário');
        
        await loadUsers();
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// AI Profile Fill Functions
function toggleAIPanel() {
    console.log('Toggling AI Panel');
    const aiPanel = document.getElementById('ai-panel');
    const toggleBtn = document.getElementById('toggle-ai-btn');
    
    if (aiPanel.classList.contains('hidden')) {
        aiPanel.classList.remove('hidden');
        toggleBtn.textContent = 'Recolher';
    } else {
        aiPanel.classList.add('hidden');
        toggleBtn.textContent = 'Expandir';
    }
}

async function extractWithAI() {
    const aiInput = document.getElementById('ai-input');
    const statusDiv = document.getElementById('ai-status');
    const extractBtn = document.getElementById('extract-ai-btn');
    
    const text = aiInput.value.trim();
    if (!text) {
        statusDiv.className = 'ai-status error';
        statusDiv.textContent = '⚠️ Por favor, insira algum texto para extrair';
        return;
    }
    
    // Show loading
    statusDiv.className = 'ai-status loading';
    statusDiv.textContent = '🤖 Analisando com IA...';
    extractBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/ai-extract`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro na extração');
        }
        
        const data = await response.json();
        
        // Populate dynamic lists with AI data
        clearDynamicLists(); // Clear existing to avoid duplicates or keep? Thinking clear is better for "Fill" action
        
        if (data.experiencias) data.experiencias.forEach(exp => addExperienceItem(exp));
        if (data.educacao) data.educacao.forEach(edu => addEducationItem(edu));
        if (data.habilidades) data.habilidades.forEach(skill => addSkillItem(skill));
        if (data.idiomas) data.idiomas.forEach(lang => addLanguageItem(lang));

        statusDiv.className = 'ai-status success';
        statusDiv.innerHTML = `
            ✅ <strong>Dados extraídos e preenchidos!</strong><br>
            📄 ${data.experiencias.length} experiências<br>
            🎓 ${data.educacao.length} formações<br>
            ⚡ ${data.habilidades.length} habilidades<br>
            <small>Revise os campos abaixo e edite se necessário.</small>
        `;
        
        console.log('AI data populated to form');
        
    } catch (error) {
        console.error('AI Error:', error);
        statusDiv.className = 'ai-status error';
        statusDiv.textContent = `❌ ${error.message || 'Erro ao extrair dados. Tente novamente.'}`;
    } finally {
        // Re-enable button
        extractBtn.disabled = false;
        extractBtn.innerHTML = '🤖 Extrair Dados';
    }
}
