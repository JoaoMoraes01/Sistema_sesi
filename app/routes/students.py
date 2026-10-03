"""Rotas de aluno: cadastro, fila ordenada por prioridade, edição e exclusão."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentResponse
from app.crud import create_student, get_ordered_queue, get_student_by_id, update_student, delete_student, find_student_by_cpf
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/students", tags=["Alunos"])


def build_student_response(st: Student, position: Optional[int] = None, status_vaga: Optional[str] = None) -> StudentResponse:
    """
    Monta o StudentResponse manualmente, campo a campo, em vez de usar
    StudentResponse.model_validate(st). Isso evita o ResponseValidationError (Erro 500)
    que ocorria no cadastro e mantém o mesmo comportamento já usado na fila.
    """
    return StudentResponse(
        id=st.id,
        timestamp=st.registration_date.strftime("%d/%m/%Y %H:%M:%S"),
        category=st.category,
        studentName=st.student_name,
        studentBirth=st.student_birth,
        studentRg=st.student_rg,
        studentCpf=st.student_cpf,
        studentNat=st.student_nat,
        studentGrade=st.student_grade,
        studentShift=st.student_shift,
        studentLaudo=st.student_laudo,
        laudoDesc=st.laudo_desc,
        irmaoQty=st.irmao_qty,
        possui_irmao=st.possui_irmao,
        irmaos=[{"id": i.id, "nome": i.nome, "serie": i.serie} for i in st.irmaos],
        respName=st.resp_name,
        respBirth=st.resp_birth,
        respRg=st.resp_rg,
        respCpf=st.resp_cpf,
        respNat=st.resp_nat,
        respAddress=st.resp_address,
        respNum=st.resp_num,
        respBairro=st.resp_bairro,
        respCep=st.resp_cep,
        respCivil=st.resp_civil,
        respEduc=st.resp_educ,
        respEmail=st.resp_email,
        respCompany=st.resp_company,
        respCnpj=st.resp_cnpj,
        telPai=st.tel_pai,
        emailPai=st.email_pai,
        telMae=st.tel_mae,
        emailMae=st.email_mae,
        telOutro=st.tel_outro,
        emailOutro=st.email_outro,
        respFin=st.resp_fin,
        respAcad=st.resp_acad,
        position=position,
        status_vaga=status_vaga,
    )


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def register_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. BLOQUEIO DE DUPLICATAS: Verifica se o CPF já existe (ignorando pontuação)
    if student_in.studentCpf:
        aluno_existente = find_student_by_cpf(db, student_in.studentCpf)
        if aluno_existente:
            raise HTTPException(status_code=400, detail="Este CPF já está na fila!")

    student = create_student(db, student_in, current_user["name"])

    # Monta a resposta manualmente (mesmo padrão da rota de fila), sem depender
    # de model_validate — isso é o que eliminava o Erro 500 e a duplicação no frontend.
    return build_student_response(student)


@router.get("/queue", response_model=List[StudentResponse])
def get_queue(total_vagas: int = 5, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    students_ordered = get_ordered_queue(db)
    response = []
    for idx, st in enumerate(students_ordered):
        item = build_student_response(
            st,
            position=idx + 1,
            status_vaga="VAGA GARANTIDA" if idx < total_vagas else "LISTA DE ESPERA"
        )
        response.append(item)
    return response


@router.put("/{student_id}", response_model=StudentResponse)
def edit_student(
    student_id: int,
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_student = get_student_by_id(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado.")

    # Bloqueia duplicidade de CPF apenas se o CPF mudou para um que já existe em outro registro
    if student_in.studentCpf:
        outro = find_student_by_cpf(db, student_in.studentCpf, exclude_id=student_id)
        if outro:
            raise HTTPException(status_code=400, detail="Este CPF já está na fila em outro cadastro!")

    updated = update_student(db, db_student, student_in, current_user["name"])
    return build_student_response(updated)


@router.delete("/{student_id}")
def remove_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_student = get_student_by_id(db, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado.")

    delete_student(db, db_student, current_user["name"])
    return {"message": "Cadastro removido com sucesso"}