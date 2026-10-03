import secrets
from sqlalchemy.orm import Session
from sqlalchemy import case, asc
from app.models import Student, Sibling, HistoryLog, User, CategoryEnum, UserRoleEnum, Reminder
from app.schemas import StudentCreate, UserCreate
from datetime import datetime
from app.security import hash_password
from app.config import settings

# --- MAPEAMENTO DE PRIORIDADE DE CATEGORIA ---
CATEGORY_PRIORITY = {
    CategoryEnum.INDUSTRIARIO: 1,
    CategoryEnum.COLABORADOR: 2,
    CategoryEnum.EMPRESARIO: 3,
    CategoryEnum.CONVENIO: 4,
    CategoryEnum.COMUNIDADE: 5
}

def find_student_by_cpf(db: Session, cpf: str, exclude_id: int = None):
    """
    Procura um aluno com o mesmo CPF, ignorando diferenças de formatação
    (com ou sem pontos/traço) — assim, "529.982.247-25" e "52998224725"
    são reconhecidos como o mesmo CPF na hora de checar duplicidade.
    """
    digits = "".join(ch for ch in (cpf or "") if ch.isdigit())
    if not digits:
        return None

    query = db.query(Student).filter(Student.student_cpf.isnot(None))
    if exclude_id is not None:
        query = query.filter(Student.id != exclude_id)

    for student in query.all():
        student_digits = "".join(ch for ch in (student.student_cpf or "") if ch.isdigit())
        if student_digits == digits:
            return student
    return None

def create_default_user(db: Session):
    """Cria o usuário 'admin' padrão caso não exista no banco de dados."""
    user_exists = db.query(User).filter(User.login == "admin").first()
    if user_exists:
        return

    # A senha inicial NÃO fica mais escrita aqui no código (qualquer pessoa com
    # acesso aos arquivos do projeto — zip, pen drive, GitHub — conheceria a
    # senha do administrador). Ela vem do arquivo .env (ADMIN_DEFAULT_PASSWORD).
    senha_inicial = settings.ADMIN_DEFAULT_PASSWORD
    if not senha_inicial:
        # Se ninguém definiu no .env, geramos uma senha aleatória forte e
        # mostramos UMA vez aqui no console do servidor — ela nunca fica salva
        # em texto puro em lugar nenhum (no banco vai só o hash bcrypt).
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
        role=UserRoleEnum.ADMIN
    )
    db.add(admin_user)
    db.commit()

def migrate_password_to_hash(db: Session, user: User, plain_password: str):
    """
    Re-salva a senha de uma conta antiga (ainda em texto puro) já com hash,
    na hora do login — sem precisar de nenhum passo manual e sem derrubar
    o acesso de ninguém.
    """
    user.pass_hash = hash_password(plain_password)
    db.commit()

def create_student(db: Session, student_in: StudentCreate, user_name: str) -> Student:
    # Regra: Se tem 1 ou mais irmãos, possui_irmao = True (Bônus único)
    has_sibling = student_in.irmaoQty > 0 or len(student_in.irmaos) > 0

    db_student = Student(
        category=student_in.category,
        student_name=student_in.studentName,
        student_birth=student_in.studentBirth,
        student_rg=student_in.studentRg,
        student_cpf=student_in.studentCpf,
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
    db.commit()
    db.refresh(db_student)

    # Cadastro dos irmãos detalhados
    for sib in student_in.irmaos:
        db_sib = Sibling(student_id=db_student.id, nome=sib.nome, serie=sib.serie)
        db.add(db_sib)

    db.commit()
    
    # Registrar no Histórico
    add_log(db, "Novo Cadastro", f"Aluno: {db_student.student_name} ({db_student.category.value})", user_name)
    return db_student

def get_ordered_queue(db: Session):
    """
    Ordenação da fila conforme as especificações de negócio:
    1. Categoria (1 a 5)
    2. Possui Irmão (True [1] antes de False [0])
    3. Data/Hora de cadastro (Mais antigo primeiro)
    """
    category_order = case(
        (Student.category == CategoryEnum.INDUSTRIARIO, 1),
        (Student.category == CategoryEnum.COLABORADOR, 2),
        (Student.category == CategoryEnum.EMPRESARIO, 3),
        (Student.category == CategoryEnum.CONVENIO, 4),
        (Student.category == CategoryEnum.COMUNIDADE, 5),
        else_=99
    )

    query = db.query(Student).order_by(
        category_order.asc(),
        Student.possui_irmao.desc(),
        Student.registration_date.asc()
    )
    
    return query.all()

def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()

def update_student(db: Session, db_student: Student, student_in: StudentCreate, user_name: str) -> Student:
    """Atualiza todos os campos do aluno e substitui a lista de irmãos."""
    has_sibling = student_in.irmaoQty > 0 or len(student_in.irmaos) > 0

    db_student.category = student_in.category
    db_student.student_name = student_in.studentName
    db_student.student_birth = student_in.studentBirth
    db_student.student_rg = student_in.studentRg
    db_student.student_cpf = student_in.studentCpf
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

    # Substitui os irmãos detalhados (remove os antigos e insere os novos)
    for sib in list(db_student.irmaos):
        db.delete(sib)
    db.flush()
    for sib in student_in.irmaos:
        db.add(Sibling(student_id=db_student.id, nome=sib.nome, serie=sib.serie))

    db.commit()
    db.refresh(db_student)

    add_log(db, "Edição de Cadastro", f"Aluno: {db_student.student_name} ({db_student.category.value})", user_name)
    return db_student

def delete_student(db: Session, db_student: Student, user_name: str):
    nome = db_student.student_name
    categoria = db_student.category.value
    db.delete(db_student)
    db.commit()
    add_log(db, "Exclusão de Cadastro", f"Aluno: {nome} ({categoria})", user_name)

def clear_history(db: Session, user_name: str):
    db.query(HistoryLog).delete()
    db.commit()
    add_log(db, "Limpeza de Histórico", "Todo o histórico de atividades foi apagado", user_name)

def add_log(db: Session, action: str, details: str, user_name: str):
    log = HistoryLog(action=action, details=details, user_name=user_name)
    db.add(log)
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