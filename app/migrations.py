"""
Migrações leves de schema executadas no startup da aplicação.

`Base.metadata.create_all` NÃO altera tabelas que já existem — só cria as que
faltam. Então, quando adicionamos colunas novas em `models.py` (como
`category_priority` e `student_cpf_digits`), instalações que já têm o banco
precisam de um `ALTER TABLE`. Este módulo faz isso de forma idempotente:

- Verifica em `information_schema` se a coluna/índice já existe antes de criar.
- Backfill dos valores para registros antigos.
- É seguro rodar em toda inicialização: se já está tudo lá, não faz nada.

Só faz sentido para MySQL. Se um dia o projeto migrar de banco (ex: Postgres),
troque `information_schema.columns` por `information_schema.columns` com
`table_schema = current_schema()` — a sintaxe é bem parecida.
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Mantenha em sincronia com CATEGORY_PRIORITY em app/crud.py.
# Em SQL usamos os VALORES string do Enum, não os nomes Python.
_CATEGORY_PRIORITY_SQL_CASE = """
    CASE category
        WHEN 'Industriário'          THEN 1
        WHEN 'Colaborador'           THEN 2
        WHEN 'Empresário Industrial' THEN 3
        WHEN 'Convênio'              THEN 4
        WHEN 'Comunidade'            THEN 5
        ELSE 99
    END
"""

def _has_column(conn, table: str, column: str) -> bool:
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return (r.scalar() or 0) > 0

def _has_index(conn, table: str, index_name: str) -> bool:
    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :i"
    ), {"t": table, "i": index_name})
    return (r.scalar() or 0) > 0

def _add_column_if_missing(conn, table: str, column: str, ddl: str) -> None:
    if not _has_column(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))

def _create_index_if_missing(conn, table: str, index_name: str, columns: str) -> None:
    if not _has_index(conn, table, index_name):
        conn.execute(text(f"CREATE INDEX {index_name} ON {table} ({columns})"))

def run_migrations(engine: Engine) -> None:
    """Executa todas as migrações. Seguro para rodar em toda inicialização."""
    with engine.begin() as conn:
        # 1) category_priority — permite ORDER BY indexado na fila
        _add_column_if_missing(conn, "alunos", "category_priority", "category_priority INT NULL")
        _create_index_if_missing(
            conn, "alunos", "ix_alunos_category_priority", "category_priority"
        )
        _create_index_if_missing(
            conn, "alunos", "idx_queue_order",
            "category_priority, possui_irmao, registration_date",
        )
        # Backfill apenas se houver linhas pendentes (evita UPDATE em toda subida)
        pendentes = conn.execute(text(
            "SELECT COUNT(*) FROM alunos WHERE category_priority IS NULL"
        )).scalar() or 0
        if pendentes:
            conn.execute(text(
                f"UPDATE alunos SET category_priority = {_CATEGORY_PRIORITY_SQL_CASE} "
                "WHERE category_priority IS NULL"
            ))

        # 2) student_cpf_digits — busca de CPF por índice em vez de varrer tabela
        _add_column_if_missing(
            conn, "alunos", "student_cpf_digits", "student_cpf_digits VARCHAR(11) NULL"
        )
        _create_index_if_missing(
            conn, "alunos", "ix_alunos_student_cpf_digits", "student_cpf_digits"
        )
        pendentes = conn.execute(text(
            "SELECT COUNT(*) FROM alunos "
            "WHERE student_cpf IS NOT NULL AND student_cpf_digits IS NULL"
        )).scalar() or 0
        if pendentes:
            conn.execute(text(
                "UPDATE alunos "
                "SET student_cpf_digits = REPLACE(REPLACE(REPLACE(student_cpf, '.', ''), '-', ''), ' ', '') "
                "WHERE student_cpf IS NOT NULL AND student_cpf_digits IS NULL"
            ))
