import re
from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional
from datetime import datetime
from app.models import CategoryEnum, UserRoleEnum

# --- CONSTANTES DE VALIDAÇÃO (fonte única de verdade) ---
# Se precisar mudar uma regra, muda aqui — e o backend inteiro segue.

NOME_RE = re.compile(r"^[A-Za-zÀ-ÿ' \-]+$")

GRADES_PERMITIDAS = {
    "Educação Infantil",
    "1º Ano Fundamental", "2º Ano Fundamental", "3º Ano Fundamental",
    "4º Ano Fundamental", "5º Ano Fundamental", "6º Ano Fundamental",
    "7º Ano Fundamental", "8º Ano Fundamental", "9º Ano Fundamental",
    "1º Ano Médio", "2º Ano Médio", "3º Ano Médio",
}

ESCOLARIDADES_PERMITIDAS = {
    "Fundamental I incompleto", "Fundamental I completo",
    "Fundamental II incompleto", "Fundamental II completo",
    "Médio incompleto", "Médio completo",
    "Superior incompleto", "Superior completo", "Pós-graduação",
}

RESPONSAVEIS_PERMITIDOS = {
    "Pai", "Mãe", "Avô/Avó", "Tio(a)", "Irmão(ã) maior",
    "Tutor(a) legal", "Guardião(ã) judicial",
}

CIVIS_PERMITIDOS = {
    "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável",
}


# Sibling Schemas
class SiblingBase(BaseModel):
    nome: str = Field(..., max_length=200)
    serie: str = Field(..., max_length=100)

    @field_validator("nome")
    @classmethod
    def validar_nome_irmao(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("Nome do irmão muito curto (mínimo 3 caracteres).")
        if not NOME_RE.match(v):
            raise ValueError("Nome do irmão deve conter apenas letras, espaços, hífen e apóstrofo.")
        return v

    @field_validator("serie")
    @classmethod
    def validar_serie(cls, v: str) -> str:
        if v not in GRADES_PERMITIDAS:
            raise ValueError("Série do irmão inválida.")
        return v


class SiblingCreate(SiblingBase):
    pass


class SiblingResponse(SiblingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Student Schemas
class StudentBase(BaseModel):
    # --- Dados do candidato ---
    category: CategoryEnum
    studentName: str = Field(..., max_length=200)
    studentBirth: Optional[str] = Field(None, max_length=20)
    studentRg: Optional[str] = Field(None, max_length=30)
    studentCpf: Optional[str] = Field(None, max_length=20)
    studentNat: Optional[str] = Field(None, max_length=100)
    studentGrade: str = Field(..., max_length=100)
    studentShift: str = Field(..., max_length=50)
    studentLaudo: str = Field("Não", max_length=10)
    laudoDesc: Optional[str] = Field(None, max_length=1000)
    irmaoQty: int = 0
    irmaos: List[SiblingCreate] = []

    # --- Dados do responsável legal ---
    respName: str = Field(..., max_length=200)
    respBirth: Optional[str] = Field(None, max_length=20)
    respRg: Optional[str] = Field(None, max_length=30)
    respCpf: str = Field(..., max_length=20)
    respNat: Optional[str] = Field(None, max_length=100)
    respAddress: Optional[str] = Field(None, max_length=255)
    respNum: Optional[str] = Field(None, max_length=20)
    respBairro: Optional[str] = Field(None, max_length=100)
    respCep: Optional[str] = Field(None, max_length=20)
    respCivil: Optional[str] = Field(None, max_length=50)
    respEduc: Optional[str] = Field(None, max_length=100)
    respEmail: Optional[str] = Field(None, max_length=150)
    respCompany: Optional[str] = Field(None, max_length=150)
    respCnpj: Optional[str] = Field(None, max_length=30)
    telPai: Optional[str] = Field(None, max_length=30)
    emailPai: Optional[str] = Field(None, max_length=150)
    telMae: Optional[str] = Field(None, max_length=30)
    emailMae: Optional[str] = Field(None, max_length=150)
    telOutro: Optional[str] = Field(None, max_length=30)
    emailOutro: Optional[str] = Field(None, max_length=150)
    respFin: str = Field(..., max_length=50)
    respAcad: str = Field(..., max_length=50)

    # --- Validações de formato (mesma regra aplicada no front-end, agora
    # também conferida no servidor, já que o front-end pode ser burlado
    # por quem chamar a API diretamente, sem passar pela tela) ---

    @field_validator("studentName", "respName")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("Nome muito curto (mínimo 3 caracteres).")
        if not NOME_RE.match(v):
            raise ValueError("Nome deve conter apenas letras, espaços, hífen e apóstrofo.")
        return v

    @field_validator("studentRg", "respRg")
    @classmethod
    def validar_rg(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 5 or len(digits) > 12:
            raise ValueError("RG inválido: precisa ter entre 5 e 12 dígitos.")
        return v

    @field_validator("studentGrade")
    @classmethod
    def validar_serie_aluno(cls, v: str) -> str:
        if v == "Outro":
            return v
        if v not in GRADES_PERMITIDAS:
            raise ValueError("Série/ano inválido(a).")
        return v

    @field_validator("respEduc")
    @classmethod
    def validar_escolaridade(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v not in ESCOLARIDADES_PERMITIDAS:
            raise ValueError("Grau de escolaridade inválido.")
        return v

    @field_validator("respCivil")
    @classmethod
    def validar_civil(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        # "Outro" com texto livre é válido — mas se for uma opção fixa,
        # precisa bater com a lista.
        if v in CIVIS_PERMITIDOS:
            return v
        # Aceita texto livre (campo "Outro" digitado) — só limita tamanho.
        return v

    @field_validator("respFin", "respAcad")
    @classmethod
    def validar_responsavel(cls, v: str) -> str:
        if not v:
            raise ValueError("Informe o responsável.")
        if v in RESPONSAVEIS_PERMITIDOS:
            return v
        # Se não é uma opção fixa, é o texto livre do "Outro" — já limitado por max_length=50.
        return v

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
    timestamp: str = ""
    possui_irmao: bool
    position: Optional[int] = None
    status_vaga: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# User Schemas
class UserBase(BaseModel):
    name: str = Field(..., max_length=150)
    login: str = Field(..., max_length=100)
    role: UserRoleEnum


class UserCreate(UserBase):
    pass_word: str = Field(..., max_length=72)


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
    texto: str = Field(..., max_length=500)


class ReminderResponse(BaseModel):
    id: int
    texto: str
    createdAt: str
    concluido: bool
    concluidoEm: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
