"""
Popula o banco com cadastros FICTÍCIOS para testes do sistema.

Uso (a partir da pasta do projeto):

    python -m app.seed_teste              # gera 100 cadastros fictícios
    python -m app.seed_teste --quantidade 150

Regras deste script:
- Todos os nomes, telefones, e-mails, endereços e CPFs são gerados aleatoriamente.
  Nenhum dado real é usado. O CPF tem dígitos verificadores válidos apenas para
  passar nas validações do sistema.
- A geração usa uma semente fixa (SEED), então a base é sempre a mesma em
  qualquer computador. Assim, todo o grupo testa com os mesmos dados.
- É seguro rodar mais de uma vez: cada cadastro é identificado pelo CPF, e os
  que já existem no banco são pulados. Não há duplicação.
- Os cadastros são gravados com o usuário "seed_teste" no histórico, para ficar
  claro, na tela de Histórico, que foram criados por este script.
"""
import argparse
import random

from app.database import SessionLocal, engine, Base
from app.models import CategoryEnum, Student
from app.schemas import StudentCreate
from app.crud import create_student

SEED = 2026
USUARIO_SEED = "seed_teste"

PRIMEIROS = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Hugo", "Isabela",
             "João", "Karen", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Rafaela",
             "Samuel", "Tatiana", "Vinícius", "Yasmin", "Wesley", "Ícaro", "Júlia"]
SOBRENOMES = ["Almeida", "Barbosa", "Carvalho", "Dias", "Esteves", "Ferreira", "Gomes",
              "Haddad", "Iglesias", "Jardim", "Lopes", "Moreira", "Nogueira", "Oliveira",
              "Pereira", "Queiroz", "Ribeiro", "Santos", "Teixeira", "Vieira", "Xavier"]
RUAS = ["Rua das Flores", "Avenida Central", "Rua do Comércio", "Rua Projetada 3",
        "Travessa dos Lírios", "Rua Sete de Setembro", "Alameda das Acácias"]
BAIRROS = ["Centro", "Jardim Primavera", "Vila Nova", "Parque Verde", "Bela Vista"]
SERIES = ["Educação Infantil", "1º Ano Fundamental", "3º Ano Fundamental", "5º Ano Fundamental",
          "7º Ano Fundamental", "9º Ano Fundamental", "1º Ano Médio", "2º Ano Médio", "3º Ano Médio"]
TURNOS = ["Matutino", "Vespertino", "Qualquer turno"]
RESPONSAVEIS = ["Pai", "Mãe", "Avô/Avó", "Tio(a)", "Tutor(a) legal"]
ESCOLARIDADES = ["Fundamental II completo", "Médio incompleto", "Médio completo", "Superior completo"]
CIVIS = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "União Estável"]
CATEGORIAS = list(CategoryEnum)


def gerar_cpf(rng: random.Random) -> str:
    """CPF sintético com dígitos verificadores válidos (não pertence a ninguém)."""
    while True:
        base = [rng.randint(0, 9) for _ in range(9)]
        if len(set(base)) == 1:
            continue
        for _ in range(2):
            soma = sum(d * (len(base) + 1 - i) for i, d in enumerate(base))
            resto = (soma * 10) % 11
            base.append(0 if resto == 10 else resto)
        cpf = "".join(map(str, base))
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def gerar_telefone(rng: random.Random) -> str:
    return f"({rng.randint(11, 99)}) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"


def gerar_nome(rng: random.Random) -> str:
    return f"{rng.choice(PRIMEIROS)} {rng.choice(SOBRENOMES)}"


def gerar_cadastro(rng: random.Random, indice: int) -> StudentCreate:
    aluno = gerar_nome(rng)
    responsavel = gerar_nome(rng)
    tem_irmao = rng.random() < 0.3
    irmaos = []
    if tem_irmao:
        irmaos.append({"nome": gerar_nome(rng), "serie": rng.choice(SERIES)})
    cep = f"{rng.randint(10000, 99999)}-{rng.randint(100, 999)}"
    return StudentCreate(
        category=CATEGORIAS[indice % len(CATEGORIAS)],
        studentName=aluno,
        studentRg=f"{rng.randint(10000000, 99999999)}",
        studentCpf=gerar_cpf(rng),
        studentNat="Cidade Exemplo/UF",
        studentGrade=rng.choice(SERIES),
        studentShift=rng.choice(TURNOS),
        studentLaudo="Não",
        irmaoQty=len(irmaos),
        irmaos=irmaos,
        respName=responsavel,
        respRg=f"{rng.randint(10000000, 99999999)}",
        respCpf=gerar_cpf(rng),
        respNat="Cidade Exemplo/UF",
        respAddress=rng.choice(RUAS),
        respNum=str(rng.randint(1, 999)),
        respBairro=rng.choice(BAIRROS),
        respCep=cep,
        respCivil=rng.choice(CIVIS),
        respEduc=rng.choice(ESCOLARIDADES),
        respEmail=f"responsavel{indice}@exemplo.com",
        telPai=gerar_telefone(rng),
        emailPai=f"pai{indice}@exemplo.com",
        telMae=gerar_telefone(rng),
        emailMae=f"mae{indice}@exemplo.com",
        respFin=rng.choice(RESPONSAVEIS),
        respAcad=rng.choice(RESPONSAVEIS),
    )


def main():
    parser = argparse.ArgumentParser(description="Gera cadastros fictícios para teste.")
    parser.add_argument("--quantidade", type=int, default=100, help="quantidade total desejada (padrão: 100)")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    rng = random.Random(SEED)
    db = SessionLocal()
    try:
        cpfs_existentes = {c for (c,) in db.query(Student.student_cpf).all() if c}
        criados = 0
        pulados = 0
        for i in range(args.quantidade):
            cadastro = gerar_cadastro(rng, i)
            if cadastro.studentCpf in cpfs_existentes:
                pulados += 1
                continue
            create_student(db, cadastro, USUARIO_SEED)
            cpfs_existentes.add(cadastro.studentCpf)
            criados += 1
        total = db.query(Student).count()
        print(f"Cadastros fictícios criados: {criados}")
        print(f"Já existiam (pulados):       {pulados}")
        print(f"Total de alunos no banco:    {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
