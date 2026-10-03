# Sistema de Gestão de Fila de Matrículas — SESI

Sistema web para gerenciar a fila de espera de matrículas do SESI, aplicando
automaticamente as regras de prioridade de cadastro (categoria do candidato,
possuir irmão já matriculado, e ordem de chegada) e oferecendo um painel
administrativo completo para acompanhar e gerenciar essa fila.

Substitui o processo em papel/planilhas (500+ solicitações) e roda 100% na
rede interna da escola (intranet): o servidor fica em uma máquina e os demais
computadores/celulares acessam pelo navegador usando o IP local.

Projeto desenvolvido como parte de uma competição de resolução de problemas
do SESI, com apoio de IA (Claude/Anthropic) como ferramenta de
desenvolvimento e aprendizado — todas as decisões de arquitetura, revisão de
segurança e testes foram acompanhadas e validadas ao longo do processo.

## Funcionalidades

- **Fila com prioridade automática** — ordena os candidatos por categoria
  (Industriário → Colaborador → Empresário Industrial → Convênio →
  Comunidade), depois por quem já tem irmão matriculado (regra booleana),
  e por último por ordem de cadastro. A posição na fila nunca é gravada no
  banco: é sempre recalculada na hora, o que evita erros de concorrência.
- **Autenticação real** — login com senha protegida por hash (bcrypt) e
  token JWT, com dois papéis **que não se sobrepõem**:
  - **Admin**: gerencia usuários e vê/limpa o histórico (não mexe em cadastros);
  - **Atendente**: cadastra, edita e exclui candidatos e define o total de vagas.
- **Cadastro completo de aluno e responsável**, com validação de CPF (dígitos
  verificadores) no front-end E no back-end, bloqueio de CPF duplicado mesmo
  com formatação diferente ("529.982.247-25" = "52998224725"), máscaras
  automáticas de CPF/CNPJ/CEP/telefone e campos "Outro" com texto livre.
- **Painel administrativo**: gestão de usuários do sistema e histórico
  auditável de todas as ações (quem cadastrou, editou ou excluiu o quê, e
  quando — registrando o nome real da pessoa, não só o cargo).
- **Lembretes pessoais** por usuário (aba exclusiva, com badge de pendentes
  e seção recolhível de concluídos).
- **Comprovante de cadastro** imprimível a qualquer momento (botão "Recibo")
  e **Relatório de Aptos** imprimível (quem está com vaga garantida).
- **Acessibilidade**: tamanho de fonte (5 níveis), alto contraste, fonte
  facilitada para dislexia e espaçamento entre linhas — tudo persistente.
- **Tema claro/escuro**, com preferência salva no navegador.
- **Confirmações visuais grandes** (banner centralizado) nas ações
  importantes, em vez de alerts/toasts discretos que passam despercebidos.

## Tecnologias

**Back-end:** Python, FastAPI, SQLAlchemy, Pydantic v2, MySQL (PyMySQL),
JWT (python-jose), bcrypt.
**Front-end:** HTML, CSS e JavaScript puros, organizados em módulos ES
(sem framework, sem etapa de build) — servidos diretamente pelo FastAPI.
**Testes:** script de validação automatizada (`teste_correcoes.py`), com
banco SQLite em memória — não precisa do MySQL rodando para testar.

## Estrutura de pastas

```
sistema_sesi/
├── app/
│   ├── main.py             # cria o app, middlewares, routers e serve o front-end
│   ├── config.py           # configurações lidas do .env
│   ├── database.py         # conexão com o MySQL (SQLAlchemy)
│   ├── models.py           # tabelas do banco de dados
│   ├── schemas.py          # validação de entrada/saída (Pydantic)
│   ├── crud.py             # regras de negócio e acesso ao banco
│   ├── security.py         # hash de senha (bcrypt) e tokens (JWT)
│   ├── dependencies.py     # proteção de rotas (login exigido / só admin)
│   └── routes/             # cada arquivo cuida de um assunto da API
│       ├── auth.py          #   login (+ bloqueio anti força bruta)
│       ├── students.py      #   cadastro, fila, edição e exclusão de alunos
│       ├── users.py         #   gestão de usuários (Painel Admin)
│       ├── history.py       #   histórico de atividades (Painel Admin)
│       └── reminders.py     #   lembretes pessoais
├── static/                 # front-end (servido pelo próprio FastAPI)
│   ├── index.html
│   ├── style.css
│   ├── sesi.png
│   └── js/                 # módulos ES: state, ui, accessibility, auth,
│                           #   students, history, reminders, users, main
├── requirements.txt        # dependências Python
├── .env                    # configuração real (NUNCA compartilhar/versionar)
├── .env.example            # modelo do .env (seguro para compartilhar)
├── seguranca_mysql.sql     # cria o usuário dedicado do banco (sem usar root)
├── teste_correcoes.py      # teste automatizado das correções de segurança
├── iniciar.bat / iniciar.sh# atalho de duplo clique para subir o sistema
└── README.md               # este arquivo
```

## Como rodar no dia a dia (máquina já configurada)

No Windows, dê **duplo clique em `iniciar.bat`** (ou execute
`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`).

O servidor abre o navegador sozinho em `http://127.0.0.1:8000/` e imprime no
console o endereço para acessar de outros dispositivos na mesma rede
(ex: `http://192.168.x.x:8000`).

A janela preta do terminal **precisa ficar aberta** enquanto o sistema estiver
em uso — fechá-la desliga o sistema. Para copiar texto dela, selecione com o
mouse e clique com o botão direito (Ctrl+C encerra o servidor).

> **Dica:** fora do VS Code é mais estável. O terminal integrado dele tem
> instabilidades conhecidas para manter o servidor de pé.

## Instalando em uma máquina NOVA (passo a passo do zero)

### 1. Instalar o Python
1. Baixe o Python 3.12+ em <https://www.python.org/downloads/>
2. **Na primeira tela do instalador, marque "Add python.exe to PATH"** antes de
   clicar em Install (sem isso, os comandos `python` não funcionam no terminal)
3. Confira no terminal: `python --version`

### 2. Instalar o MySQL
1. Baixe o MySQL Installer em <https://dev.mysql.com/downloads/installer/>
2. Instale no modo "Server only" (ou "Developer Default") e **anote a senha do
   root** que você definir
3. Crie o banco do sistema. No terminal:
   ```
   mysql -u root -p
   CREATE DATABASE sesi_gestao CHARACTER SET utf8mb4;
   exit
   ```

### 3. Trazer o código
- Pelo Git: `git clone <url-do-repositorio>` e entre na pasta; **ou**
- Copie a pasta `sistema_sesi` por pen drive/zip (descompacte antes)

### 4. Instalar as dependências
Dentro da pasta do projeto:
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 5. Configurar o `.env`
```bash
copy .env.example .env        # Windows
cp .env.example .env          # Linux/Mac
```
Edite o `.env` e preencha:
- `MYSQL_USER` / `MYSQL_PASSWORD` — veja o passo 6 abaixo (recomendado)
- `JWT_SECRET_KEY` — gere uma chave fixa com:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- `ADMIN_DEFAULT_PASSWORD` — senha do primeiro admin. Se deixar vazia, o
  sistema gera uma aleatória e mostra **uma única vez** no console na primeira
  execução. Depois da criação do admin, esta linha não tem mais efeito.

### 6. (Recomendado) Criar o usuário dedicado do banco
Em vez de usar o `root` do MySQL no sistema, rode:
```
mysql -u root -p < seguranca_mysql.sql
```
**Antes, abra o arquivo `seguranca_mysql.sql` e troque `TROQUE_ESTA_SENHA`
por uma senha forte.** Depois ajuste `MYSQL_USER=sesi_app` e a senha no `.env`.

### 7. Liberar a porta no Firewall do Windows (para acesso pela rede)
Para outros dispositivos da escola acessarem, libere a porta 8000:
```
netsh advfirewall firewall add rule name="Sistema SESI 8000" dir=in action=allow protocol=TCP localport=8000
```
(execute o terminal **como administrador**)

### 8. Primeira execução
Dê duplo clique em `iniciar.bat`. Na primeira vez, o sistema cria as tabelas
e o usuário `admin` sozinho. Anote a senha do admin (a do `.env` ou a gerada
no console) e **troque-a no Painel Admin logo no primeiro acesso**.

### 9. Teste de conectividade entre máquinas
Antes do uso real (ou do teste de invasão com o professor), confira de outro
dispositivo: `http://<IP-do-servidor>:8000`. Se não abrir:
- Verifique o firewall (passo 7)
- **Atenção ao hotspot de celular:** muitos têm "isolamento de cliente"
  (AP Isolation), que impede os aparelhos de se enxergarem. Prefira o Wi-Fi
  da escola ou um roteador.


## Rodar os testes automatizados

```bash
python teste_correcoes.py
```
Usa um banco SQLite isolado em memória — não precisa de MySQL rodando e não
toca no banco real. Ao final, imprime se todos os testes passaram e salva o
resultado em `resultado_teste.txt`.

## Segurança (o que já é praticado)

- **Senhas com hash bcrypt** — nada de senha em texto puro no banco. Contas
  antigas (criadas antes do hash) são migradas automaticamente no 1º login.
- **Toda rota de dados exige token JWT válido**, verificado no servidor
  (não apenas escondido no front-end). Rotas administrativas exigem o papel
  de admin, também verificado no servidor.
- **Bloqueio anti força bruta no login**: 5 tentativas erradas em 5 minutos
  trava o usuário temporariamente.
- **CORS restrito** às origens da rede interna (sem `*` e sem cookies).
- **Validação no back-end** de CEP, telefone e regras de formato — o front-end
  também valida, mas quem chamar a API direto não passa batido.
- **XSS armazenado neutralizado**: dados vindos do banco são escapados
  (`escapeHtml`) antes de entrarem no HTML da página.
- **SQL Injection**: impossível por construção — 100% das consultas passam
  pelo SQLAlchemy com parâmetros (nenhuma string de SQL montada na mão).
- **Nenhuma senha no código-fonte**: credenciais ficam só no `.env`
  (protegido pelo `.gitignore`).

## Melhorias já aplicadas (auditoria de segurança — set/2026)

- [x] Senha padrão do admin **fora do código-fonte** (vai para o `.env` ou é
      gerada aleatoriamente; a antiga `Sesi@2026!` deixou de existir no código)
- [x] Criados `.env.example` e `seguranca_mysql.sql` (usuário dedicado do
      banco, em vez do root)
- [x] Bug da edição de usuário com `role` inválido (virava Erro 500 no MySQL)
      corrigido com validação por enum
- [x] Teste automatizado das correções (`teste_correcoes.py`) — 12 verificações
- [x] (rodadas anteriores) XSS armazenado, CORS aberto, senha do MySQL no
      fallback do código, rate limiting no login, migração automática de
      senhas antigas em texto puro para bcrypt

## Pontos pendentes (próximas rodadas, por prioridade)

Prioridade média — segurança:
- [ ] Token de usuário apagado/rebaixado segue válido até expirar (8h) —
      validar o usuário no banco a cada requisição
- [ ] Cadastro de aluno não é atômico (3 commits separados — se falhar no
      meio, grava dado parcial)
- [ ] Condição de corrida na checagem de CPF duplicado (verifica e depois
      insere, sem índice único no banco)
- [ ] XSS residual: `onclick="editUser('${u.login}')` em users.js e mensagem
      de `showConfirm()` sem escape interno
- [ ] Validar dígitos verificadores do CPF também no back-end (hoje só no front)
- [ ] Migrar de `python-jose` (CVEs conhecidos) para `PyJWT`
- [ ] Definir tamanhos máximos nos campos do schema (evita Erro 500 com
      textos maiores que a coluna do banco)
- [ ] HTTPS (tráfego hoje é texto puro na rede local) — essencial se o
      sistema sair do "só intranet"
- [ ] Trocar a senha do admin de produção pelo Painel Admin (a senha antiga
      `Sesi@2026!` pode estar conhecida/vazada em compartilhamentos do código)

Prioridade baixa — estrutura:
- [ ] Restaurar a suíte pytest (pasta `tests/` ficou na versão anterior)
- [ ] Admin pode rebaixar o papel do próprio "admin" e trancar o sistema
      sem administrador
- [ ] Consulta de CPF duplicado carrega todos os alunos em memória
      (normalizar CPF no save + índice único resolve)
- [ ] N+1 queries ao montar a fila (carregar irmãos com `selectinload`)
- [ ] Campo para digitar cadastros antigos do papel preservando a **data/hora
      original** da solicitação (hoje a data é sempre "agora")
- [ ] Travar versões exatas das dependências (`pip freeze`)
- [ ] Migrações de banco automatizadas (Alembic) em vez de só `create_all`

## Solução de problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `python` não é reconhecido | Python fora do PATH | Reinstale marcando "Add python.exe to PATH" |
| Erro `bcrypt has no attribute __about__` | passlib antigo | Já resolvido: o sistema fala direto com a lib `bcrypt`. Se aparecer, rode `pip uninstall passlib` |
| Aviso do Chrome "senha vazada" | A senha usada já vazou em outro site | Troque a senha do usuário no Painel Admin |
| Não conecta no MySQL | Serviço parado ou senha errada no `.env` | Inicie o MySQL (services.msc) e confira usuário/senha |
| Outras máquinas não acessam | Firewall ou AP Isolation | Veja os passos 7 e 9 da instalação |
| Login de todo mundo cai ao reiniciar | `JWT_SECRET_KEY` mudou | Mantenha a chave fixa no `.env` |
| Erro 500 ao editar usuário | `role` inválida enviada à API | Corrigido nesta versão (agora retorna 422) |

