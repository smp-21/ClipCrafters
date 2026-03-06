"""
Application configuration — reads all tunables from environment variables.
Uses pydantic-settings for typed, validated config with .env file support.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root is two levels above this file (app/core/config.py → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central configuration for the RAG Video Script Generator."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Groq LLM ──────────────────────────────────────────
    groq_api_key: str = ""
    groq_model_name: str = "llama-3.3-70b-versatile"

    # ── Stability.ai ──────────────────────────────────────
    stability_api_key: str = ""

    # ── Gemini Image API ──────────────────────────────────
    gemini_api_key: str = ""

    # ── Embedding Model ───────────────────────────────────
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # ── Chunking ──────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64

    # ── Retrieval ─────────────────────────────────────────
    top_k: int = 10
    mmr_diversity_lambda: float = 0.5

    # ── Upload Limits ─────────────────────────────────────
    max_upload_size_mb: int = 50

    # ── Storage Paths (resolved relative to project root) ─
    upload_dir: str = "app/storage/uploads"
    index_dir: str = "app/storage/indices"
    parsed_dir: str = "app/storage/parsed"
    scripts_dir: str = "app/storage/scripts"
    projects_dir: str = "app/storage/projects"

    # ── Server ────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # ── Derived helpers ───────────────────────────────────
    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    def resolve_path(self, relative: str) -> Path:
        """Resolve a storage path relative to the project root and ensure it exists."""
        p = _PROJECT_ROOT / relative
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


# Singleton — import this everywhere
settings = Settings()
