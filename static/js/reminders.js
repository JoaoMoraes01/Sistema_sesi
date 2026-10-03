/*
 * Lembretes: anotações pessoais do usuário logado (cada um só vê os seus).
 */
import { appState, API_URL, authHeaders, escapeHtml } from './state.js';
import { showToast, showConfirm, showSuccessBanner } from './ui.js';
import { handleAuthResponse } from './auth.js';

async function renderReminders() {
    try {
        const response = await fetch(`${API_URL}/reminders`, { headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (!response.ok) return;

        appState.allReminders = await response.json();

        const pending = appState.allReminders.filter((r) => !r.concluido);
        const completed = appState.allReminders.filter((r) => r.concluido);

        // Badge de pendentes na barra lateral
        const badge = document.getElementById('reminderBadge');
        if (badge) {
            if (pending.length > 0) {
                badge.textContent = pending.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }

        const pendingList = document.getElementById('reminderPendingList');
        if (pendingList) {
            pendingList.innerHTML = pending.length === 0
                ? '<p style="color: var(--text-muted);">Nenhum lembrete pendente. 🎉</p>'
                : pending.map((r) => renderReminderItem(r)).join('');
        }

        const completedList = document.getElementById('reminderCompletedList');
        if (completedList) {
            completedList.innerHTML = completed.length === 0
                ? '<p style="color: var(--text-muted);">Nenhum lembrete concluído ainda.</p>'
                : completed.map((r) => renderReminderItem(r)).join('');
        }
    } catch (error) {
        console.error('Erro ao carregar lembretes:', error);
    }
}

function renderReminderItem(r) {
    return `
        <div class="reminder-item ${r.concluido ? 'completed' : ''}">
            <input type="checkbox" ${r.concluido ? 'checked' : ''} onchange="toggleReminder(${r.id}, this.checked)">
            <span class="reminder-text">${escapeHtml(r.texto)}</span>
            <span class="reminder-date">${r.concluido ? `concluído em ${escapeHtml(r.concluidoEm)}` : escapeHtml(r.createdAt)}</span>
            <button class="btn-delete-reminder" onclick="deleteReminder(${r.id})" title="Apagar lembrete">✕</button>
        </div>
    `;
}

async function addReminder(event) {
    event.preventDefault();
    const input = document.getElementById('reminderInput');
    const texto = input.value.trim();
    if (!texto) return;

    try {
        const response = await fetch(`${API_URL}/reminders`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ texto })
        });

        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho

        if (response.ok) {
            input.value = '';
            renderReminders();
        } else {
            showToast('Erro ao salvar o lembrete.', 'error');
        }
    } catch (error) {
        console.error('Erro ao adicionar lembrete (detalhes técnicos abaixo, aperte F12 para ver):', error);
        showToast('Não foi possível conectar ao servidor. Confirme se a janela preta do sistema ainda está aberta.', 'error');
    }
}

async function toggleReminder(id, concluido) {
    try {
        const response = await fetch(`${API_URL}/reminders/${id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ concluido })
        });

        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho

        if (response.ok) {
            renderReminders();
        } else {
            showToast('Erro ao atualizar o lembrete.', 'error');
            renderReminders(); // desfaz o estado visual do checkbox em caso de erro
        }
    } catch (error) {
        console.error('Erro ao atualizar lembrete:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
        renderReminders();
    }
}

async function deleteReminder(id) {
    const confirmed = await showConfirm('Apagar este lembrete?');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/reminders/${id}`, { method: 'DELETE', headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (response.ok) {
            renderReminders();
        } else {
            showToast('Erro ao apagar o lembrete.', 'error');
        }
    } catch (error) {
        console.error('Erro ao apagar lembrete:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

async function clearCompletedReminders() {
    const confirmed = await showConfirm('Apagar todos os lembretes concluídos? Essa ação não pode ser desfeita.');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/reminders`, { method: 'DELETE', headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (response.ok) {
            showSuccessBanner('Os lembretes concluídos foram apagados.', 'Lembretes limpos!');
            renderReminders();
        } else {
            showToast('Erro ao limpar os concluídos.', 'error');
        }
    } catch (error) {
        console.error('Erro ao limpar lembretes concluídos:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

function toggleCompletedReminders() {
    appState.showCompletedReminders = !appState.showCompletedReminders;
    const section = document.getElementById('reminderCompletedSection');
    const label = document.getElementById('completedToggleLabel');
    if (section) section.style.display = appState.showCompletedReminders ? 'block' : 'none';
    if (label) label.textContent = appState.showCompletedReminders ? '▾ Ocultar concluídos' : '▸ Mostrar concluídos';
}

export {
    renderReminders, renderReminderItem, addReminder, toggleReminder,
    deleteReminder, clearCompletedReminders, toggleCompletedReminders,
};