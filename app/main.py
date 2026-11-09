"""
Ponto de entrada da aplicação.

As rotas em si moram em app/routes/ (um arquivo por assunto: alunos,
usuários, histórico, lembretes, autenticação). Aqui só ficam: criação do
app, middlewares, inclusão dos routers e o "encaixe" do front-end estático.
"""
import socket
import webbrowser
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base, SessionLocal
from app.crud import create_default_user
from app.migrations import run_migrations
from app.routes import auth, students, users, history, reminders

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "static"

def get_local_ip() -> str | None:
    """
    Descobre o IP desta máquina na rede local (ex: 192.168.x.x), sem precisar
    abrir o ipconfig/ifconfig manualmente.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Cria tabelas novas (só as que faltam).
    Base.metadata.create_all(bind=engine)
    # 2) Aplica colunas/índices novos em tabelas que já existem (ex: category_priority,
    #    student_cpf_digits) e faz o backfill. Idempotente — roda em toda subida.
    run_migrations(engine)

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

    open_browser_default = "false" if os.getenv("PORT") else "true"
    if os.getenv("OPEN_BROWSER", open_browser_default).lower() in {"1", "true", "yes"}:
        port = os.getenv("PORT", "8000")
        webbrowser.open(f"http://127.0.0.1:{port}/")
    yield

app = FastAPI(title="API Gestão Escolar SESI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):8000",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# --- ROTAS DA API ---
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(users.router)
app.include_router(history.router)
app.include_router(reminders.router)

# --- FRONT-END ---
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=not bool(os.getenv("PORT")),
    )
