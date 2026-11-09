import secrets
from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models import (
    Student, Sibling, HistoryLog, User, CategoryEnum, UserRoleEnum, Reminder,
)
from app.schemas import StudentCreate
from app.security import hash_password
from app.config import settings

# --- MAPEAMENTO DE PRIORIDADE DE CATEGORIA ---
# Usado para preencher `Student.category_priority`, que permite ORDER BY
# com índice composto (ver idx_queue_order em models.py).
CATEGORY_PRIORITY = {
    CategoryEnum.INDUSTRIARIO: 1,
    CategoryEnum.COLABORADOR: 2,
    CategoryEnum.EMPRESARIO: 3,
    CategoryEnum.CONVENIO: 4,
    CategoryEnum.COMUNIDADE: 5,
}

def _cpf_digits(cpf: str | None) -> str | None:
    """Normaliza CPF para comparação/busca: só dígitos."""
    if not cpf:
        return None
    digits = "".join(ch for ch in cpf if ch.isdigit())
    return digits or None

def find_student_by_cpf(db: Session, cpf: str, exclude_id: int = None):
    """
    Procura um aluno com o mesmo CPF, ignorando diferenças de formatação.

    Antes: carregava TODOS os alunos em memória e comparava em Python (O(n)
    por consulta, com deserialização de cada linha). Agora usa a coluna
    `student_cpf_digits` (indexada), resolvendo no banco em O(log n).
    """
    digits = _cpf_digits(cpf)
    if not digits:
        return None

    query = db.query(Student).filter(Student.student_cpf_digits == digits)
    if exclude_id is not None:
        query = query.filter(Student.id != exclude_id)
    return query.first()

def create_default_user(db: Session):
    """Cria o usuário 'admin' padrão caso não exista no banco de dados."""
    user_exists = db.query(User).filter(User.login == "admin").first()
    if user_exists:
        return

    senha_inicial = settings.ADMIN_DEFAULT_PASSWORD
    if not senha_inicial:
        senha_inicial = secrets.token_urlsafe(12)
        print("!" * 60)
        print("ATENCAO: ADMIN_DEFAULT_PASSWORD nao definida no .env.")
        print(f"Senha inicial do usuario 'admin' gerada: {senha_inicial}")
        print("Anote-a agora e troque-a no Painel Admin no primeiro acesso.")
        print("!" * 60)

    admin_user = User(
        name="Administrador",
        login="admin",
        pass_hash=hash_password(senha_inicial),
        role=UserRoleEnum.ADMIN,
    )
    db.add(admin_user)
    db.commit()

def migrate_password_to_hash(db: Session, user: User, plain_password: str):
    """Re-salva a senha de uma conta antiga já com hash, no primeiro login."""
    user.pass_hash = hash_password(plain_password)
    db.commit()

# --- HELPERS DE LOG ---

def _log_no_commit(db: Session, action: str, details: str, user_name: str) -> None:
    """Adiciona o log na sessão SEM commitar — quem chamou faz o commit único."""
    db.add(HistoryLog(action=action, details=details, user_name=user_name))

def add_log(db: Session, action: str, details: str, user_name: str):
    """
    Adiciona o log e commita na hora. Usado por fluxos com um único INSERT
    (ex: rotas de usuário). Para operações com vários INSERTs, use
    _log_no_commit antes do commit único.
    """
    _log_no_commit(db, action, details, user_name)
    db.commit()

# --- CRUD DE ALUNO ---

def create_student(db: Session, student_in: StudentCreate, user_name: str) -> Student:
    """
    Cadastra aluno + irmãos + log em UM ÚNICO commit.
    Antes eram 3 commits por aluno (500+ round-trips extras no seed de 300).
    """
    has_sibling = student_in.irmaoQty > 0 or len(student_in.irmaos) > 0

    db_student = Student(
        category=student_in.category,
        category_priority=CATEGORY_PRIORITY[student_in.category],
        student_name=student_in.studentName,
        student_birth=student_in.studentBirth,
        student_rg=student_in.studentRg,
        student_cpf=student_in.studentCpf,
        student_cpf_digits=_cpf_digits(student_in.studentCpf),
        student_nat=student_in.studentNat,
        student_grade=student_in.studentGrade,
        student_shift=student_in.studentShift,
        student_laudo=student_in.studentLaudo,
        laudo_desc=student_in.laudoDesc,
        irmao_qty=student_in.irmaoQty,
        possui_irmao=has_sibling,
        resp_name=student_in.respName,
        resp_birth=student_in.respBirth,
        resp_rg=student_in.respRg,
        resp_cpf=student_in.respCpf,
        resp_nat=student_in.respNat,
        resp_address=student_in.respAddress,
        resp_num=student_in.respNum,
        resp_bairro=student_in.respBairro,
        resp_cep=student_in.respCep,
        resp_civil=student_in.respCivil,
        resp_educ=student_in.respEduc,
        resp_email=student_in.respEmail,
        resp_company=student_in.respCompany,
        resp_cnpj=student_in.respCnpj,
        tel_pai=student_in.telPai,
        email_pai=student_in.emailPai,
        tel_mae=student_in.telMae,
        email_mae=student_in.emailMae,
        tel_outro=student_in.telOutro,
        email_outro=student_in.emailOutro,
        resp_fin=student_in.respFin,
        resp_acad=student_in.respAcad,
    )
    db.add(db_student)
    db.flush()  # força o INSERT para gerar o id, sem commitar

    for sib in student_in.irmaos:
        db.add(Sibling(student_id=db_student.id, nome=sib.nome, serie=sib.serie))

    _log_no_commit(
        db, "Novo Cadastro",
        f"Aluno: {db_student.student_name} ({db_student.category.value})",
        user_name,
    )

    db.commit()  # commit único
    db.refresh(db_student)
    return db_student

def get_ordered_queue(db: Session):
    """
    Fila ordenada pelos critérios de negócio:
    1. Categoria (prioridade numérica)
    2. Possui irmão (True antes de False)
    3. Data/hora de cadastro (mais antigo primeiro)

    Usa `selectinload(Student.irmaos)` para evitar N+1 queries (antes: 1 query
    por aluno só para buscar os irmãos), e ordena por `category_priority`
    (coluna indexada via idx_queue_order) em vez de `CASE(...)`, que o MySQL
    não consegue otimizar com índice.
    """
    query = (
        db.query(Student)
        .options(selectinload(Student.irmaos))
        .order_by(
            Student.category_priority.asc(),
            Student.possui_irmao.desc(),
            Student.registration_date.asc(),
        )
    )
    return query.all()

def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()

def update_student(db: Session, db_student: Student, student_in: StudentCreate, user_name: str) -> Student:
    """Atualiza todos os campos do aluno, substitui irmãos e loga — em UM commit."""
    has_sibling = student_in.irmaoQty > 0 or len(student_in.irmaos) > 0

    db_student.category = student_in.category
    db_student.category_priority = CATEGORY_PRIORITY[student_in.category]
    db_student.student_name = student_in.studentName
    db_student.student_birth = student_in.studentBirth
    db_student.student_rg = student_in.studentRg
    db_student.student_cpf = student_in.studentCpf
    db_student.student_cpf_digits = _cpf_digits(student_in.studentCpf)
    db_student.student_nat = student_in.studentNat
    db_student.student_grade = student_in.studentGrade
    db_student.student_shift = student_in.studentShift
    db_student.student_laudo = student_in.studentLaudo
    db_student.laudo_desc = student_in.laudoDesc
    db_student.irmao_qty = student_in.irmaoQty
    db_student.possui_irmao = has_sibling
    db_student.resp_name = student_in.respName
    db_student.resp_birth = student_in.respBirth
    db_student.resp_rg = student_in.respRg
    db_student.resp_cpf = student_in.respCpf
    db_student.resp_nat = student_in.respNat
    db_student.resp_address = student_in.respAddress
    db_student.resp_num = student_in.respNum
    db_student.resp_bairro = student_in.respBairro
    db_student.resp_cep = student_in.respCep
    db_student.resp_civil = student_in.respCivil
    db_student.resp_educ = student_in.respEduc
    db_student.resp_email = student_in.respEmail
    db_student.resp_company = student_in.respCompany
    db_student.resp_cnpj = student_in.respCnpj
    db_student.tel_pai = student_in.telPai
    db_student.email_pai = student_in.emailPai
    db_student.tel_mae = student_in.telMae
    db_student.email_mae = student_in.emailMae
    db_student.tel_outro = student_in.telOutro
    db_student.email_outro = student_in.emailOutro
    db_student.resp_fin = student_in.respFin
    db_student.resp_acad = student_in.respAcad

    # Substitui irmãos (remove antigos e insere novos). O flush força o DELETE
    # antes dos INSERTs, evitando qualquer conflito residual.
    for sib in list(db_student.irmaos):
        db.delete(sib)
    db.flush()
    for sib in student_in.irmaos:
        db.add(Sibling(student_id=db_student.id, nome=sib.nome, serie=sib.serie))

    _log_no_commit(
        db, "Edição de Cadastro",
        f"Aluno: {db_student.student_name} ({db_student.category.value})",
        user_name,
    )

    db.commit()
    db.refresh(db_student)
    return db_student

def delete_student(db: Session, db_student: Student, user_name: str):
    nome = db_student.student_name
    categoria = db_student.category.value
    db.delete(db_student)
    _log_no_commit(db, "Exclusão de Cadastro", f"Aluno: {nome} ({categoria})", user_name)
    db.commit()

def clear_history(db: Session, user_name: str):
    db.query(HistoryLog).delete()
    _log_no_commit(db, "Limpeza de Histórico",
                   "Todo o histórico de atividades foi apagado", user_name)
    db.commit()

# --- LEMBRETES ---

def create_reminder(db: Session, texto: str, owner_login: str) -> Reminder:
    reminder = Reminder(texto=texto, owner_login=owner_login)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

def get_reminders(db: Session, owner_login: str):
    """Pendentes primeiro (mais antigo primeiro), depois os concluídos (mais recente primeiro)."""
    pendentes = db.query(Reminder).filter(
        Reminder.owner_login == owner_login, Reminder.concluido == False
    ).order_by(Reminder.created_at.asc()).all()

    concluidos = db.query(Reminder).filter(
        Reminder.owner_login == owner_login, Reminder.concluido == True
    ).order_by(Reminder.concluido_em.desc()).all()

    return pendentes + concluidos

def get_reminder_by_id(db: Session, reminder_id: int, owner_login: str) -> Reminder | None:
    return db.query(Reminder).filter(
        Reminder.id == reminder_id, Reminder.owner_login == owner_login
    ).first()

def set_reminder_status(db: Session, reminder: Reminder, concluido: bool) -> Reminder:
    reminder.concluido = concluido
    reminder.concluido_em = datetime.now() if concluido else None
    db.commit()
    db.refresh(reminder)
    return reminder

def delete_reminder(db: Session, reminder: Reminder):
    db.delete(reminder)
    db.commit()

def clear_completed_reminders(db: Session, owner_login: str):
    db.query(Reminder).filter(
        Reminder.owner_login == owner_login, Reminder.concluido == True
    ).delete()
    db.commit()
