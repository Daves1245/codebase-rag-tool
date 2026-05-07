import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class settings:

    # LLM (query rewriter)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    LLM_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20240620")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # Chunker
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "50"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "20"))

    # Embeddings
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Indexing
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "20"))

    # Discord bot
    DISCORD_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_COMMAND_PREFIX: str = os.getenv("DISCORD_COMMAND_PREFIX", "/")

    # Git Manager
    GIT_DIR: str = os.getenv("GIT_DIR", "./data")
    GIT_CACHE_DIR: str = os.getenv("GIT_CACHE_DIR", "./data/repos")

    # Git
    MAX_REPO_SIZE_MB: int = int(os.getenv("MAX_REPO_SIZE_MB", "500"))
