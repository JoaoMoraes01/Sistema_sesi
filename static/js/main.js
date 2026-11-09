/*
 * Ponto de entrada do front-end.
 *
 * O HTML usa atributos onclick="nomeDaFuncao(...)" em vários lugares. Isso
 * só funciona se a função existir no escopo GLOBAL do navegador — por isso
 * importamos tudo e "plugamos" em `window` as funções que o HTML chama
 * via onclick/onsubmit/onchange.
 */
import { applyAccessibilityPreferences, changeFontSize, toggleHighContrast, toggleDyslexiaFont, toggleLineSpacing, resetAccessibility, toggleAccessibilityPanel } from './accessibility.js?v=15';
import { closeSuccessBanner } from './ui.js?v=15';
import { restoreSession, toggleTheme, handleLogin, logout, switchTab } from './auth.js?v=15';
import { checkLaudo, checkIrmao, handleFormSubmit, closeReceipt, showReceiptById, renderVagas, filterTable, editStudent, cancelEdit, deleteStudent, formatCPF, formatCNPJ, formatCEP, formatTelefone, formatRG, onlyLetters, toggleOtherField } from './students.js?v=15';
import { clearHistory } from './history.js?v=15';
import { addReminder, toggleReminder, deleteReminder, clearCompletedReminders, toggleCompletedReminders } from './reminders.js?v=15';
import { handleCreateUser, editUser, cancelUserEdit, apagarUsuario } from './users.js?v=15';

function initEvents() {
    // Nota: <form id="studentForm"> já dispara handleFormSubmit via atributo
    // onsubmit no HTML. NÃO registrar addEventListener aqui também — isso
    // fazia o formulário ser enviado duas vezes a cada clique em "Salvar".
    //
    // Mesma regra para #totalVagasInput: ele já tem oninput="renderVagas()"
    // no HTML. Antes, adicionávamos também um addEventListener aqui — o que
    // resultava em DUAS chamadas de renderVagas por tecla digitada
    // (dois fetches completos a cada digitação). Removido.

    const btnTheme = document.querySelector('.btn-theme');
    if (btnTheme) {
        btnTheme.addEventListener('click', toggleTheme);
    }

    document.addEventListener('click', (event) => {
        const panel = document.getElementById('accessibilityPanel');
        const toggleBtn = document.getElementById('accessibilityToggle');
        if (!panel || !panel.classList.contains('open')) return;
        if (!panel.contains(event.target) && event.target !== toggleBtn) {
            panel.classList.remove('open');
        }
    });

    // --- MENU MOBILE ---
    document.querySelectorAll('.sidebar .nav-link, .sidebar .btn-logout').forEach((el) => {
        el.addEventListener('click', () => {
            if (window.matchMedia('(max-width: 900px)').matches) {
                document.querySelector('.sidebar')?.classList.remove('open');
            }
        });
    });

    document.addEventListener('click', (event) => {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.querySelector('.btn-menu');
        if (!sidebar || !sidebar.classList.contains('open')) return;
        if (!sidebar.contains(event.target) && event.target !== menuBtn) {
            sidebar.classList.remove('open');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }
    applyAccessibilityPreferences();
    initEvents();
    checkLaudo();
    restoreSession();
});

// --- Funções chamadas via onclick/onsubmit/onchange no HTML (precisam ser globais) ---
Object.assign(window, {
    // acessibilidade
    changeFontSize, toggleHighContrast, toggleDyslexiaFont, toggleLineSpacing, resetAccessibility, toggleAccessibilityPanel,
    // notificações
    closeSuccessBanner,
    // login / navegação
    handleLogin, logout, switchTab,
    // alunos
    checkLaudo, checkIrmao, handleFormSubmit, closeReceipt, showReceiptById, renderVagas, filterTable, editStudent, cancelEdit, deleteStudent,
    formatCPF, formatCNPJ, formatCEP, formatTelefone, formatRG, onlyLetters, toggleOtherField,
    // histórico
    clearHistory,
    // lembretes
    addReminder, toggleReminder, deleteReminder, clearCompletedReminders, toggleCompletedReminders,
    // usuários (painel admin)
    handleCreateUser, editUser, cancelUserEdit, apagarUsuario,
});
