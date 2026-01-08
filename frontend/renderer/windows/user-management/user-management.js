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
});

function setupEventListeners() {
    addUserBtn.addEventListener('click', () => openModal());
    closeModalBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    userForm.addEventListener('submit', handleSubmit);
    
    // AI extraction
    const toggleAIBtn = document.getElementById('toggle-ai-btn');
    const extractAIBtn = document.getElementById('extract-ai-btn');
    
    if (toggleAIBtn) {
        toggleAIBtn.addEventListener('click', toggleAIPanel);
    }
    if (extractAIBtn) {
        extractAIBtn.addEventListener('click', extractWithAI);
    }
    
    // Close modal on outside click
    userModal.addEventListener('click', (e) => {
        if (e.target === userModal) closeModal();
    });
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
function renderUsers() {
    if (users.length === 0) {
        usersGrid.innerHTML = '<div class="loading">Nenhum usuário cadastrado</div>';
        return;
    }
    
    usersGrid.innerHTML = users.map(user => `
        <div class="user-card ${user.id === activeUserId ? 'active' : ''}">
            ${user.id === activeUserId ? '<span class="active-badge">✓ Ativo</span>' : ''}
            
            <div class="user-name">${user.nome}</div>
            <div class="user-email">${user.email}</div>
            
            <div style="font-size: 0.875rem; color: var(--text-muted); margin: 0.5rem 0;">
                <div><strong>Cargo:</strong> ${user.cargo_atual}</div>
                <div><strong>Local:</strong> ${user.cidade}, ${user.estado}</div>
            </div>
            
            <div class="user-actions">
                ${user.id !== activeUserId ? `
                    <button class="btn-primary" onclick="setActiveUser('${user.id}')">
                        Ativar
                    </button>
                ` : '<div style="flex:1"></div>'}
                <button class="btn-secondary" onclick="editUser('${user.id}')">
                    Editar
                </button>
                <button class="btn-danger" onclick="deleteUser('${user.id}', '${user.nome}')">
                    Excluir
                </button>
            </div>
        </div>
    `).join('');
}

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
    } else {
        userForm.reset();
    }
    
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
        experiencias: [],
        educacao: [],
        habilidades: [],
        idiomas: []
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
        
        // Auto-fill would go here  (experiencias, educacao, habilidades)
        // For now, just show success since we only have basic fields in form
        statusDiv.className = 'ai-status success';
        statusDiv.textContent = `✅ ${data.message || 'Dados extraídos com sucesso!'}`;
       statusDiv.textContent += `\n📊 ${data.experiencias.length} exp, ${data.educacao.length} edu, ${data.habilidades.length} skills`;
        
        console.log('Extracted data:', data);
        
    } catch (error) {
        statusDiv.className = 'ai-status error';
        statusDiv.textContent = `❌ ${error.message}`;
    } finally {
        extractBtn.disabled = false;
    }
}
