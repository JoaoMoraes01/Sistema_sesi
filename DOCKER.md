# Como rodar o Sistema SESI no Docker (pelo VS Code)

Este guia explica como subir o sistema usando Docker direto do VS Code, sem precisar instalar Python nem MySQL na sua máquina. A ideia é que qualquer pessoa consiga clonar o repositório, seguir os passos abaixo e ter o sistema rodando no navegador em poucos minutos.

---

## O que você vai precisar

- **Docker Desktop** instalado e aberto (baixe em <https://www.docker.com/products/docker-desktop/>). No Windows, ele precisa estar rodando antes de qualquer coisa.
- **VS Code** instalado (baixe em <https://code.visualstudio.com/>).
- A extensão **Docker** do VS Code. Para instalar: abra o VS Code, aperte `Ctrl+Shift+X`, procure por "Docker" (a oficial é da Microsoft, ID `ms-azuretools.vscode-docker`) e clique em Install.

Depois de instalar a extensão, recarregue o VS Code (`Ctrl+Shift+P` → "Developer: Reload Window"). Um ícone de baleia 🐳 vai aparecer na barra lateral esquerda. Se o topo dele disser "Docker Engine: Running", está tudo certo.

---

## Arquivos necessários na raiz do projeto

O projeto precisa ter quatro arquivos na **raiz** (mesmo nível das pastas `app/` e `static/`). Se eles ainda não existirem no seu clone, crie conforme abaixo.

### 1. `Dockerfile`

Diz ao Docker como montar a imagem do sistema. Conteúdo:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OPEN_BROWSER=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY static/ ./static/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

O ponto importante aqui é que as pastas `app/` e `static/` precisam ficar **lado a lado** dentro do container (`/app/app/` e `/app/static/`), porque o `main.py` procura o front-end em `../static` a partir da pasta do código Python. Se copiar de outro jeito, o site não carrega.

### 2. `.dockerignore`

Evita que arquivos desnecessários (e segredos) entrem na imagem. Conteúdo:

```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env
.env.*
!.env.example
.git/
.gitignore
.vscode/
.idea/
*.md
iniciar.bat
iniciar.sh
render.yaml
seguranca_mysql.sql
teste_correcoes.py
resultado_teste.txt
```

A linha mais importante é o `.env`. Sem ela, seu arquivo de senhas poderia ir para dentro da imagem Docker.

### 3. `docker-compose.yml`

Sobe o sistema e o banco de dados juntos, na ordem certa. Conteúdo:

```yaml
services:
  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpass_local}
      MYSQL_DATABASE: ${MYSQL_DB:-sesi_gestao}
      MYSQL_USER: ${MYSQL_USER:-sesi_app}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-sesi_pass_local}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-u", "root", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 15
      start_period: 30s
    restart: unless-stopped

  app:
    build: .
    image: sistema-sesi:latest
    ports:
      - "8000:8000"
    environment:
      MYSQL_USER: ${MYSQL_USER:-sesi_app}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-sesi_pass_local}
      MYSQL_HOST: db
      MYSQL_PORT: "3306"
      MYSQL_DB: ${MYSQL_DB:-sesi_gestao}
      MYSQL_SSL: "false"
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?defina JWT_SECRET_KEY no .env}
      JWT_EXPIRE_MINUTES: "480"
      ADMIN_DEFAULT_PASSWORD: ${ADMIN_DEFAULT_PASSWORD:?defina ADMIN_DEFAULT_PASSWORD no .env}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  mysql_data:
```

O que ele faz, em resumo:

- O serviço **db** cria um MySQL já com o banco `sesi_gestao` e um usuário dedicado (não usa root). Os dados ficam num volume `mysql_data`, então sobrevivem a reinicializações.
- O serviço **app** constrói a imagem a partir do `Dockerfile`, expõe a porta `8000` e espera o MySQL ficar "saudável" antes de iniciar.
- `MYSQL_HOST: db` é obrigatório: dentro do container, `localhost` aponta para o próprio app, não para o banco. O nome `db` é o que conecta os dois.

### 4. `.env`

O projeto já tem esse arquivo localmente. Para o Docker funcionar, ele precisa ter **no mínimo** duas variáveis:

```env
JWT_SECRET_KEY=cole_aqui_uma_chave_aleatoria_longa
ADMIN_DEFAULT_PASSWORD=uma_senha_forte_para_o_admin
```

Para gerar a chave, abra o terminal do VS Code (`Ctrl+` `) e rode:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e cole no `.env`. O `docker compose` lê esse arquivo automaticamente — não precisa passar nada na linha de comando.

> **Atenção:** nunca faça commit do `.env` no Git. Ele deve estar listado no `.gitignore`.

---

## Como rodar (pela primeira vez)

1. Abra a pasta do projeto no VS Code (`File → Open Folder`).
2. Abra o terminal integrado (`Ctrl+` `). Confirme que está na raiz do projeto — o prompt deve mostrar a pasta onde ficam `app/`, `static/`, `Dockerfile`, etc.
3. Rode:

```bash
docker compose up --build
```

4. Aguarde. Na primeira vez demora uns 2 a 3 minutos (o Docker baixa a imagem do MySQL e instala as dependências Python). Nas próximas, leva uns 10 segundos.

5. Quando aparecer a mensagem **"Sistema SESI rodando!"** no terminal, está pronto.

---

## Como abrir o sistema no navegador

Depois que estiver rodando, você tem três formas de abrir:

**Forma 1 — mais rápida (pelo painel do VS Code):**

Na parte de baixo do VS Code, clique na aba **"Ports"** (fica ao lado de "Terminal"). Se não estiver visível, aperte `Ctrl+Shift+P` e escolha "Ports: Focus on Ports View". Você verá a porta `8000` listada. Clique no ícone de globo 🌐 ao lado dela — o navegador abre direto no sistema.

**Forma 2 — digitando no navegador:**

Abra seu navegador e acesse:

```
http://localhost:8000
```

**Forma 3 — pelo painel Docker:**

Clique no ícone 🐳 na barra lateral. Em **Containers**, você verá `sistema_sesi-app-1` e `sistema_sesi-db-1`. Passe o mouse em `app-1`; se estiver verde, está tudo funcionando. Clique com o botão direito em `app-1` → **"View Logs"** para ver o que está acontecendo.

**Para entrar no sistema:** use o usuário `admin` e a senha que você definiu em `ADMIN_DEFAULT_PASSWORD` no `.env`. No primeiro acesso, troque essa senha em "Painel Admin".

---

## Comandos do dia a dia

**Parar o sistema** (os dados do banco continuam salvos):

```bash
docker compose down
```

**Subir de novo** (não precisa buildar de novo se não mudou código):

```bash
docker compose up -d
```

**Ver os logs do sistema em tempo real:**

```bash
docker compose logs -f app
```

(Ou, pelo VS Code: botão direito em `app-1` no painel Docker → "View Logs".)

**Depois de alterar arquivos em `app/` ou `static/`**, reconstrua a imagem:

```bash
docker compose up -d --build
```

**Apagar tudo, inclusive os dados do banco** (use com cuidado — não tem volta):

```bash
docker compose down -v
```

**Entrar no terminal de dentro do container** (para inspecionar arquivos ou rodar algo pontual):

Pelo VS Code: botão direito em `app-1` → **"Attach Shell"**. Ou pelo terminal:

```bash
docker compose exec app bash
```

**Popular o banco com dados fictícios de teste** (não use em produção):

```bash
docker compose exec app python -m app.seed_teste --quantidade 300
```

---

## Problemas comuns

**"port is already allocated" ao subir**

A porta 8000 já está sendo usada por outro programa. Abra o `docker-compose.yml` e troque:

```yaml
ports:
  - "8080:8000"
```

Depois rode `docker compose up -d`. Você acessa em `http://localhost:8080`.

**"defina JWT_SECRET_KEY no .env"**

O arquivo `.env` está vazio ou não existe. Siga o passo 4 acima.

**O app reinicia em loop com "Can't connect to MySQL server"**

Geralmente é porque o MySQL ainda não terminou de iniciar. Rode `docker compose ps` e verifique se o serviço `db` aparece como `(healthy)`. Se não aparecer, veja os logs com `docker compose logs db`.

**A página abre mas o logo aparece quebrado**

O arquivo `static/sesi.png` está faltando na pasta do projeto. Coloque-o lá e rode `docker compose up -d --build` de novo.

**O terminal do VS Code diz "Docker daemon is not running"**

O Docker Desktop não está aberto. Inicie o programa e aguarde uns 30 segundos até o ícone da baleia ficar verde.

**Esqueci a senha do admin**

A senha só é usada **na primeira vez** que o admin é criado. Se você trocou e esqueceu, o jeito mais simples é apagar o volume do banco (`docker compose down -v`) e subir de novo — mas **isso apaga todos os dados**. Em produção, peça para outro admin resetar a senha pelo painel.

---

## Resumo rápido

Toda vez que você quiser usar o sistema:

1. Abra o projeto no VS Code.
2. Abra o terminal (`Ctrl+` `) e rode `docker compose up -d`.
3. Abra a aba **Ports** no VS Code e clique no globo da porta 8000.
4. Faça login.

Ao terminar, rode `docker compose down` (ou apenas feche o VS Code — os containers continuam rodando até você parar ou reiniciar o computador).

Os dados do banco ficam salvos no volume `mysql_data` e sobrevivem a reinicializações, atualizações e `down`/`up`. Só são perdidos se você rodar `docker compose down -v` de propósito.
