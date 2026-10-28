FROM python:3.12-slim

# Boas práticas: sem .pyc, logs sem buffer, sem cache do pip, sem abrir navegador
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OPEN_BROWSER=false

WORKDIR /app

# curl só é usado pelo HEALTHCHECK abaixo
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências primeiro (aproveita o cache de layer do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código preservando a estrutura app/ + static/ lado a lado
COPY app/ ./app/
COPY static/ ./static/

# Usuário não-root (boa prática de segurança)
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

# Executa o uvicorn "por fora" do módulo (mesma coisa que iniciar.sh faz,
# mas sem --reload, que é só para desenvolvimento)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]