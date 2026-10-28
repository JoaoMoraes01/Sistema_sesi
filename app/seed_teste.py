"""
Popula o banco com cadastros FICTÍCIOS para testes do sistema.

Uso (a partir da pasta do projeto):

    python -m app.seed_teste              # gera 300 cadastros fictícios
    python -m app.seed_teste --quantidade 500

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
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.models import CategoryEnum, Student, HistoryLog
from app.schemas import StudentCreate
from app.crud import create_student

SEED = 2026
USUARIO_SEED = "seed_teste"

PRIMEIROS = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Hugo", "Isabela", "João",
    "Karen", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Rafaela", "Samuel", "Tatiana",
    "Vinícius", "Yasmin", "Wesley", "Ícaro", "Júlia", "Aline", "Bianca", "Caio", "Débora", "Eduardo",
    "Fernanda", "Gustavo", "Helena", "Igor", "Joana", "Kaique", "Letícia", "Marcos", "Natália",
    "Otávio", "Priscila", "Renan", "Sofia", "Tiago", "Úrsula", "Valentina", "Wagner", "Xênia",
    "Yuri", "Zélia", "Adriano", "Beatriz", "Cássio", "Dalila", "Emanuel", "Flávia", "Guilherme",
    "Heloísa", "Ícaro", "Jéssica", "Kléber", "Lívia", "Márcio", "Noêmia", "Orlando", "Patrícia",
]
SOBRENOMES = [
    "Almeida", "Barbosa", "Carvalho", "Dias", "Esteves", "Ferreira", "Gomes", "Haddad", "Iglesias",
    "Jardim", "Lopes", "Moreira", "Nogueira", "Oliveira", "Pereira", "Queiroz", "Ribeiro", "Santos",
    "Teixeira", "Vieira", "Xavier", "Albuquerque", "Brandão", "Cardoso", "Duarte", "Espíndola",
    "Fagundes", "Gonçalves", "Hermann", "Ibrahim", "Junqueira", "Kozlowski", "Lacerda", "Machado",
    "Naves", "Ortega", "Peixoto", "Quintela", "Rocha", "Sampaio", "Tavares", "Uchôa", "Valadares",
    "Wanderley", "Yamamoto", "Zanetti", "Aguiar", "Bezerra", "Cavalcanti", "Drummond", "Efraim",
]
RUAS = [
    "Rua das Flores", "Avenida Central", "Rua do Comércio", "Rua Projetada 3", "Travessa dos Lírios",
    "Rua Sete de Setembro", "Alameda das Acácias", "Avenida dos Ipês", "Rua Bela Vista",
    "Rua dos Pinheiros", "Avenida Brasil", "Rua Quinze de Novembro", "Travessa do Porto",
    "Rua Santa Clara", "Avenida das Palmeiras", "Rua dos Girassóis", "Alameda Rio Branco",
    "Rua Major Cardoso", "Avenida Paulista Norte", "Travessa Esperança",
]
BAIRROS = [
    "Centro", "Jardim Primavera", "Vila Nova", "Parque Verde", "Bela Vista", "Jardim Europa",
    "Morada do Sol", "Conjunto Habitacional Norte", "Vila Industrial", "Jardim das Oliveiras",
    "Vila Esperança", "Recanto dos Pássaros", "Parque das Águas", "Setor Sul", "Vila Operária",
]
CIDADES = [
    "Cidade Alfa/SP", "Cidade Beta/MG", "Cidade Gama/RJ", "Cidade Delta/PR", "Cidade Épsilon/BA",
    "Cidade Zeta/RS", "Cidade Eta/SC", "Cidade Teta/GO", "Cidade Iota/PE", "Cidade Kappa/CE",
    "Cidade Lambda/PA", "Cidade Mu/AM",
]
DESCRICOES_LAUDO = [
    "Asma leve", "Dificuldade de visão", "TDAH em acompanhamento", "Alergia alimentar", "Dislexia",
    "Diabetes tipo 1", "Epilepsia controlada", "Deficiência auditiva leve", "Hipotireoidismo",
    "Restrição a amendoim",
]
SERIES = [
    "Educação Infantil", "1º Ano Fundamental", "2º Ano Fundamental", "3º Ano Fundamental",
    "4º Ano Fundamental", "5º Ano Fundamental", "6º Ano Fundamental", "7º Ano Fundamental",
    "8º Ano Fundamental", "9º Ano Fundamental", "1º Ano Médio", "2º Ano Médio", "3º Ano Médio",
]
TURNOS = ["Matutino", "Vespertino", "Qualquer turno"]
RESPONSAVEIS = [
    "Pai", "Mãe", "Avô/Avó", "Tio(a)", "Irmão(ã) maior", "Tutor(a) legal", "Guardião(ã) judicial",
]
ESCOLARIDADES = [
    "Fundamental I incompleto", "Fundamental I completo", "Fundamental II incompleto",
    "Fundamental II completo", "Médio incompleto", "Médio completo", "Superior incompleto",
    "Superior completo", "Pós-graduação",
]
CIVIS = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
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


def gerar_nome(rng: random.Random, usados: set) -> str:
    """Nome composto que ainda não foi usado em nenhum outro registro."""
    while True:
        nome = f"{rng.choice(PRIMEIROS)} {rng.choice(SOBRENOMES)} {rng.choice(SOBRENOMES)}"
        if nome not in usados:
            usados.add(nome)
            return nome


def gerar_data_nascimento(rng: random.Random, idade_min: int, idade_max: int) -> str:
    hoje = datetime(2026, 10, 1)
    dias = rng.randint(idade_min * 365, idade_max * 365)
    return (hoje - timedelta(days=dias)).strftime("%d/%m/%Y")


def gerar_cadastro(rng: random.Random, indice: int, usados: set) -> StudentCreate:
    aluno = gerar_nome(rng, usados)
    responsavel = gerar_nome(rng, usados)
    qtd_irmaos = rng.choices([0, 1, 2], weights=[60, 30, 10])[0]
    irmaos = [{"nome": gerar_nome(rng, usados), "serie": rng.choice(SERIES)} for _ in range(qtd_irmaos)]
    tem_laudo = rng.random() < 0.15
    cep = f"{rng.randint(10000, 99999)}-{rng.randint(100, 999)}"
    return StudentCreate(
        category=CATEGORIAS[indice % len(CATEGORIAS)] if rng.random() < 0.5 else rng.choice(CATEGORIAS),
        studentName=aluno,
        studentBirth=gerar_data_nascimento(rng, 3, 17),
        studentRg=f"{rng.randint(10000000, 99999999)}",
        studentCpf=gerar_cpf(rng),
        studentNat=rng.choice(CIDADES),
        studentGrade=rng.choice(SERIES),
        studentShift=rng.choice(TURNOS),
        studentLaudo="Sim" if tem_laudo else "Não",
        laudoDesc=rng.choice(DESCRICOES_LAUDO) if tem_laudo else None,
        irmaoQty=qtd_irmaos,
        irmaos=irmaos,
        respName=responsavel,
        respBirth=gerar_data_nascimento(rng, 22, 65),
        respRg=f"{rng.randint(10000000, 99999999)}",
        respCpf=gerar_cpf(rng),
        respNat=rng.choice(CIDADES),
        respAddress=rng.choice(RUAS),
        respNum=str(rng.randint(1, 999)),
        respBairro=rng.choice(BAIRROS),
        respCep=cep,
        respCivil=rng.choice(CIVIS),
        respEduc=rng.choice(ESCOLARIDADES),
        respEmail=f"resp{indice}@exemplo.com" if rng.random() < 0.7 else None,
        telPai=gerar_telefone(rng) if rng.random() < 0.8 else None,
        emailPai=f"pai{indice}@exemplo.com" if rng.random() < 0.5 else None,
        telMae=gerar_telefone(rng) if rng.random() < 0.8 else None,
        emailMae=f"mae{indice}@exemplo.com" if rng.random() < 0.5 else None,
        respFin=rng.choice(RESPONSAVEIS),
        respAcad=rng.choice(RESPONSAVEIS),
    )


# Período em que os cadastros "foram feitos" (espalhados, para a fila ter ordem real)
PERIODO_INICIO = datetime(2026, 8, 1, 7, 0)
PERIODO_DIAS = 60


def gerar_data_cadastro(rng: random.Random) -> datetime:
    """Data e hora de cadastro espalhadas em ~60 dias, em horário comercial."""
    dia = rng.randint(0, PERIODO_DIAS)
    hora = rng.randint(7, 17)
    minuto = rng.randint(0, 59)
    segundo = rng.randint(0, 59)
    return PERIODO_INICIO + timedelta(days=dia, hours=hora - 7, minutes=minuto, seconds=segundo)


def main():
    parser = argparse.ArgumentParser(description="Gera cadastros fictícios para teste.")
    parser.add_argument("--quantidade", type=int, default=300, help="quantidade total desejada (padrão: 300)")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    rng = random.Random(SEED)
    db = SessionLocal()
    try:
        cpfs_existentes = {c for (c,) in db.query(Student.student_cpf).all() if c}
        # Nomes gerados nesta execução: começa vazio para a sequência ser sempre a mesma.
        usados: set = set()
        criados = 0
        pulados = 0
        for i in range(args.quantidade):
            cadastro = gerar_cadastro(rng, i, usados)
            # Sorteia a data SEMPRE, mesmo quando o cadastro será pulado,
            # para a sequência aleatória ser idêntica em todas as execuções.
            data_cadastro = gerar_data_cadastro(rng)
            if cadastro.studentCpf in cpfs_existentes:
                pulados += 1
                continue
            aluno = create_student(db, cadastro, USUARIO_SEED)
            aluno.registration_date = data_cadastro
            log = db.query(HistoryLog).order_by(HistoryLog.id.desc()).first()
            if log:
                log.created_at = data_cadastro
            db.commit()
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
