from pathlib import Path
from typing import Optional
import shutil

import git
from loguru import logger

from src.core.config import settings
from src.utils.fs import directory_size
from src.utils.helpers import generate_repo_id, parse_github_url


class GitHandler:
    def __init__(self) -> None:
        self.cache_dir = Path(settings.GIT_CACHE_DIR)
        self.cache_dir.mkdir(parents = True, exist_ok = True)

    async def clone_repo(
        self,
        github_url,
    ) -> tuple[str, Path]:
        repo_id = generate_repo_id(github_url)
        repo_path = self.cache_dir / repo_id

        if repo_path.exists():
            logger.info(f"Repo {repo_id} already cloned at {repo_path}")
            return repo_id, repo_path
        parsed = parse_github_url(github_url)
        if not parsed:
            raise ValueError(f"Invalid github URL: {github_url}")
        logger.info(f"Cloning repository {github_url} to {repo_path}")

        try:
            git.Repo.clone(
                github_url,
                depth = 1,
                single_branch = True,
                path= repo_path,
            )
            repo_size_mb = directory_size(repo_path) / (1024 * 1024)
            if repo_size_mb > settings.MAX_REPO_SIZE_MB:
                shutil.rmtree(repo_path)
                raise ValueError(
                    f"github repo too large: {repo_size_mb:.1f}MB > "
                    f"{settings.MAX_REPO_SIZE_MB}MB limit"
                )
            logger.info(f"Successfully cloned repo {repo_id} at {repo_path}")
            return repo_id, repo_path
        except Exception as e:
            logger.error(f"Encountered error: {e}")
            raise

    def delete_repo(self, repo_id: str) -> bool:
        repo_path = self.cache_dir / repo_id
        if not repo_path.exists():
            logger.warning(f"repo {repo_id} not found at {repo_path}")
            return False
        shutil.rmtree(repo_path)
        logger.info(f"deleted repo {repo_id}")
        return True

    def get_repo_path(self, repo_id: str) -> Optional[Path]:
        repo_path = self.cache_dir / repo_id
        return repo_path if repo_path.exists() else None
