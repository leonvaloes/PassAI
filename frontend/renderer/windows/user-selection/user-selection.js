const API_URL = 'http://localhost:8000/api/users';

const geekQuotes = [
    "Invocando o Jarvis...",
    "Carregando chunks do mapa...",
    "Defusando a bomba no B...",
    "Aguardando o Bat-Sinal...",
    "Reunindo as Joias do Infinito...",
    "Calculando a resposta para a vida, o universo e tudo mais... 42",
    "Sintonizando a Força...",
    "Atualizando drivers da NVIDIA...",
    "Procurando o One Piece...",
    "Esperando o Goku carregar o Ki...",
    "Estabelecendo conexão via matrix...",
      "Compilando bits mágicos...",
    "Invocando o Mestre Yoda para conselhos...",
    "Sincronizando com o multiverso...",
    "Carregando shaders ultra-realistas...",
    "Alocando mais RAM do que o necessário...",
    "Verificando se está na linha do tempo correta...",
    "Aguardando respawn...",
    "Desfragmentando pensamentos...",
    "Consultando o oráculo de Stack Overflow...",
    "Recarregando a mana...",
    "Inicializando protocolo Skynet (brincadeira 👀)...",
    "Aguardando o upload da consciência...",
    "Calculando pathfinding do personagem...",
    "Carregando DLCs não compradas...",
    "Executando rollback no tempo...",
    "Conectando aos servidores da Matrix...",
    "Treinando IA para fingir que sabe tudo...",
    "Aguardando sincronização com o servidor mestre...",
    "Convertendo café em código...",
    "Carregando saves corrompidos...",
    "Rodando em modo hardcore...",
    "Desbloqueando achievements secretos...",
    "Esperando o lag desaparecer...",
    "Compilando bugs conhecidos...",
    "Aplicando hotfix improvisado...",
    "Buscando Wi-Fi em outra dimensão...",
    "Ajustando dificuldade para 'Insano'...",
    "Inicializando modo Deus...",
    "Carregando NPCs aleatórios...",
    "Reescrevendo a realidade em JavaScript...",
    "Aguardando aprovação do deploy em produção...",
    "Consultando logs do universo...",
    "Sincronizando com o servidor do além...",
    "Renderizando pixels com amor...",
    "Esperando o café fazer efeito..."
];

let quoteInterval;

document.addEventListener('DOMContentLoaded', startLoading);

function showRandomQuote() {
    const list = document.getElementById('users-list');
    const quote = geekQuotes[Math.floor(Math.random() * geekQuotes.length)];
    list.innerHTML = `
        <div class="loading-container">
            <div class="spinner"></div>
            <div class="geek-quote fade-in">${quote}</div>
            <div class="sub-text">Aguardando o servidor...</div>
        </div>
    `;
}

async function startLoading() {
    showRandomQuote();
    // Rotate quotes every 3 seconds
    quoteInterval = setInterval(showRandomQuote, 3000);
    connectWithRetry();
}

async function connectWithRetry() {
    let data;
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Server not ready');
        data = await response.json();
    } catch (error) {
        // Retry after 2 seconds
        setTimeout(connectWithRetry, 2000);
        return;
    }
    
    // Success: stop loading loop
    clearInterval(quoteInterval);
    
    try {
        // The API returns { users: [...], total: N, ... }
        // We need to extract the array
        const userList = Array.isArray(data) ? data : (data.users || []);
        
        renderUsers(userList);
    } catch (renderError) {
        console.error('Render error:', renderError);
        document.getElementById('users-list').innerHTML = `
            <div style="color:#ef4444; margin-top: 20px;">
                Erro ao exibir usuários.<br>
                <small>${renderError.message}</small>
            </div>
        `;
    }
}

function renderUsers(users) {
    const list = document.getElementById('users-list');
    
    if (users.length === 0) {
        list.innerHTML = '<div style="color:#64748b">Nenhum usuário encontrado.</div>';
        return;
    }

    list.innerHTML = users.map(user => {
        const displayName = user.nome || user.profile_name || 'Usuário Desconhecido';
        return `
        <div class="user-item" onclick="selectUser('${user.id}')">
            <div class="avatar">${getInitials(displayName)}</div>
            <div class="name">${displayName.split(' ')[0]}</div>
        </div>
        `;
    }).join('');
}

function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

async function selectUser(userId) {
    try {
        // Show loading state visually if needed, but it should be fast
        document.body.style.cursor = 'wait';
        
        // 1. Set active user in backend
        await fetch(`${API_URL}/active/set`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        
        // 2. Notify main process to launch the app
        window.electronAPI.send('user-selected-launch');
        
    } catch (err) {
        console.error('Error selecting user:', err);
        document.body.style.cursor = 'default';
        alert('Erro ao selecionar usuário');
    }
}

document.getElementById('manage-btn').addEventListener('click', () => {
    // Send request to open the advanced management window
    window.electronAPI.send('open-user-manager-setup');
});
