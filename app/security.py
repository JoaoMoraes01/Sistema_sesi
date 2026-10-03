"""
Módulo de segurança: hash de senha (bcrypt) e tokens de login (JWT).

Fica tudo concentrado aqui em vez de espalhado pelas rotas — é mais fácil
de revisar e de explicar: "toda a lógica de segurança do sistema está
neste arquivo".
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# --- SENHAS ---
#
# Usamos a biblioteca `bcrypt` diretamente (em vez de passar por `passlib`).
# `passlib` está sem atualização há alguns anos e tem um conflito conhecido
# com versões recentes do `bcrypt` (o próprio bcrypt removeu um atributo
# interno que o passlib usava pra descobrir "qual versão é essa" — daí o
# erro "module bcrypt has no attribute __about__"). Falando direto com o
# bcrypt, esse problema não existe.

# bcrypt tem um limite de 72 bytes por senha — cortamos nesse tamanho para
# nunca dar erro, mesmo que alguém digite uma senha gigante.
_MAX_BCRYPT_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Transforma uma senha em texto puro num hash bcrypt (irreversível)."""
    password_bytes = plain_password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Confere se a senha digitada bate com o hash salvo no banco.

    Trata também o caso de contas antigas, criadas antes desta atualização,
    cuja senha ainda está salva em texto puro (ex: "123456" sem hash nenhum).
    Nesse caso, comparamos diretamente — e quem chamar esta função é
    responsável por re-salvar a senha já com hash (veja `migrate_password_to_hash`
    em crud.py), migrando a conta na hora do próximo login, sem quebrar o
    acesso de ninguém.
    """
    # Um hash bcrypt sempre começa com "$2b$" (ou variações "$2a$"/"$2y$").
    # Se não começa assim, é uma senha antiga, ainda em texto puro.
    if not stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        return plain_password == stored_hash

    password_bytes = plain_password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, stored_hash.encode("utf-8"))
    except ValueError:
        # Hash salvo corrompido ou em formato inesperado — trata como senha incorreta,
        # em vez de deixar o erro subir e quebrar a rota de login.
        return False


def is_legacy_plaintext(stored_hash: str) -> bool:
    """True se a senha salva ainda está em texto puro (conta antiga, não migrada)."""
    return not stored_hash.startswith(("$2a$", "$2b$", "$2y$"))


# --- TOKENS (JWT) ---

def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """
    Gera um token assinado contendo os dados do usuário logado (login, nome, papel)
    e uma data de expiração. O front-end guarda esse token e manda de volta em
    cada pedido, no cabeçalho Authorization.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Confere a assinatura e a validade do token. Retorna None se for inválido/expirado."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None