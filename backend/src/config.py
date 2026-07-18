"""アプリケーション設定。"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_secret(value: object, default: str) -> str:
    """Railway 変数の前後空白・引用符・空文字を除去してデフォルトに戻す。"""
    if value is None:
        return default
    text = str(value).strip().strip('"').strip("'").strip()
    return text or default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "技術継承プラットフォーム"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/technology_succession",
        validation_alias="DATABASE_URL",
    )
    allowed_origins: str = Field(default="http://localhost:3000", validation_alias="ALLOWED_ORIGINS")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL"
    )
    openai_chat_model: str = Field(default="gpt-4o", validation_alias="OPENAI_CHAT_MODEL")
    prompt_version: str = Field(default="v1", validation_alias="PROMPT_VERSION")

    jwt_secret: str = Field(default="", validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = Field(default=24, validation_alias="JWT_EXPIRE_HOURS")
    auth_username: str = Field(default="admin", validation_alias="AUTH_USERNAME")
    auth_password: str = Field(default="admin", validation_alias="AUTH_PASSWORD")

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def normalize_jwt_secret(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().strip('"').strip("'").strip()

    @field_validator("auth_username", mode="before")
    @classmethod
    def normalize_auth_username(cls, value: object) -> str:
        return _normalize_secret(value, "admin")

    @field_validator("auth_password", mode="before")
    @classmethod
    def normalize_auth_password(cls, value: object) -> str:
        return _normalize_secret(value, "admin")

    upload_dir: str = Field(
        default=str(Path(__file__).parent.parent / "uploads"), validation_alias="UPLOAD_DIR"
    )
    data_dir: str = Field(
        default=str(Path(__file__).parent.parent.parent / "data"),
        validation_alias="DATA_DIR",
    )
    config_dir: str = str(Path(__file__).parent.parent / "config")

    embedding_dimensions: int = 1536
    retrieval_top_k: int = Field(default=12, validation_alias="RETRIEVAL_TOP_K")
    rrf_top_k: int = Field(default=8, validation_alias="RRF_TOP_K")
    rerank_top_k: int = Field(default=5, validation_alias="RERANK_TOP_K")
    chunk_max_chars: int = Field(default=600, validation_alias="CHUNK_MAX_CHARS")
    chunk_overlap: int = Field(default=80, validation_alias="CHUNK_OVERLAP")

    @property
    def database_url_normalized(self) -> str:
        """Railway 等の postgres:// を asyncpg 用に正規化（SSL クエリ除去）。"""
        url = self.database_url
        for prefix in (
            "postgres://",
            "postgresql://",
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
        ):
            if url.startswith(prefix):
                url = "postgresql+asyncpg://" + url[len(prefix):]
                break

        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query.pop("ssl", None)
        query.pop("sslmode", None)
        clean_query = urlencode({k: v[0] for k, v in query.items()})
        return urlunparse(parsed._replace(query=clean_query))

    @property
    def database_connect_args(self) -> dict:
        """Railway 外部 DB 接続用 SSL・タイムアウト設定。"""
        url = self.database_url
        is_internal = (
            ".railway.internal" in url
            or "localhost" in url
            or "127.0.0.1" in url
        )
        args: dict = {"timeout": 10}
        if not is_internal:
            args["ssl"] = "require"
        return args

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
