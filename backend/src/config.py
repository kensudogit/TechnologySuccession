"""アプリケーション設定。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "TechnologySuccession RAG"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/technology_succession"
    )
    allowed_origins: str = "http://localhost:3000"

    # Railway: OPENAI_API_KEY
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"
    prompt_version: str = "v1"

    # Railway: JWT_SECRET
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    auth_username: str = "admin"
    auth_password: str = "admin"

    upload_dir: str = str(Path(__file__).parent.parent / "uploads")
    data_dir: str = str(Path(__file__).parent.parent.parent / "data")
    config_dir: str = str(Path(__file__).parent.parent / "config")

    embedding_dimensions: int = 1536
    retrieval_top_k: int = 10
    rrf_top_k: int = 5

    @property
    def database_url_normalized(self) -> str:
        """Railway 等の postgres:// を asyncpg 用に正規化。"""
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+asyncpg://" + url[len(prefix):]
        return url

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def prompts_dir(self) -> Path:
        return Path(self.config_dir) / "prompts"

    @property
    def auth_enabled(self) -> bool:
        return bool(self.jwt_secret)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
