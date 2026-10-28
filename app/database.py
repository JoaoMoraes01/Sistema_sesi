import ssl
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {}
if settings.MYSQL_SSL:
    tls_context = ssl.create_default_context()
    if settings.MYSQL_SSL_CA:
        ca_path = Path(settings.MYSQL_SSL_CA)
        if ca_path.is_file():
            tls_context.load_verify_locations(cafile=str(ca_path))
        else:
            # Também aceita o conteúdo PEM do certificado em variável de ambiente.
            tls_context.load_verify_locations(cadata=settings.MYSQL_SSL_CA)
    connect_args["ssl"] = tls_context

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
