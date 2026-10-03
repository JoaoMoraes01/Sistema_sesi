"""Rotas do histórico de atividades (Painel Admin): consultar e limpar o log de auditoria."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HistoryLog
from app.schemas import HistoryLogResponse
from app.crud import clear_history
from app.dependencies import require_admin

router = APIRouter(prefix="/api/history", tags=["Histórico"])


@router.get("", response_model=List[HistoryLogResponse])
def get_history(db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    logs = db.query(HistoryLog).order_by(HistoryLog.created_at.desc()).all()
    return [
        HistoryLogResponse(
            id=log.id,
            date=log.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            action=log.action,
            details=log.details,
            user=log.user_name
        ) for log in logs
    ]


@router.delete("")
def clear_history_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    clear_history(db, current_user["name"])
    return {"message": "Histórico limpo com sucesso"}