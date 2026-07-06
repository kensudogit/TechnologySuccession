"""アプリケーション設定。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TechnologySuccession RAG"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/technology_succession"
    )
    allowed_origins: str = "http://localhost:3000"

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"
    prompt_version: str = "v1"

    upload_dir: str = str(Path(__file__).parent.parent / "uploads")
    data_dir: str = str(Path(__file__).parent.parent.parent / "data")
    config_dir: str = str(Path(__file__).parent.parent / "config")

    embedding_dimensions: int = 1536
    retrieval_top_k: int = 10
    rrf_top_k: int = 5

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def prompts_dir(self) -> Path:
        return Path(self.config_dir) / "prompts"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
