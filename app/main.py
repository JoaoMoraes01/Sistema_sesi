"""
Ponto de entrada da aplicação.

As rotas em si moraram para app/routes/ (um arquivo por assunto: alunos,
usuários, histórico, lembretes, autenticação). Aqui só ficam: criação do
app, middlewares, inclusão dos routers e o "encaixe" do front-end estático.
"""
import socket
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base, SessionLocal
from app.crud import create_default_user
from app.routes import auth, students, users, history, reminders

# Pasta do front-end (index.html, script.js, style.css, sesi.png), servida pelo próprio FastAPI
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "static"


def get_local_ip() -> str | None:
    """
    Descobre o IP desta máquina na rede local (ex: 192.168.x.x), sem precisar
    abrir o ipconfig/ifconfig manualmente. Não faz nenhuma conexão de verdade
    (o socket UDP nunca chega a enviar nada) — é só um truque para perguntar
    ao sistema operacional "qual seria minha saída pra internet".
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criar tabelas automaticamente no MySQL (só cria as que faltam, não altera as existentes).
    # Fica aqui dentro (e não solto no topo do arquivo) para que só aconteça quando o
    # servidor realmente sobe — importar este módulo (como os testes automatizados fazem)
    # não deve, por si só, tentar abrir uma conexão com o banco de dados.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        create_default_user(db)
    finally:
        db.close()

    local_ip = get_local_ip()
    print("\n" + "=" * 55)
    print("Sistema SESI rodando!")
    print("  Nesta máquina:        http://127.0.0.1:8000")
    if local_ip:
        print(f"  De outro dispositivo na mesma rede: http://{local_ip}:8000")
    else:
        print("  Não foi possível detectar o IP da rede local.")
    print("=" * 55 + "\n")

    webbrowser.open("http://127.0.0.1:8000/")
    yield

app = FastAPI(title="API Gestão Escolar SESI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # O sistema não usa cookies (login é via token no header Authorization),
    # então não precisamos de allow_credentials nem de liberar geral com "*".
    # Restringimos a origens conhecidas: localhost (uso na própria máquina)
    # e qualquer rede local privada (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
    # acessando pela porta 8000 — cobre rede da escola, roteador de casa
    # ou hotspot de celular (Android e iPhone usam faixas diferentes entre si).
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):8000",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- ROTAS DA API (cada router cuida de um assunto — veja app/routes/) ---
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(users.router)
app.include_router(history.router)
app.include_router(reminders.router)

# --- FRONT-END ---
# Serve index.html, script.js, style.css e sesi.png direto pelo FastAPI.
# Precisa ser a ÚLTIMA coisa registrada no app: assim as rotas /api acima
# continuam funcionando normalmente, e tudo que não é /api cai aqui,
# devolvendo o index.html (html=True). É isso que permite abrir o sistema
# inteiro com um único comando, sem precisar de um Live Server separado.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)