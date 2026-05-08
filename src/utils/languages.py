"""
languages.py - canonical mapping from file extensions to tree-sitter language names.
"""
from pathlib import Path
from typing import Optional


LANGUAGE_BY_EXTENSION: dict[str, str] = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.java': 'java',
    '.c': 'c',
    '.h': 'cpp',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.hpp': 'cpp',
    '.go': 'go',
    '.rs': 'rust',
}


def detect_language(path: Path) -> Optional[str]:
    """Return the tree-sitter language name for `path`, or None if the extension is unsupported."""
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower())


def require_language(path: Path) -> str:
    """Like detect_language, but raise ValueError when the extension is unsupported."""
    language = detect_language(path)
    if language is None:
        raise ValueError(f"Could not determine language of {path}")
    return language
