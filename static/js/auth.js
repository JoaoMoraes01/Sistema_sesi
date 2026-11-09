/*
 * Autenticação, sessão e navegação entre abas.
 *
 * Nota sobre os imports de students.js/reminders.js/history.js/users.js:
 * existe uma dependência "circular" entre este arquivo e alguns deles — isso
 * é seguro em módulos ES porque o uso acontece sempre DENTRO de uma função
 * (nunca executado no load do módulo), e essas funções só rodam depois de
 * um clique ou de um login.
 */
import { appState, API_URL } from './state.js?v=14';
import { renderVagas, filterTable, renderVagasTableOnly } from './students.js?v=14';
import { renderReminders } from './reminders.js?v=14';
import { renderHistory } from './history.js?v=14';
import { renderUsers } from './users.js?v=14';
import { showToast } from './ui.js?v=14';

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
            return;
        }
        enterApp(session);
    } catch (error) {
        console.error('Sessão salva inválida, removendo:', error);
        localStorage.removeItem(SESSION_KEY);
    }
}

// Lê a data de expiração do próprio token JWT, sem precisar perguntar ao servidor
function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return !payload.exp || (Date.now() / 1000) >= payload.exp;
    } catch (error) {
        return true;
    }
}

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

/**
 * Carrega tudo que a tela precisa ao entrar no sistema.
 *
 * Antes: fetches em série (`await` um após o outro) — 4 round-trips somados
 * no login de um admin. Agora: `Promise.all` dispara tudo em paralelo. Em
 * rede local cada request cai de ~50ms; em Wi-Fi de escola, a soma pode
 * economizar 1 segundo ou mais.
 */
async function renderAll() {
    const tarefas = [renderVagas(), renderReminders()];
    if (appState.currentUserRole === 'admin') {
        tarefas.push(renderHistory(), renderUsers());
    }
    await Promise.all(tarefas);
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
            data.token = data.access_token;

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

/**
 * Troca de aba. Re-renderiza do CACHE quando possível, em vez de refazer o
 * fetch pesado. Antes, cada clique em "Lista & Busca" ou "Vagas e Ocupação"
 * disparava `GET /api/students/queue` de novo — essa era a lentidão mais
 * percebida pelo usuário.
 */
function switchTab(event, tabId) {
    if (event) event.preventDefault();
    switchTabDirect(tabId);

    if (tabId === 'tab-lista') {
        // Re-renderiza a partir de appState.allStudents (já carregado no login/CRUD)
        filterTable(true);
    } else if (tabId === 'tab-vagas') {
        // Idem, mas na tabela de vagas
        renderVagasTableOnly();
    } else if (tabId === 'tab-lembretes') {
        renderReminders();
    } else if (tabId === 'tab-historico' && appState.currentUserRole === 'admin') {
        // Histórico e Admin são abas menos usadas — sempre frescos ao abrir.
        renderHistory();
    } else if (tabId === 'tab-admin' && appState.currentUserRole === 'admin') {
        renderUsers();
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
