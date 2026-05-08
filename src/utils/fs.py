"""
fs.py - filesystem helpers.
"""
import os
from pathlib import Path


def directory_size(path: Path) -> int:
    """Total size in bytes of all regular files under `path`. Does not follow symlinks."""
    total = 0
    for dirpath, _, filenames in os.walk(path, followlinks=False):
        for name in filenames:
            try:
                total += os.stat(os.path.join(dirpath, name), follow_symlinks=False).st_size
            except OSError:
                # unreadable / removed mid-walk — skip
                continue
    return total
