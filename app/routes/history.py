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

# Limite de linhas retornadas por consulta. Sem isso, cada abertura da aba
# baixava TODOS os logs (potencialmente milhares, e crescendo para sempre).
# 200 cobre o uso do dia e mantém o payload leve; se um dia precisar ver mais
# antigos, adicione paginação com cursor `before_id`.
_HISTORY_LIMIT = 200

@router.get("", response_model=List[HistoryLogResponse])
def get_history(db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    # Ordenar por `id DESC` em vez de `created_at DESC`: o id é PK indexada,
    # o MySQL retorna as N linhas mais recentes sem precisar varrer/ordenar a
    # tabela inteira (created_at não tem índice).
    logs = (
        db.query(HistoryLog)
        .order_by(HistoryLog.id.desc())
        .limit(_HISTORY_LIMIT)
        .all()
    )
    return [
        HistoryLogResponse(
            id=log.id,
            date=log.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            action=log.action,
            details=log.details,
            user=log.user_name,
        )
        for log in logs
    ]

@router.delete("")
def clear_history_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    clear_history(db, current_user["name"])
    return {"message": "Histórico limpo com sucesso"}
