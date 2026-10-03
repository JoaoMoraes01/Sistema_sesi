"""
Dependências do FastAPI usadas para proteger rotas.

Ficam separadas em um arquivo próprio (em vez de dentro de main.py ou de um
router específico) porque são usadas por VÁRIOS routers diferentes
(students, users, history, reminders) — colocar aqui evita que um arquivo
de rotas precise importar de outro arquivo de rotas só para pegar essas
funções emprestadas.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.security import decode_access_token

# HTTPBearer extrai o token do cabeçalho "Authorization: Bearer <token>".
# auto_error=False para podermos devolver uma mensagem em português (em vez do
# erro genérico do FastAPI) quando o cabeçalho não vier.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Dependência usada em TODA rota que exige login. O FastAPI roda isto antes
    de executar a rota — se o token não vier, estiver errado ou tiver expirado,
    a requisição é barrada aqui, com 401, e a rota nem chega a ser executada.
    Esta é a verificação que faltava: antes, a "proteção" existia só no JavaScript.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado. Faça login novamente.")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada. Faça login novamente.")

    return {"login": payload.get("sub"), "name": payload.get("name"), "role": payload.get("role")}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Igual a get_current_user, mas também exige que o papel seja admin (Painel Admin, Histórico)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores podem fazer isso.")
    return current_user