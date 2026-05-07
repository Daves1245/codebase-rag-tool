"""
settings.py - interface for configurable values through toml files
"""
from typing import Dict, Any
import tomllib
from pydantic import BaseModel, SecretStr

class Config(BaseModel):
    """
    Load configuration variables from a settings.toml file
    """
    # llm logistics
    llm_provider: str
    llm_model: str

    # parameteres
    batch_size: int
    embedding_dimensions: int

    # git-related
    git_max_repo_size_mb: int
    git_cache_dir: str


    def load(self, path: str = "settings.toml"):
        """
        Args:
            path: Path to settings.toml file. See settings.toml.example for expected values
        """
        _data: Dict[str, Any]
        with open(path, "rb") as f:
            _data = tomllib.load(f)

        self.llm_provider = _data['logistics']['llm_provider']
        self.llm_model = _data['logistics']['llm_model']

        self.batch_size = _data['parameters']['batch_size']
        self.embedding_dimensions = _data['parameters']['embedding_dimensions']

        self.git_max_repo_size_mb = _data['git']['max_repo_size_mb']
        self.git_cache_dir = _data['git']['cache_dir']

class Credentials(BaseModel):
    """
    Load secrets from a credentials.toml file
    """
    api_key: SecretStr

    def load(self, path: str = "credentials.toml"):
        """
        Args:
            path: Path to a credentials.toml file. See credentials.toml.example for expected values
        """
        _data: Dict[str, Any]

        with open(path, "rb") as f:
            _data = tomllib.load(f)
        self.api_key = _data['api_key']
