/*
 * Ponto de entrada do front-end.
 *
 * O HTML usa atributos onclick="nomeDaFuncao(...)" em vários lugares (ex:
 * <button onclick="logout()">). Isso só funciona se a função existir no
 * escopo GLOBAL do navegador — mas funções dentro de um módulo ES (import/
 * export) NÃO são globais por padrão, ficam isoladas dentro do módulo.
 *
 * Por isso, este arquivo importa tudo que os outros módulos exportam, e
 * "pluga" explicitamente em `window` só as funções que o HTML realmente
 * chama via onclick/onsubmit/onchange — o resto continua só circulando
 * entre os módulos via import/export, do jeito normal.
 */
import { applyAccessibilityPreferences, changeFontSize, toggleHighContrast, toggleDyslexiaFont, toggleLineSpacing, resetAccessibility, toggleAccessibilityPanel } from './accessibility.js';
import { closeSuccessBanner } from './ui.js';
import { restoreSession, toggleTheme, handleLogin, logout, switchTab } from './auth.js';
import { checkLaudo, checkIrmao, handleFormSubmit, closeReceipt, showReceiptById, renderVagas, filterTable, editStudent, cancelEdit, deleteStudent, formatCPF, formatCNPJ, formatCEP, formatTelefone, toggleOtherField } from './students.js';
import { clearHistory } from './history.js';
import { addReminder, toggleReminder, deleteReminder, clearCompletedReminders, toggleCompletedReminders } from './reminders.js';
import { handleCreateUser, editUser, cancelUserEdit, apagarUsuario } from './users.js';

function initEvents() {
    // O <form id="studentForm"> já dispara handleFormSubmit via atributo onsubmit no HTML.
    // NÃO registrar addEventListener aqui também — isso fazia o formulário ser enviado
    // duas vezes a cada clique em "Salvar", duplicando o cadastro no banco de dados.

    const totalVagasInput = document.getElementById('totalVagasInput');
    if (totalVagasInput) totalVagasInput.addEventListener('input', renderVagas);

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
    formatCPF, formatCNPJ, formatCEP, formatTelefone, toggleOtherField,
    // histórico
    clearHistory,
    // lembretes
    addReminder, toggleReminder, deleteReminder, clearCompletedReminders, toggleCompletedReminders,
    // usuários (painel admin)
    handleCreateUser, editUser, cancelUserEdit, apagarUsuario,
});