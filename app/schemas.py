from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime
from app.models import CategoryEnum, UserRoleEnum

# Sibling Schemas
class SiblingBase(BaseModel):
    nome: str
    serie: str

class SiblingCreate(SiblingBase):
    pass

class SiblingResponse(SiblingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Student Schemas
class StudentBase(BaseModel):
    category: CategoryEnum
    studentName: str
    studentBirth: Optional[str] = None
    studentRg: Optional[str] = None
    studentCpf: Optional[str] = None
    studentNat: Optional[str] = None
    studentGrade: str
    studentShift: str
    studentLaudo: str = "Não"
    laudoDesc: Optional[str] = None
    irmaoQty: int = 0
    irmaos: List[SiblingCreate] = []

    respName: str
    respBirth: Optional[str] = None
    respRg: Optional[str] = None
    respCpf: str
    respNat: Optional[str] = None
    respAddress: Optional[str] = None
    respNum: Optional[str] = None
    respBairro: Optional[str] = None
    respCep: Optional[str] = None
    respCivil: Optional[str] = None
    respEduc: Optional[str] = None
    respEmail: Optional[str] = None
    respCompany: Optional[str] = None
    respCnpj: Optional[str] = None
    telPai: Optional[str] = None
    emailPai: Optional[str] = None
    telMae: Optional[str] = None
    emailMae: Optional[str] = None
    telOutro: Optional[str] = None
    emailOutro: Optional[str] = None
    respFin: str
    respAcad: str

    # --- Validações de formato (mesma regra aplicada no front-end, agora
    # também conferida no servidor, já que o front-end pode ser burlado
    # por quem chamar a API diretamente, sem passar pela tela) ---

    @field_validator("respCep")
    @classmethod
    def validar_cep(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 8:
            raise ValueError("CEP inválido: precisa ter 8 dígitos (formato 00000-000)")
        return value

    @field_validator("telPai", "telMae", "telOutro")
    @classmethod
    def validar_telefone(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) not in (10, 11):
            raise ValueError("Telefone inválido: precisa ter 10 ou 11 dígitos (com DDD)")
        return value

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    timestamp: str = "" # <-- A correção salvadora está aqui!
    possui_irmao: bool
    position: Optional[int] = None
    status_vaga: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    name: str
    login: str
    role: UserRoleEnum

class UserCreate(UserBase):
    pass_word: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# History Log Schemas
class HistoryLogResponse(BaseModel):
    id: int
    date: str
    action: str
    details: str
    user: str

    model_config = ConfigDict(from_attributes=True)

# Reminder Schemas
class ReminderCreate(BaseModel):
    texto: str

class ReminderResponse(BaseModel):
    id: int
    texto: str
    createdAt: str
    concluido: bool
    concluidoEm: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)