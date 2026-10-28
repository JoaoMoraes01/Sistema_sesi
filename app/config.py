import os
import secrets
import warnings
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


class Settings:
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "sesi_gestao")
    MYSQL_SSL: bool = os.getenv("MYSQL_SSL", "false").lower() in {"1", "true", "yes"}
    # Pode ser um caminho para um certificado CA ou o próprio certificado PEM.
    MYSQL_SSL_CA: str = os.getenv("MYSQL_SSL_CA", "").strip()
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        # Aceita também uma URL mysql:// fornecida por um provedor cloud.
        external_url = os.getenv("DATABASE_URL", "").strip()
        if external_url:
            if external_url.startswith("mysql://"):
                return external_url.replace("mysql://", "mysql+pymysql://", 1)
            return external_url

        # URL.create faz o escape correto para senhas que contenham @, / ou :.
        url = URL.create(
            "mysql+pymysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST,
            port=int(self.MYSQL_PORT),
            database=self.MYSQL_DB,
        )
        return url.render_as_string(hide_password=False)


settings = Settings()

if not os.getenv("DATABASE_URL") and not os.getenv("MYSQL_PASSWORD"):
    warnings.warn(
        "Configure DATABASE_URL ou MYSQL_PASSWORD no ambiente; a conexão com "
        "o banco provavelmente vai falhar.",
        stacklevel=2,
    )
