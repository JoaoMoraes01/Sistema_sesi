/*
 * Histórico de atividades (Painel Admin): consultar e limpar o log de auditoria.
 */
import { API_URL, authHeaders, escapeHtml } from './state.js';
import { showToast, showConfirm, showSuccessBanner } from './ui.js';
import { handleAuthResponse } from './auth.js';

async function renderHistory() {
    try {
        const response = await fetch(`${API_URL}/history`, { headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (!response.ok) return;
        
        const logs = await response.json();
        const tbody = document.getElementById('historyTableBody');
        if (!tbody) return;
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Nenhum registro.</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map((log) => `
            <tr>
                <td>${escapeHtml(log.date)}</td>
                <td>${escapeHtml(log.action)}</td>
                <td>${escapeHtml(log.details)}</td>
                <td>${escapeHtml(log.user)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Erro no histórico:', error);
    }
}

async function clearHistory() {
    const confirmed = await showConfirm('Tem certeza que deseja apagar TODO o histórico de atividades? Essa ação não pode ser desfeita.');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/history`, { method: 'DELETE', headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (response.ok) {
            showSuccessBanner('Todo o histórico de atividades foi apagado.', 'Histórico limpo!');
            renderHistory();
        } else {
            showToast('Erro ao limpar o histórico.', 'error');
        }
    } catch (error) {
        console.error('Erro ao limpar histórico:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

export { renderHistory, clearHistory };