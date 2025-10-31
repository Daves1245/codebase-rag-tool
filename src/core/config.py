from typing import Optional

class settings:

    # LLM (query rewriter)
    LLM_PROVIDER = 'anthropic'
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "claude-3-5-sonnet-20240620"
    LLM_MAX_TOKENS: int = 4096

    # Chunker
    CHUNK_SIZE: int = 50
    CHUNK_OVERLAP: int = 20

    # Embeddings
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    OPENAI_API_KEY: Optional[str] = None

    # Indexing
    BATCH_SIZE = 20

    # Discord bot
    DISCORD_TOKEN: str = ""
    DISCORD_COMMAND_PREFIX: str = "/"

    # Git Manager
    GIT_DIR = "./data"
    GIT_CACHE_DIR = "./data/repos"

    # Git
    MAX_REPO_SIZE_MB = 500
