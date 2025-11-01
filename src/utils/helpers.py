from typing import Optional
import hashlib
import re
from urllib.parse import urlparse

def generate_repo_id(github_url: str) -> str:
    """generate a unique repo id from github url"""
    parsed = parse_github_url(github_url)
    if not parsed:
        # use md5 for now ig?
        return hashlib.md5(github_url.encode()).hexdigest()[:16]

    owner, repo = parsed
    return f"{owner}_{repo}"

def parse_github_url(github_url: str) -> Optional[tuple[str, str]]:
    """parse github url to extract owner and repo name"""
    url = github_url.strip().rstrip('/')

    patterns = [
        r'https?://github\.com/([^/]+)/([^/]+)/?',
        r'git@github\.com:([^/]+)/([^/]+)\.git',
        r'https?://www\.github\.com/([^/]+)/([^/]+)/?'
    ]

    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            if repo.endswith('.git'):
                repo = repo[:-4]
            return owner, repo

    return None
