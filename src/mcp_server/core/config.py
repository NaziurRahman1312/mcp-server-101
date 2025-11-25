"""
Application-wide configuration helpers.
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="smart-mcp")
    environment: str = Field(default="local")
    database_url: str = Field(default="sqlite:///data/mcp.db")
    faiss_index_path: str = Field(default="data/faiss.index")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384)
    faiss_top_k: int = Field(default=5)
    data_dir: Path = Field(default=Path("data"))

    class Config:
        env_prefix = "MCP_"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings


