/*
 * Estado global do front-end.
 *
 * Fica tudo dentro de UM objeto (appState) em vez de variáveis soltas —
 * assim, qualquer módulo que importar `appState` pode ler E alterar esses
 * valores. Módulos JavaScript não deixam você reatribuir uma variável
 * importada diretamente (ex: `import { authToken } from ...; authToken = 'x'`
 * dá erro), mas mutar uma propriedade de um objeto importado (`appState.authToken = 'x'`)
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

// Monta os headers usados em toda chamada autenticada. O token no cabeçalho
// Authorization é o que o backend confere de verdade (Depends(get_current_user));
// sem ele, ou com ele expirado/inválido, a rota recusa o pedido com 401 —
// mesmo que alguém tente burlar o JavaScript e chamar a API direto.
export function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${appState.authToken}`
    };
}

// Escapa caracteres especiais de HTML antes de inserir um valor vindo do
// usuário (nome, endereço, lembrete etc.) dentro de um template `innerHTML`.
// Sem isso, alguém poderia cadastrar um aluno com nome tipo
// `<img src=x onerror="...">` e esse código rodaria de verdade no navegador
// de quem visse a lista (inclusive o Admin, ao ver o Histórico) — é o que
// se chama de XSS armazenado (Stored XSS). Use SEMPRE que for colocar um
// valor vindo da API dentro de um template `${...}` que vira innerHTML.
export function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}