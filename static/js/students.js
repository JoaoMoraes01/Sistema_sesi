/*
 * Tudo relacionado a Aluno: formulário de cadastro/edição, validação de CPF,
 * comprovante (recibo), fila (Lista & Busca e Vagas e Ocupação).
 */
import { appState, API_URL, authHeaders, escapeHtml } from './state.js?v=14';
import { showToast, showConfirm, showSuccessBanner } from './ui.js?v=14';
import { switchTabDirect, switchTab, handleAuthResponse } from './auth.js?v=14';

// --- LISTAS FECHADAS ---
const GRADE_OPTIONS = [
    'Educação Infantil',
    '1º Ano Fundamental', '2º Ano Fundamental', '3º Ano Fundamental',
    '4º Ano Fundamental', '5º Ano Fundamental', '6º Ano Fundamental',
    '7º Ano Fundamental', '8º Ano Fundamental', '9º Ano Fundamental',
    '1º Ano Médio', '2º Ano Médio', '3º Ano Médio'
];
const CIVIL_OPTIONS = ['Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União Estável'];
const RESP_OPTIONS = [
    'Pai', 'Mãe', 'Avô/Avó', 'Tio(a)', 'Irmão(ã) maior',
    'Tutor(a) legal', 'Guardião(ã) judicial'
];

function checkLaudo() {
    const laudoSelect = document.getElementById('studentLaudo');
    const laudoBox = document.getElementById('laudoBox');

    if (laudoSelect && laudoBox) {
        if (laudoSelect.value === 'Sim') {
            laudoBox.style.display = 'grid';
        } else {
            laudoBox.style.display = 'none';
            const laudoInput = document.getElementById('laudoDesc');
            if (laudoInput) laudoInput.value = '';
        }
    }
}

function checkIrmao() {
    const qty = parseInt(document.getElementById('studentIrmaoQty')?.value) || 0;
    const container = document.getElementById('irmaoBox');
    if (!container) return;

    container.innerHTML = '';
    if (qty > 0) {
        container.style.display = 'grid';
        for (let i = 1; i <= qty; i++) {
            const opcoesSerie = GRADE_OPTIONS
                .map((g) => `<option value="${g}">${g}</option>`)
                .join('');

            container.innerHTML += `
                <div class="irmao-row" style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <input type="text" id="irmaoNome${i}"
                           placeholder="Nome do Irmão ${i}"
                           required maxlength="200"
                           pattern="[A-Za-zÀ-ÿ' \\-]+"
                           title="Use apenas letras, espaços, hífen e apóstrofo."
                           oninput="this.value = onlyLetters(this.value)"
                           style="flex: 2; min-width: 200px;">
                    <select id="irmaoSerie${i}" required style="flex: 1; min-width: 140px;">
                        <option value="" disabled selected>Série/Ano</option>
                        ${opcoesSerie}
                    </select>
                </div>
            `;
        }
    } else {
        container.style.display = 'none';
    }
}

// --- FORMATAÇÃO AUTOMÁTICA (CPF/CNPJ/CEP/TELEFONE/RG) ---

function formatCPF(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 11);
    return digits
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

function formatCNPJ(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 14);
    return digits
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1/$2')
        .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
}

function formatCEP(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 8);
    return digits.replace(/(\d{5})(\d)/, '$1-$2');
}

function formatTelefone(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 10) {
        return digits
            .replace(/(\d{2})(\d)/, '($1) $2')
            .replace(/(\d{4})(\d{1,4})$/, '$1-$2');
    }
    return digits
        .replace(/(\d{2})(\d)/, '($1) $2')
        .replace(/(\d{5})(\d{1,4})$/, '$1-$2');
}

function formatRG(value) {
    const digits = (value || '').replace(/\D/g, '').slice(0, 9);
    return digits
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1})$/, '$1-$2');
}

function onlyLetters(value) {
    return (value || '')
        .replace(/[^A-Za-zÀ-ÿ' \-]/g, '')
        .replace(/\s{2,}/g, ' ')
        .replace(/^\s+/, '')
        .slice(0, 200);
}

function validarCEP(cep) {
    const digits = (cep || '').replace(/\D/g, '');
    return digits.length === 0 || digits.length === 8;
}

function validarTelefone(tel) {
    const digits = (tel || '').replace(/\D/g, '');
    return digits.length === 0 || digits.length === 10 || digits.length === 11;
}

function toggleOtherField(baseId) {
    const select = document.getElementById(baseId);
    const otherInput = document.getElementById(baseId + 'Other');
    if (!select || !otherInput) return;

    const isOther = select.value === 'Outro';
    otherInput.style.display = isOther ? 'block' : 'none';
    otherInput.required = isOther;
    if (!isOther) otherInput.value = '';
}

function getFieldValue(baseId) {
    const select = document.getElementById(baseId);
    if (!select) return '';
    if (select.value === 'Outro') {
        return document.getElementById(baseId + 'Other')?.value.trim() || '';
    }
    return select.value;
}

function setFieldValue(baseId, value, knownOptions) {
    const select = document.getElementById(baseId);
    if (!select) return;

    if (!value) {
        select.value = '';
        toggleOtherField(baseId);
        return;
    }

    if (knownOptions.includes(value)) {
        select.value = value;
        toggleOtherField(baseId);
    } else {
        select.value = 'Outro';
        toggleOtherField(baseId);
        const otherInput = document.getElementById(baseId + 'Other');
        if (otherInput) otherInput.value = value || '';
    }
}

function validarCPF(cpf) {
    cpf = (cpf || '').replace(/\D/g, '');
    if (cpf.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(cpf)) return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) soma += parseInt(cpf[i], 10) * (10 - i);
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf[9], 10)) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) soma += parseInt(cpf[i], 10) * (11 - i);
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf[10], 10)) return false;

    return true;
}

async function handleFormSubmit(event) {
    event.preventDefault();
    const irmaoQty = parseInt(document.getElementById('studentIrmaoQty')?.value) || 0;
    let irmaos = [];
    for (let i = 1; i <= irmaoQty; i++) {
        const nome = document.getElementById(`irmaoNome${i}`)?.value;
        const serie = document.getElementById(`irmaoSerie${i}`)?.value;
        if (nome && serie) irmaos.push({ nome, serie });
    }

    const payload = {
        category: document.getElementById('studentCategory')?.value,
        studentName: document.getElementById('studentName')?.value,
        studentBirth: document.getElementById('studentBirth')?.value || null,
        studentRg: document.getElementById('studentRg')?.value || null,
        studentCpf: document.getElementById('studentCpf')?.value || null,
        studentNat: document.getElementById('studentNat')?.value || null,
        studentGrade: getFieldValue('studentGrade'),
        studentShift: document.getElementById('studentShift')?.value,
        studentLaudo: document.getElementById('studentLaudo')?.value,
        laudoDesc: document.getElementById('laudoDesc')?.value || null,
        irmaoQty: irmaoQty,
        irmaos: irmaos,
        respName: document.getElementById('respName')?.value,
        respBirth: document.getElementById('respBirth')?.value || null,
        respRg: document.getElementById('respRg')?.value || null,
        respCpf: document.getElementById('respCpf')?.value,
        respNat: document.getElementById('respNat')?.value || null,
        respAddress: document.getElementById('respAddress')?.value || null,
        respNum: document.getElementById('respNum')?.value || null,
        respBairro: document.getElementById('respBairro')?.value || null,
        respCep: document.getElementById('respCep')?.value || null,
        respCivil: getFieldValue('respCivil') || null,
        respEduc: document.getElementById('respEduc')?.value || null,
        respEmail: document.getElementById('respEmail')?.value || null,
        respCompany: document.getElementById('respCompany')?.value || null,
        respCnpj: document.getElementById('respCnpj')?.value || null,
        telPai: document.getElementById('telPai')?.value || null,
        emailPai: document.getElementById('emailPai')?.value || null,
        telMae: document.getElementById('telMae')?.value || null,
        emailMae: document.getElementById('emailMae')?.value || null,
        telOutro: document.getElementById('telOutro')?.value || null,
        emailOutro: document.getElementById('emailOutro')?.value || null,
        respFin: getFieldValue('respFin'),
        respAcad: getFieldValue('respAcad')
    };

    const erros = [];
    if (!validarCPF(payload.respCpf))                            erros.push('• CPF do responsável inválido');
    if (payload.studentCpf && !validarCPF(payload.studentCpf))   erros.push('• CPF do aluno inválido');
    if (!validarCEP(payload.respCep))                            erros.push('• CEP precisa ter 8 dígitos (00000-000)');
    if (!validarTelefone(payload.telPai))                        erros.push('• Telefone do Pai precisa ter 10 ou 11 dígitos');
    if (!validarTelefone(payload.telMae))                        erros.push('• Telefone da Mãe precisa ter 10 ou 11 dígitos');
    if (!validarTelefone(payload.telOutro))                      erros.push('• Telefone do Outro responsável precisa ter 10 ou 11 dígitos');

    if (erros.length) {
        showToast(erros.join('\n'), 'error');
        return;
    }

    const editingId = document.getElementById('editingId')?.value;
    const isEditing = !!editingId;
    const url = isEditing ? `${API_URL}/students/${editingId}` : `${API_URL}/students`;
    const method = isEditing ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        if (!handleAuthResponse(response)) return;

        if (response.ok) {
            const created = await response.json();
            cancelEdit();

            if (isEditing) {
                showSuccessBanner('O cadastro foi atualizado com sucesso.', 'Cadastro atualizado!');
                // Só a fila mudou — não faz sentido recarregar histórico/usuários.
                renderVagas();
            } else {
                // `await` para garantir appState.allStudents já atualizado
                // antes de buscar a posição do aluno recém-criado no banner.
                await renderVagas();
                const registered = appState.allStudents.find((s) => s.id === created.id) || created;
                showSuccessBanner(
                    `${registered.studentName} foi cadastrado(a) na posição ${registered.position ? registered.position + 'º lugar' : '(a definir)'}.\nSituação: ${registered.status_vaga || 'Em processamento'}.\n\nO comprovante para impressão fica disponível a qualquer momento em "Lista & Busca" ou "Vagas e Ocupação".`,
                    'Cadastro realizado com sucesso!',
                    9000
                );
            }
        } else if (response.status === 400) {
            const errorData = await response.json();
            showToast(`Erro: ${errorData.detail}`, 'error');
        } else if (response.status === 422) {
            const errorData = await response.json();
            const msgs = (errorData.detail || []).map((e) => {
                const campo = e.loc && e.loc.length ? e.loc[e.loc.length - 1] : '?';
                return `• ${campo}: ${e.msg}`;
            }).join('\n');
            showToast(msgs || 'Dados inválidos. Confira os campos.', 'error');
        } else {
            showToast(`Erro ${response.status} ao salvar. Tente novamente.`, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

// --- RECIBO ---

function showReceipt(student) {
    const body = document.getElementById('receiptBody');
    if (!body) return;

    const irmaosHtml = (student.irmaos && student.irmaos.length > 0)
        ? `<p><strong>Irmãos na escola:</strong></p><ul>${student.irmaos.map((i) => `<li>${escapeHtml(i.nome)} — ${escapeHtml(i.serie)}</li>`).join('')}</ul>`
        : '';

    body.innerHTML = `
        <h4>Dados do Aluno</h4>
        <p><strong>Nome:</strong> ${escapeHtml(student.studentName)}</p>
        <p><strong>Categoria:</strong> ${escapeHtml(student.category)}</p>
        <p><strong>Série/Turno:</strong> ${escapeHtml(student.studentGrade)} / ${escapeHtml(student.studentShift)}</p>
        ${irmaosHtml}

        <h4>Responsável</h4>
        <p><strong>Nome:</strong> ${escapeHtml(student.respName)}</p>

        <h4>Situação na Fila</h4>
        <p><strong>Data/Hora do cadastro:</strong> ${escapeHtml(student.timestamp)}</p>
        <p><strong>Posição atual:</strong> ${student.position ? `${student.position}º lugar` : 'a definir'}</p>
        <p><strong>Situação:</strong> ${escapeHtml(student.status_vaga) || 'Em processamento'}</p>
        <p style="margin-top: 10px; color: #666; font-size: 0.9em;">A posição pode mudar conforme novos cadastros forem feitos, respeitando os critérios de prioridade do sistema.</p>
    `;

    const modal = document.getElementById('sesiReceiptModal');
    if (modal) modal.style.display = 'flex';
}

function closeReceipt() {
    const modal = document.getElementById('sesiReceiptModal');
    if (modal) modal.style.display = 'none';
}

function showReceiptById(id) {
    const student = appState.allStudents.find((s) => s.id === id);
    if (!student) {
        showToast('Cadastro não encontrado na lista atual. Atualize a página e tente novamente.', 'error');
        return;
    }
    showReceipt(student);
}

// --- VAGAS E FILA ---

/**
 * Busca a fila do servidor e atualiza o cache. Depois:
 * - Renderiza a tabela de vagas SEMPRE (mesmo se invisível, pra estar pronta
 *   quando o usuário trocar de aba)
 * - Re-renderiza a tabela da Lista & Busca SOMENTE se aquela aba estiver ativa
 *   (antes rodava incondicionalmente, dobrando o trabalho de DOM)
 */
async function renderVagas() {
    const totalVagas = document.getElementById('totalVagasInput')?.value || 5;
    try {
        const response = await fetch(`${API_URL}/students/queue?total_vagas=${totalVagas}`, { headers: authHeaders() });
        if (!handleAuthResponse(response)) return;
        if (!response.ok) return;

        const sortedStudents = await response.json();
        appState.allStudents = prepararIndiceBusca(sortedStudents);

        renderVagasTableOnly();

        // Só re-renderiza a lista se o usuário estiver olhando para ela
        if (document.getElementById('tab-lista')?.classList.contains('active')) {
            filterTable(true);
        }
    } catch (error) {
        console.error('Erro na fila:', error);
        showToast('Não foi possível carregar a fila de alunos.', 'error');
    }
}

/**
 * Renderiza a tabela de "Vagas e Ocupação" a partir do cache `appState.allStudents`.
 * Não faz fetch. Usado ao trocar de aba (dados já carregados no login/CRUD).
 */
function renderVagasTableOnly() {
    const tbody = document.getElementById('vagasTableBody');
    if (!tbody) return;

    const sortedStudents = appState.allStudents;

    if (sortedStudents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhum aluno cadastrado.</td></tr>';
        return;
    }

    tbody.innerHTML = sortedStudents.map((s) => `
        <tr>
            <td><strong>${s.position}º</strong></td>
            <td>${escapeHtml(s.timestamp)}</td>
            <td>${escapeHtml(s.studentName)}</td>
            <td>${escapeHtml(s.category)}</td>
            <td><span class="status-vaga ${s.status_vaga === 'VAGA GARANTIDA' ? 'alocado' : 'espera'}">${escapeHtml(s.status_vaga)}</span></td>
            <td>
                <div class="table-actions">
                    <button class="btn-print" style="padding: 6px 12px; font-size: 0.85rem;" onclick="showReceiptById(${s.id})">Recibo</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// --- LISTA & BUSCA DE ALUNOS ---

function renderStudentsList(students) {
    const tbody = document.getElementById('studentTableBody');
    if (!tbody) return;

    if (students.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Nenhum cadastro encontrado.</td></tr>';
        return;
    }

    tbody.innerHTML = students.map((s) => `
        <tr>
            <td><strong>${s.position}º</strong></td>
            <td>${escapeHtml(s.timestamp)}</td>
            <td>${escapeHtml(s.studentName)}<br><span style="color: var(--text-muted); font-size: 0.85em;">${escapeHtml(s.studentCpf) || 'CPF não informado'}</span></td>
            <td>${escapeHtml(s.studentGrade)} / ${escapeHtml(s.studentShift)}</td>
            <td>${escapeHtml(s.category)}</td>
            <td>
                <div class="table-actions">
                    <button style="padding: 6px 12px; font-size: 0.85rem;" onclick="editStudent(${s.id})">Editar</button>
                    <button class="btn-print" style="padding: 6px 12px; font-size: 0.85rem;" onclick="showReceiptById(${s.id})">Recibo</button>
                    <button class="btn-danger" style="padding: 6px 12px; font-size: 0.85rem;" onclick="deleteStudent(${s.id})">Apagar</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function normalizarBusca(value) {
    return (value || '')
        .toString()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function apenasDigitos(value) {
    return (value || '').replace(/\D/g, '');
}

function prepararIndiceBusca(students) {
    students.forEach((s) => {
        s._nomeBusca = normalizarBusca(s.studentName);
        s._cpfBusca = apenasDigitos(s.studentCpf);
    });
    return students;
}

let _filtroTimer = null;

function filterTable(immediate = false) {
    clearTimeout(_filtroTimer);
    if (immediate) {
        aplicarFiltro();
    } else {
        _filtroTimer = setTimeout(aplicarFiltro, 180);
    }
}

function aplicarFiltro() {
    const term = (document.getElementById('searchInput')?.value || '').trim();
    const category = document.getElementById('filterCategory')?.value || 'all';

    const buscandoPorCpf = term.length > 0 && /^[\d.\-\s]+$/.test(term);
    const termNorm = normalizarBusca(term);
    const termDigits = apenasDigitos(term);

    const filtered = appState.allStudents.filter((s) => {
        if (category !== 'all' && s.category !== category) return false;
        if (!term) return true;

        if (buscandoPorCpf) {
            return termDigits.length > 0 && s._cpfBusca.includes(termDigits);
        }
        return s._nomeBusca.includes(termNorm);
    });

    renderStudentsList(filtered);

    const counter = document.getElementById('searchResultCount');
    if (counter) {
        if (!term && category === 'all') {
            counter.textContent = '';
            counter.style.display = 'none';
        } else {
            counter.textContent = `${filtered.length} resultado(s) encontrado(s)`;
            counter.style.display = 'block';
        }
    }
}

function editStudent(id) {
    const student = appState.allStudents.find((s) => s.id === id);
    if (!student) {
        showToast('Cadastro não encontrado na lista atual. Atualize a página e tente novamente.', 'error');
        return;
    }

    const setVal = (elId, value) => {
        const el = document.getElementById(elId);
        if (el) el.value = value ?? '';
    };

    setVal('editingId', student.id);
    setVal('studentCategory', student.category);
    setVal('studentName', student.studentName);
    setVal('studentBirth', student.studentBirth);
    setVal('studentRg', student.studentRg);
    setVal('studentCpf', student.studentCpf);
    setVal('studentNat', student.studentNat);
    setFieldValue('studentGrade', student.studentGrade, GRADE_OPTIONS);
    setVal('studentShift', student.studentShift);
    setVal('studentLaudo', student.studentLaudo);
    checkLaudo();
    setVal('laudoDesc', student.laudoDesc);

    setVal('studentIrmaoQty', student.irmaoQty || 0);
    checkIrmao();
    (student.irmaos || []).forEach((irmao, idx) => {
        setVal(`irmaoNome${idx + 1}`, irmao.nome);
        setVal(`irmaoSerie${idx + 1}`, irmao.serie);
    });

    setVal('respName', student.respName);
    setVal('respBirth', student.respBirth);
    setVal('respRg', student.respRg);
    setVal('respCpf', student.respCpf);
    setVal('respNat', student.respNat);
    setVal('respAddress', student.respAddress);
    setVal('respNum', student.respNum);
    setVal('respBairro', student.respBairro);
    setVal('respCep', student.respCep);
    setFieldValue('respCivil', student.respCivil, CIVIL_OPTIONS);
    setVal('respEduc', student.respEduc);
    setVal('respEmail', student.respEmail);
    setVal('respCompany', student.respCompany);
    setVal('respCnpj', student.respCnpj);
    setVal('telPai', student.telPai);
    setVal('emailPai', student.emailPai);
    setVal('telMae', student.telMae);
    setVal('emailMae', student.emailMae);
    setVal('telOutro', student.telOutro);
    setVal('emailOutro', student.emailOutro);
    setFieldValue('respFin', student.respFin, RESP_OPTIONS);
    setFieldValue('respAcad', student.respAcad, RESP_OPTIONS);

    document.getElementById('formTitle').textContent = 'Editando Cadastro';
    document.getElementById('formSubtitle').textContent = `Alterando os dados de ${student.studentName}. Salve para atualizar o cadastro.`;
    const btnSubmit = document.getElementById('btnSubmitForm');
    if (btnSubmit) btnSubmit.textContent = 'Atualizar Cadastro';
    const btnCancel = document.getElementById('btnCancelEdit');
    if (btnCancel) btnCancel.style.display = 'inline-block';

    appState.editOriginTab = document.querySelector('.tab-content.active')?.id || null;

    switchTabDirect('tab-cadastro');
    document.getElementById('navCadastro')?.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function cancelEdit() {
    document.getElementById('studentForm')?.reset();
    document.getElementById('editingId').value = '';
    document.getElementById('formTitle').textContent = 'Formulário de Cadastro';
    document.getElementById('formSubtitle').textContent = 'Preencha os dados do requerente e do aluno abaixo.';
    const btnSubmit = document.getElementById('btnSubmitForm');
    if (btnSubmit) btnSubmit.textContent = 'Salvar Cadastro';
    const btnCancel = document.getElementById('btnCancelEdit');
    if (btnCancel) btnCancel.style.display = 'none';
    checkLaudo();
    checkIrmao();
    ['studentGrade', 'respCivil', 'respFin', 'respAcad'].forEach(toggleOtherField);

    if (appState.editOriginTab && appState.editOriginTab !== 'tab-cadastro') {
        switchTab(null, appState.editOriginTab);
    }
    appState.editOriginTab = null;
}

async function deleteStudent(id) {
    const student = appState.allStudents.find((s) => s.id === id);
    const confirmed = await showConfirm(`Tem certeza que deseja apagar o cadastro de "${escapeHtml(student ? student.studentName : 'este aluno')}"? Essa ação não pode ser desfeita.`);
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/students/${id}`, { method: 'DELETE', headers: authHeaders() });
        if (!handleAuthResponse(response)) return;
        if (response.ok) {
            showSuccessBanner('O cadastro foi removido com sucesso.', 'Cadastro removido!');
            renderVagas();
        } else {
            const err = await response.json();
            showToast(`Erro: ${err.detail}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao apagar cadastro:', error);
        showToast('Não foi possível conectar ao servidor.', 'error');
    }
}

export {
    checkLaudo, checkIrmao, validarCPF, handleFormSubmit,
    showReceipt, closeReceipt, showReceiptById,
    renderVagas, renderVagasTableOnly, renderStudentsList, filterTable,
    editStudent, cancelEdit, deleteStudent,
    formatCPF, formatCNPJ, formatCEP, formatTelefone, formatRG, onlyLetters, toggleOtherField,
    normalizarBusca,
};
