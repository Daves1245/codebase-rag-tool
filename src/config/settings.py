"""
settings.py - interface for configurable values through toml files
"""
from typing import Literal
import tomllib
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Config(BaseModel):
    """
    Load configuration variables from a settings.toml file.
    Construct via `Config.load(path)` so values are validated on construction.
    """
    model_config = ConfigDict(frozen=True, extra='forbid')

    # llm logistics
    llm_provider: Literal['anthropic']
    llm_model: str = Field(min_length=1)

    # parameters
    batch_size: int = Field(gt=0)
    embedding_dimensions: int = Field(gt=0)

    # embeddings
    embedding_provider: Literal['sentence-transformers', 'zembed', 'mock']
    embedding_model: str = Field(min_length=1)

    # git-related
    git_max_repo_size_mb: int = Field(gt=0)
    git_cache_dir: str = Field(min_length=1)

    # rewrite strategy
    strategy: Literal['hyde', 'rewrite', 'composite', 'passthrough']

    @classmethod
    def load(cls, path: str = "settings.toml") -> "Config":
        """Parse a settings.toml file and return a validated Config instance."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls(
            llm_provider=data['logistics']['llm_provider'],
            llm_model=data['logistics']['llm_model'],
            batch_size=data['parameters']['batch_size'],
            embedding_dimensions=data['parameters']['embedding_dimensions'],
            embedding_provider=data['embeddings']['provider'],
            embedding_model=data['embeddings']['model'],
            git_max_repo_size_mb=data['git']['max_repo_size_mb'],
            git_cache_dir=data['git']['cache_dir'],
            strategy=data['rewrite']['strategy'],
        )


class Credentials(BaseModel):
    """
    Load secrets from a credentials.toml file.
    Construct via `Credentials.load(path)`.
    """
    model_config = ConfigDict(frozen=True, extra='forbid')

    api_key: SecretStr = Field(min_length=1)

    @classmethod
    def load(cls, path: str = "credentials.toml") -> "Credentials":
        """Parse a credentials.toml file and return a validated Credentials instance."""
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(api_key=data['api_key'])
