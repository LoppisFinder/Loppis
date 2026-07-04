from pydantic_settings import BaseSettings

from app.db_url import normalize_async_database_url


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://loppis:loppis@localhost:5432/loppisfinder"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_expire_hours: int = 8760  # 1 year for anonymous sessions
    cors_origins: str = "http://localhost:3000,http://localhost:8081"
    pii_salt: str = "change-me-in-production"
    crawl_auto_interval_hours: float = 6.0
    admin_password: str = ""

    @property
    def admin_enabled(self) -> bool:
        return bool(self.admin_password.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        url, _ = normalize_async_database_url(self.database_url)
        return url

    @property
    def async_connect_args(self) -> dict:
        _, connect_args = normalize_async_database_url(self.database_url)
        return connect_args

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
