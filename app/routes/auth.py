"""Rota de login. Gera o token JWT que todas as outras rotas protegidas exigem."""
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.security import verify_password, is_legacy_plaintext, create_access_token
from app.crud import migrate_password_to_hash

router = APIRouter(tags=["Autenticação"])


class UserLogin(BaseModel):
    username: str
    password: str


# --- PROTEÇÃO CONTRA FORÇA BRUTA NO LOGIN ---
#
# Guarda, em memória, os horários das últimas tentativas ERRADAS de login
# por usuário. Se alguém errar demais em pouco tempo, bloqueia por alguns
# minutos — mesmo que acerte a senha certa durante o bloqueio.
#
# É simples de propósito (não usa Redis/banco): reinicia quando o servidor
# reinicia, o que é aceitável para este sistema (uso interno, poucos
# usuários). Se algum dia o sistema for exposto além da rede interna da
# escola, vale trocar por uma solução com estado persistente (ex: Redis).
_MAX_TENTATIVAS = 5
_JANELA_BLOQUEIO_SEGUNDOS = 5 * 60  # 5 minutos

_tentativas_falhas: dict[str, list[float]] = defaultdict(list)


def _checar_bloqueio(username: str):
    agora = time.time()
    tentativas = _tentativas_falhas[username]
    # Descarta tentativas antigas, fora da janela de bloqueio
    tentativas[:] = [t for t in tentativas if agora - t < _JANELA_BLOQUEIO_SEGUNDOS]

    if len(tentativas) >= _MAX_TENTATIVAS:
        espera_min = int((_JANELA_BLOQUEIO_SEGUNDOS - (agora - tentativas[0])) / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas de login com este usuário. Tente novamente em cerca de {espera_min} minuto(s)."
        )


def _registrar_falha(username: str):
    _tentativas_falhas[username].append(time.time())


def _limpar_falhas(username: str):
    _tentativas_falhas.pop(username, None)


@router.post("/api/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    _checar_bloqueio(credentials.username)

    user = db.query(User).filter(User.login == credentials.username).first()

    if not user or not verify_password(credentials.password, user.pass_hash):
        _registrar_falha(credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos"
        )

    _limpar_falhas(credentials.username)

    # Conta antiga, criada antes da atualização de segurança: a senha ainda está
    # em texto puro no banco. Como o login deu certo, aproveitamos para já salvar
    # com hash — na próxima vez, essa conta já entra pelo caminho seguro.
    if is_legacy_plaintext(user.pass_hash):
        migrate_password_to_hash(db, user, credentials.password)

    token = create_access_token({"sub": user.login, "name": user.name, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "username": user.login, "role": user.role, "name": user.name}