/*
 * Autenticação, sessão e navegação entre abas.
 *
 * Nota sobre os imports de students.js/reminders.js/history.js/users.js:
 * existe uma dependência "circular" entre este arquivo e alguns deles
 * (ex: students.js importa `switchTabDirect` daqui, e aqui importamos
 * `renderVagas` de students.js). Isso é seguro em módulos ES desde que
 * o uso aconteça sempre DENTRO de uma função (nunca executado assim que
 * o módulo carrega) — que é exatamente o caso aqui: essas funções só
 * rodam depois de um clique ou de um login, bem depois de tudo já ter
 * sido carregado.
 */
import { appState, API_URL } from './state.js';
import { renderVagas } from './students.js';
import { renderReminders } from './reminders.js';
import { renderHistory } from './history.js';
import { renderUsers } from './users.js';
import { showToast } from './ui.js';

const SESSION_KEY = 'sesi_session';

function saveSession(data) {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
        username: data.username,
        role: data.role,
        name: data.name,
        token: data.access_token
    }));
}

function restoreSession() {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return;

    try {
        const session = JSON.parse(raw);
        if (!session.token || isTokenExpired(session.token)) {
            localStorage.removeItem(SESSION_KEY);
            return; // deixa a tela de login aparecer normalmente, sem sessão expirada
        }
        enterApp(session);
    } catch (error) {
        console.error('Sessão salva inválida, removendo:', error);
        localStorage.removeItem(SESSION_KEY);
    }
}

// Lê a data de expiração de dentro do próprio token (JWT), sem precisar perguntar
// ao servidor — evita reabrir a sessão sozinho com um token que já não serve mais.
function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return !payload.exp || (Date.now() / 1000) >= payload.exp;
    } catch (error) {
        return true; // token ilegível = trata como expirado, por segurança
    }
}

// Centraliza o que acontece ao "entrar" no sistema, seja por login novo ou por sessão restaurada
function enterApp(session) {
    appState.currentUserRole = session.role;
    appState.currentUserName = session.name || session.username;
    appState.currentUserLogin = session.username;
    appState.authToken = session.token;

    const loginOverlay = document.getElementById('loginOverlay');
    const appContainer = document.getElementById('appContainer');
    if (loginOverlay) loginOverlay.style.display = 'none';
    if (appContainer) appContainer.style.display = 'flex';

    const displayUserName = document.getElementById('displayUserName');
    if (displayUserName) {
        displayUserName.textContent = `Olá, ${session.username}!`;
    }

    applyRolePermissions();
    renderAll();
}

// Busca tudo que a tela precisa mostrar assim que a pessoa entra no sistema
async function renderAll() {
    await renderVagas(); // alimenta appState.allStudents + abas "Vagas" e "Lista & Busca" (esta última visível para ambos os papéis)
    await renderReminders(); // alimenta o badge de pendentes na barra lateral, visível para ambos os papéis
    if (appState.currentUserRole === 'admin') {
        await renderHistory();
        await renderUsers();
    }
}

function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

async function handleLogin(event) {
    event.preventDefault();

    const user = document.getElementById('loginUser').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    const loginError = document.getElementById('loginError');

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (response.ok) {
            const data = await response.json();
            data.token = data.access_token; // normaliza o nome do campo (a API devolve "access_token")

            if (loginError) loginError.style.display = 'none';
            saveSession(data);
            enterApp(data);
        } else if (response.status === 401) {
            if (loginError) {
                loginError.textContent = "Usuário ou senha incorretos.";
                loginError.style.display = 'block';
            }
        } else {
            if (loginError) {
                loginError.textContent = "Erro ao processar requisição no servidor.";
                loginError.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Erro de conexão:', error);
        if (loginError) {
            loginError.textContent = "Não foi possível conectar à API na porta 8000.";
            loginError.style.display = 'block';
        }
    }
}

// Confere se uma resposta veio com 401 (token expirado/inválido) e, se sim,
// desloga automaticamente em vez de deixar tudo travado sem explicação.
function handleAuthResponse(response) {
    if (response.status === 401) {
        showToast('Sua sessão expirou. Faça login novamente.', 'error');
        logout();
        return false;
    }
    return true;
}

function applyRolePermissions() {
    const navCadastro = document.getElementById('navCadastro');
    const navLista = document.getElementById('navLista');
    const navVagas = document.getElementById('navVagas');
    const navHistorico = document.getElementById('navHistorico');
    const navAdmin = document.getElementById('navAdmin');

    if (appState.currentUserRole === 'admin') {
        if (navCadastro) navCadastro.style.display = 'none';
        if (navVagas) navVagas.style.display = 'none';

        if (navLista) navLista.style.display = 'block';
        if (navHistorico) navHistorico.style.display = 'block';
        if (navAdmin) navAdmin.style.display = 'block';
        switchTabDirect('tab-admin');
    } else {
        if (navCadastro) navCadastro.style.display = 'block';
        if (navLista) navLista.style.display = 'block';
        if (navVagas) navVagas.style.display = 'block';

        if (navHistorico) navHistorico.style.display = 'none';
        if (navAdmin) navAdmin.style.display = 'none';
        switchTabDirect('tab-cadastro');
    }
}

function switchTabDirect(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));

    const activeTab = document.getElementById(tabId);
    if (activeTab) activeTab.classList.add('active');

    const activeNav = Array.from(navLinks).find(link => link.getAttribute('onclick')?.includes(tabId));
    if (activeNav) activeNav.classList.add('active');
}

function switchTab(event, tabId) {
    if (event) event.preventDefault();
    switchTabDirect(tabId);
    if (tabId === 'tab-lista' || tabId === 'tab-vagas') {
        renderVagas();
    }
    if (tabId === 'tab-lembretes') {
        renderReminders();
    }
}

function logout() {
    const loginOverlay = document.getElementById('loginOverlay');
    const appContainer = document.getElementById('appContainer');

    localStorage.removeItem(SESSION_KEY);
    appState.currentUserRole = '';
    appState.currentUserName = '';
    appState.currentUserLogin = '';
    appState.authToken = '';
    appState.allStudents = [];
    appState.allUsers = [];
    appState.allReminders = [];

    if (loginOverlay) loginOverlay.style.display = 'flex';
    if (appContainer) appContainer.style.display = 'none';
}

export {
    restoreSession,
    enterApp,
    renderAll,
    toggleTheme,
    handleLogin,
    handleAuthResponse,
    applyRolePermissions,
    switchTabDirect,
    switchTab,
    logout,
};