"""Rotas de lembretes: anotações pessoais do usuário logado (cada um só vê os seus)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import ReminderCreate, ReminderResponse
from app.crud import (
    create_reminder,
    get_reminders,
    get_reminder_by_id,
    set_reminder_status,
    delete_reminder,
    clear_completed_reminders,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/reminders", tags=["Lembretes"])


class ReminderStatusUpdate(BaseModel):
    concluido: bool


@router.get("", response_model=List[ReminderResponse])
def list_reminders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    reminders = get_reminders(db, current_user["login"])
    return [
        ReminderResponse(
            id=r.id,
            texto=r.texto,
            createdAt=r.created_at.strftime("%d/%m/%Y %H:%M"),
            concluido=r.concluido,
            concluidoEm=r.concluido_em.strftime("%d/%m/%Y %H:%M") if r.concluido_em else None,
        ) for r in reminders
    ]


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def add_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not reminder_in.texto.strip():
        raise HTTPException(status_code=400, detail="O lembrete não pode estar vazio.")

    r = create_reminder(db, reminder_in.texto.strip(), current_user["login"])
    return ReminderResponse(
        id=r.id,
        texto=r.texto,
        createdAt=r.created_at.strftime("%d/%m/%Y %H:%M"),
        concluido=r.concluido,
        concluidoEm=None,
    )


@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder_status(
    reminder_id: int,
    status_in: ReminderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    reminder = get_reminder_by_id(db, reminder_id, current_user["login"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado.")

    r = set_reminder_status(db, reminder, status_in.concluido)
    return ReminderResponse(
        id=r.id,
        texto=r.texto,
        createdAt=r.created_at.strftime("%d/%m/%Y %H:%M"),
        concluido=r.concluido,
        concluidoEm=r.concluido_em.strftime("%d/%m/%Y %H:%M") if r.concluido_em else None,
    )


@router.delete("/{reminder_id}")
def remove_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    reminder = get_reminder_by_id(db, reminder_id, current_user["login"])
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado.")

    delete_reminder(db, reminder)
    return {"message": "Lembrete removido"}


@router.delete("")
def remove_completed_reminders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    clear_completed_reminders(db, current_user["login"])
    return {"message": "Lembretes concluídos apagados"}