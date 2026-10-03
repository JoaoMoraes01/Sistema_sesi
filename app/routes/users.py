"""Rotas de usuário (Painel Admin): listar, criar, editar e apagar credenciais de acesso."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, UserRoleEnum
from app.schemas import UserCreate, UserResponse
from app.crud import add_log
from app.security import hash_password
from app.dependencies import require_admin

router = APIRouter(prefix="/api/users", tags=["Usuários"])


# Modelo auxiliar para atualizar usuário sem precisar mexer no schemas.py.
# ATENÇÃO: role usa UserRoleEnum (e não str solta) — antes, qualquer texto
# (ex: "superadmin") era aceito aqui e explodia no ENUM do MySQL, virando
# Erro 500. Com o enum, o Pydantic barra valores inválidos com erro 422.
class UserUpdate(BaseModel):
    name: Optional[str] = None
    pass_word: Optional[str] = None
    role: Optional[UserRoleEnum] = None


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    return db.query(User).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_route(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    existing = db.query(User).filter(User.login == user_in.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado.")

    new_user = User(
        name=user_in.name,
        login=user_in.login,
        pass_hash=hash_password(user_in.pass_word),
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    add_log(db, "Criação de Usuário", f"Usuário {new_user.login} cadastrado", current_user["name"])
    return new_user


@router.put("/{login}")
def update_user(
    login: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    user = db.query(User).filter(User.login == login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user_in.name:
        user.name = user_in.name
    if user_in.pass_word:
        user.pass_hash = hash_password(user_in.pass_word)
    if user_in.role:
        user.role = user_in.role

    db.commit()
    add_log(db, "Edição de Usuário", f"Usuário {user.login} atualizado", current_user["name"])
    return {"message": "Usuário atualizado com sucesso"}


@router.delete("/{login}")
def delete_user(
    login: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    user = db.query(User).filter(User.login == login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user.login == "admin":
        raise HTTPException(status_code=403, detail="Não é possível apagar o administrador principal.")

    db.delete(user)
    db.commit()
    add_log(db, "Exclusão de Usuário", f"Usuário {login} apagado", current_user["name"])
    return {"message": "Usuário removido"}