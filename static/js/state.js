/*
 * Estado global do front-end.
 *
 * Fica tudo dentro de UM objeto (appState) em vez de variáveis soltas —
 * assim, qualquer módulo que importar `appState` pode ler E alterar esses
 * valores. Módulos JavaScript não deixam você reatribuir uma variável
 * importada diretamente, mas mutar uma propriedade de um objeto importado
 * funciona normalmente — por isso o objeto.
 */
export const appState = {
    currentUserRole: '',
    currentUserName: '',   // nome real de quem está logado, usado para rastreabilidade no histórico
    currentUserLogin: '',  // login (identificador único), usado para filtrar os Lembretes de cada um
    authToken: '',         // token JWT devolvido no login — obrigatório em toda rota protegida
    allStudents: [],       // cache em memória da última fila carregada (usada pela busca/filtro e pela edição)
    allUsers: [],          // cache em memória da última lista de usuários (usada pela edição no painel admin)
    allReminders: [],      // cache em memória dos lembretes do usuário logado
    showCompletedReminders: false, // controla se a seção "Concluídos" está expandida
    editOriginTab: null,   // guarda de qual aba o usuário veio antes de clicar em "Editar" um aluno
};

export const API_URL = '/api'; // relativo: front-end e back-end agora rodam no mesmo servidor/porta

export function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${appState.authToken}`
    };
}

// Mapa de substituição fixo (fora da função) para não recriar objeto a cada chamada.
const HTML_ESCAPE_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
};

/**
 * Escapa caracteres especiais de HTML antes de inserir um valor vindo do
 * usuário dentro de um template `innerHTML` (proteção contra XSS armazenado).
 *
 * Uma única regex com callback é ~4x mais rápida que cinco `.replace()` em
 * sequência — relevante porque esta função é chamada milhares de vezes ao
 * renderizar a lista de alunos.
 */
export function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value).replace(/[&<>"']/g, (c) => HTML_ESCAPE_MAP[c]);
}
