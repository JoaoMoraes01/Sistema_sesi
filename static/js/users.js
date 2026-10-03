/*
 * Painel Admin: gestão dos usuários que têm login no sistema.
 */
import { appState, API_URL, authHeaders, escapeHtml } from './state.js';
import { showToast, showConfirm, showSuccessBanner } from './ui.js';
import { renderAll, handleAuthResponse } from './auth.js';

async function handleCreateUser(event) {
    event.preventDefault();
    const name = document.getElementById('newUserName').value.trim();
    const username = document.getElementById('newUserLogin').value.trim();
    const pass = document.getElementById('newUserPass').value.trim();
    const role = document.getElementById('newUserRole').value;
    const editingLogin = document.getElementById('editingUserId')?.value;
    const isEditing = !!editingLogin;

    if (isEditing) {
        // Na edição, login não muda; senha é opcional (em branco = mantém a atual)
        const payload = { name, role };
        if (pass) payload.pass_word = pass;

        try {
            const response = await fetch(`${API_URL}/users/${editingLogin}`, {
                method: 'PUT',
                headers: authHeaders(),
                body: JSON.stringify(payload)
            });

            if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho

            if (response.ok) {
                showSuccessBanner('O usuário foi atualizado com sucesso.', 'Usuário atualizado!');
                cancelUserEdit();
                renderAll();
            } else {
                const errorData = await response.json();
                showToast(`Erro ao atualizar: ${errorData.detail || 'verifique os campos.'}`, 'error');
            }
        } catch (error) {
            console.error('Erro ao atualizar usuário:', error);
            showToast('Não foi possível conectar ao servidor.', 'error');
        }
        return;
    }

    const payload = {
        name: name,
        login: username,
        pass_word: pass,
        role: role
    };

    try {
        const response = await fetch(`${API_URL}/users`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho

        if (response.ok) {
            showSuccessBanner('O novo usuário foi cadastrado com sucesso.', 'Usuário cadastrado!');
            document.getElementById('userForm').reset();
            renderAll(); 
        } else {
            const errorData = await response.json();
            showToast(`Erro ao cadastrar: ${errorData.detail}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao criar usuário:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

// Preenche o formulário de usuário para edição (substitui o antigo fluxo baseado em prompt())
function editUser(login) {
    const user = appState.allUsers.find((u) => u.login === login);
    if (!user) {
        showToast('Usuário não encontrado na lista atual. Atualize a página e tente novamente.', 'error');
        return;
    }

    document.getElementById('editingUserId').value = user.login;
    document.getElementById('userFormTitle').textContent = `Editando Usuário: ${user.name}`;
    document.getElementById('userFormSubtitle').textContent = 'Altere os campos desejados e clique em "Atualizar Usuário" para salvar.';
    document.getElementById('newUserName').value = user.name;
    document.getElementById('newUserLogin').value = user.login;
    document.getElementById('newUserPass').value = '';
    document.getElementById('newUserPass').placeholder = 'Deixe em branco para manter a senha atual';
    document.getElementById('newUserPass').required = false;
    document.getElementById('newUserRole').value = user.role;

    const loginInput = document.getElementById('newUserLogin');
    loginInput.readOnly = true;
    loginInput.style.opacity = '0.7';
    loginInput.style.cursor = 'not-allowed';

    const btnSubmit = document.getElementById('btnSubmitUser');
    if (btnSubmit) btnSubmit.textContent = 'Atualizar Usuário';
    const btnCancel = document.getElementById('btnCancelUserEdit');
    if (btnCancel) btnCancel.style.display = 'inline-block';

    document.getElementById('userForm')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function cancelUserEdit() {
    document.getElementById('userForm')?.reset();
    document.getElementById('editingUserId').value = '';
    document.getElementById('userFormTitle').textContent = 'Gerenciamento de Usuários';
    document.getElementById('userFormSubtitle').textContent = 'Crie, edite ou remova credenciais de acesso para a equipe escolar.';

    const passInput = document.getElementById('newUserPass');
    passInput.placeholder = 'Senha de acesso';
    passInput.required = true;

    const loginInput = document.getElementById('newUserLogin');
    loginInput.readOnly = false;
    loginInput.style.opacity = '';
    loginInput.style.cursor = '';

    const btnSubmit = document.getElementById('btnSubmitUser');
    if (btnSubmit) btnSubmit.textContent = 'Adicionar Novo Usuário';
    const btnCancel = document.getElementById('btnCancelUserEdit');
    if (btnCancel) btnCancel.style.display = 'none';
}

async function renderUsers() {
    try {
        const response = await fetch(`${API_URL}/users`, { headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (!response.ok) return;
        
        const users = await response.json();
        appState.allUsers = users; // cache usada pela edição (evita nova chamada à API ao clicar em "Editar")
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Nenhum usuário.</td></tr>';
            return;
        }
        
        tbody.innerHTML = users.map((u) => `
            <tr>
                <td>${escapeHtml(u.name)}</td>
                <td>${escapeHtml(u.login)}</td>
                <td>${u.role === 'admin' ? 'Administrador' : 'Atendente'}</td>
                <td>
                    <div class="table-actions">
                        <button class="btn-warning" style="padding: 6px 12px; font-size: 0.85rem;" onclick="editUser('${u.login}')">Editar</button>
                        <button class="btn-danger" style="padding: 6px 12px; font-size: 0.85rem;" onclick="apagarUsuario('${u.login}')">Apagar</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Erro ao buscar usuários:', error);
    }
}

// === APAGAR USUÁRIO ===

async function apagarUsuario(login) {
    const confirmed = await showConfirm(`Tem certeza que deseja apagar o usuário ${login}?`);
    if (!confirmed) return;
    
    try {
        const response = await fetch(`${API_URL}/users/${login}`, { method: 'DELETE', headers: authHeaders() });
        if (!handleAuthResponse(response)) return; // token expirado/inválido: já desloga sozinho
        if (response.ok) {
            showSuccessBanner('O usuário foi removido com sucesso.', 'Usuário removido!');
            renderUsers();
        } else {
            const err = await response.json();
            showToast(`Erro: ${err.detail}`, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

export { handleCreateUser, editUser, cancelUserEdit, renderUsers, apagarUsuario };