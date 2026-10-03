import os
import secrets
import warnings
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "sesi_gestao")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas (um turno de trabalho)
    # Senha inicial do usuario 'admin' (usada apenas na PRIMEIRA criacao do banco,
    # quando ainda nao existe nenhum admin). Fica no .env, nunca no codigo-fonte.
    # Se estiver vazia, crud.py gera uma senha aleatoria e mostra no console.
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

settings = Settings()

if not os.getenv("MYSQL_PASSWORD"):
    warnings.warn(
        "MYSQL_PASSWORD não foi definido no .env — a conexão com o banco "
        "provavelmente vai falhar. Confira o arquivo .env na raiz do projeto.",
        stacklevel=2,
    )
