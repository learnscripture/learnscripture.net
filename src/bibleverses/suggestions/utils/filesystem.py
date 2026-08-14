import os
from pathlib import Path


def ensure_dir(path: Path):
    """
    Ensure that a directory exists
    """
    if not path.exists():
        os.makedirs(str(path))
