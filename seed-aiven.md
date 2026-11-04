# Seed Aiven + Render — Resumo da sessão de troubleshooting

Registro do que foi feito, do que quebrou e por quê. Serve para retomar
depois sem repetir a diagnose.

---

## Contexto

- Repositório: `JoaoMoraes01/Sistema_sesi`, branch `deploy/render-demo`
- Frontend + backend: Render (web service `sistema-sesi-demo`)
- Banco: Aiven MySQL, host `sesidb-sistemasesi.c.aivencloud.com`
- Seed: `app/seed_teste.py`, 300 alunos fictícios, `SEED=2026`, idempotente por CPF
- Máquina local: Windows 10, PowerShell, venv em `.venv`
- Objetivo: rodar o seed localmente apontando para o Aiven

---

## Ordem dos eventos

### 1. Leitura do repositório e plano

Plano original dividido em:

- **Caminho A**: seed local exportando `MYSQL_*` no shell, sem `DATABASE_URL`.
- **Caminho B**: Render Job one-off reutilizando variáveis do web service.

Armadilha identificada no plano: `app/config.py` dá prioridade a
`DATABASE_URL` sobre `MYSQL_*`. Se a variável existir e apontar para
`localhost`, o seed semeia o banco local sem aviso.

### 2. Usuário definiu credenciais via `.env`

`.env` preenchido com host/porta/usuário/senha/banco/SSL/CA do Aiven.
Nenhuma variável exportada no shell.

### 3. Erro de conexão: timeout

```

sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)
(2003, "Can't connect to MySQL server on
'sesidb-sistemasesi.c.aivencloud.com' (timed out)")

```

A porta padrão usada pelo `pymysql` é 3306. O Aiven entrega uma porta
customizada que **não é 3306**.

### 4. Diagnóstico da URL resolvida

```

> python -c "from app.config import settings; print(settings.DATABASE_URL.rsplit('@', 1)[-1])"
> mysql+pymysql://sesidb-sistemasesi.c.aivencloud.com

```

O `rsplit('@', 1)[-1]` sem `@` na string retorna a string inteira. Isso
prova que a URL resolvida **não tem usuário, senha, porta nem database**.

Causa: `.env` continha `DATABASE_URL=mysql+pymysql://sesidb-sistemasesi.c.aivencloud.com`
incompleta. Como `DATABASE_URL` vence sobre `MYSQL_*` em `config.py`,
o `URL.create(...)` com os campos corretos nunca foi executado.

```

> python -c "import os; print('DATABASE_URL definido no ambiente:',
> bool(os.getenv('DATABASE_URL')))"
> DATABASE_URL definido no ambiente: False

```

Confirma que `DATABASE_URL` não estava exportada no shell — vinha só do
`.env` via `load_dotenv()`, que é o comportamento correto do
`python-dotenv` (`override=False`).

### 5. Correção aplicada

No `.env`:

- `DATABASE_URL` comentada ou removida.
- `MYSQL_PORT` ajustada para a porta real do painel Aiven (customizada).
- `MYSQL_SSL=true` e `MYSQL_SSL_CA` apontando para o PEM baixado.

Após a correção, o comando de conexão:

```

> python -c "from app.database import engine; c = engine.connect(); print('Conectado'); c.close()"
> Conectado

```

Conectou sem erro.

### 6. Seed rodou, mas parece travar

O seed ficou rodando por mais de um minuto sem imprimir nada.
Diagnóstico: **não travou**, é lento por construção.

Custo por aluno em `app/crud.py::create_student` + `app/seed_teste.py::main`:

1. `db.add(db_student)` + `db.commit()` + `db.refresh(db_student)`
2. `db.commit()` (irmãos, se houver)
3. `db.add(log)` + `db.commit()` (via `add_log`)
4. `db.commit()` para sobrescrever `registration_date`
5. `db.commit()` para ajustar `log.created_at`
6. `db.query(HistoryLog).order_by(HistoryLog.id.desc()).first()`

São **cinco commits e pelo menos dois SELECTs por aluno**, mais um
`SELECT ... ORDER BY id DESC LIMIT 1` que varre a tabela de logs
inteira a cada iteração (O(n) dentro de loop O(n)).

Em 300 alunos, mais de 2000 operações de rede. Com latência residencial
(150–250 ms RTT até o Aiven), o tempo total passa de 5 a 10 minutos.

---

## Como verificar progresso sem interromper

Em outro terminal (mesmo venv):

```bash
python -c "from app.database import SessionLocal; from app.models import Student; db=SessionLocal(); print('Alunos:', db.query(Student).count())"
```

Se o número sobe a cada 30 segundos, o seed está progredindo.

Alternativa: `SELECT COUNT(*) FROM alunos;` no console do Aiven.

---

## Estado atual (fim da sessão)

- Conexão com Aiven: **OK**.
- Seed: **em andamento**, sem erro, apenas lento.
- Frontend Render: ainda não verificado nesta sessão.

---

## Próximos passos recomendados

### Verificação pós-seed (quando o processo terminar)

```
python -c "from app.database import SessionLocal; from app.models import Student, HistoryLog; db=SessionLocal(); print('Alunos:', db.query(Student).count()); print('Logs seed:', db.query(HistoryLog).filter(HistoryLog.user_name=='seed_teste').count())"
```

Esperado: `Alunos: 300` e `Logs seed: 300`.

### Verificação no Render

1. Abrir a URL `.onrender.com`.
2. Login como `admin`, senha = `ADMIN_DEFAULT_PASSWORD`.
3. Aba **Lista & Busca**: devem aparecer 300 registros.
4. Aba **Histórico** (Painel Admin): 300 linhas `Novo Cadastro` com
`seed_teste` na coluna de usuário.

### Se o seed precisar rodar de novo (rodadas futuras)

Rodar do Render via **Render Job** (Caminho B do plano). Tráfego entre
web service e Aiven passa por datacenter, latência de dezenas de ms.
Os mesmos 300 alunos entram em menos de um minuto.

### Se quiser acelerar o seed localmente

Duas mudanças em `app/seed_teste.py` e `app/crud.py` reduzem o tempo
para segundos:

- Substituir `create_student` por insert em massa
(`db.execute(insert(Student), [...])` em lotes de 50).
- Trocar
`db.query(HistoryLog).order_by(HistoryLog.id.desc()).first()`
por `db.query(HistoryLog).filter(HistoryLog.user_name == 'seed_teste').order_by(HistoryLog.id.desc()).first()`.

Juntas: 1500 commits caem para 6, e o O(n) por iteração desaparece.

---

## Referência de comandos

### Diagnóstico de URL resolvida

```
python -c "from app.config import settings; print(settings.DATABASE_URL.rsplit('@', 1)[-1])"
```

### Teste de conexão com TLS

```
python -c "from app.database import engine; c = engine.connect(); print('Conectado'); c.close()"
```

### Contagem de alunos

```
python -c "from app.database import SessionLocal; from app.models import Student; db=SessionLocal(); print('Alunos:', db.query(Student).count())"
```

### Contagem de logs do seed

```
python -c "from app.database import SessionLocal; from app.models import HistoryLog; db=SessionLocal(); print('Logs seed:', db.query(HistoryLog).filter(HistoryLog.user_name=='seed_teste').count())"
```

### Rodar o seed em lotes (retomável por CPF)

```
python -m app.seed_teste --quantidade 50
python -m app.seed_teste --quantidade 100
python -m app.seed_teste --quantidade 150
```

### Teste TCP puro (confirma se a porta abre)

```
python -c "import socket; s=socket.create_connection(('sesidb-sistemasesi.c.aivencloud.com', PORTA_REAL), timeout=5); s.close(); print('OK')"
```

### Verificação no PowerShell

```
Test-NetConnection -ComputerName sesidb-sistemasesi.c.aivencloud.com -Port PORTA_REAL
```

`TcpTestSucceeded: True` indica que o caminho de rede está liberado.

---

## Lições para a próxima sessão

- `DATABASE_URL` no `.env` sempre vence sobre `MYSQL_*` em `config.py`.
Se um dos dois for usado, o outro precisa estar ausente ou comentado.
- A URL do Aiven sempre precisa de porta customizada. O default 3306 do
`pymysql` **não funciona**.
- `rsplit('@', 1)[-1]` sem `@` na string não é diagnóstico confiável
isolado — só prova que a URL está incompleta quando o resultado é a
string inteira.
- O seed é lento por design (5 commits por aluno). Um minuto de silêncio
não é travamento. Confirmar com contagem em outro terminal antes de
matar o processo.
- Ctrl+C no meio de um aluno pode deixar `registration_date` errada
permanentemente (próxima execução pula por CPF). Esperar o contador
de alunos estabilizar por 2 segundos antes de interromper.

