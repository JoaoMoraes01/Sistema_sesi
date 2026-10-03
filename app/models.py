import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class CategoryEnum(str, enum.Enum):
    INDUSTRIARIO = "Industriário"
    COLABORADOR = "Colaborador"
    EMPRESARIO = "Empresário Industrial"
    CONVENIO = "Convênio"
    COMUNIDADE = "Comunidade"

class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

# --- TABELA DE USUÁRIOS ---
class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    login = Column(String(100), unique=True, index=True, nullable=False)
    pass_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

# --- TABELA DE CANDIDATOS / ALUNOS ---
class Student(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    registration_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    
    # Dados do Candidato
    student_name = Column(String(200), nullable=False)
    student_birth = Column(String(20), nullable=True)
    student_rg = Column(String(30), nullable=True)
    student_cpf = Column(String(20), nullable=True, index=True)
    student_nat = Column(String(100), nullable=True)
    student_grade = Column(String(100), nullable=False)
    student_shift = Column(String(50), nullable=False)
    student_laudo = Column(String(10), default="Não")
    laudo_desc = Column(Text, nullable=True)
    
    # Regra de Negócio: Bônus de Irmão
    irmao_qty = Column(Integer, default=0)
    possui_irmao = Column(Boolean, default=False, index=True)

    # Dados do Responsável Legal
    resp_name = Column(String(200), nullable=False)
    resp_birth = Column(String(20), nullable=True)
    resp_rg = Column(String(30), nullable=True)
    resp_cpf = Column(String(20), nullable=False)
    resp_nat = Column(String(100), nullable=True)
    resp_address = Column(String(255), nullable=True)
    resp_num = Column(String(20), nullable=True)
    resp_bairro = Column(String(100), nullable=True)
    resp_cep = Column(String(20), nullable=True)
    resp_civil = Column(String(50), nullable=True)
    resp_educ = Column(String(100), nullable=True)
    resp_email = Column(String(150), nullable=True)
    resp_company = Column(String(150), nullable=True)
    resp_cnpj = Column(String(30), nullable=True)
    tel_pai = Column(String(30), nullable=True)
    email_pai = Column(String(150), nullable=True)
    tel_mae = Column(String(30), nullable=True)
    email_mae = Column(String(150), nullable=True)
    tel_outro = Column(String(30), nullable=True)
    email_outro = Column(String(150), nullable=True)
    resp_fin = Column(String(50), nullable=False)
    resp_acad = Column(String(50), nullable=False)

    # Relacionamentos
    irmaos = relationship("Sibling", back_populates="student", cascade="all, delete-orphan")

# --- TABELA DE IRMÃOS DETALHADOS ---
class Sibling(Base):
    __tablename__ = "irmaos"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(200), nullable=False)
    serie = Column(String(100), nullable=False)

    student = relationship("Student", back_populates="irmaos")

# --- TABELA DE HISTÓRICO DE LOGS ---
class HistoryLog(Base):
    __tablename__ = "historico_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    user_name = Column(String(150), nullable=False)

# --- TABELA DE LEMBRETES (pessoal, por usuário) ---
class Reminder(Base):
    __tablename__ = "lembretes"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(Text, nullable=False)
    owner_login = Column(String(100), nullable=False, index=True)  # login de quem criou (cada um vê só os seus)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    concluido = Column(Boolean, default=False, index=True)
    concluido_em = Column(DateTime, nullable=True)