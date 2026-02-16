"""File discovery and backup utilities."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def get_dwg_files(folder: Path, recursive: bool = True) -> list[Path]:
    """Return all .dwg files under *folder*, sorted by name."""
    pattern = "**/*.dwg" if recursive else "*.dwg"
    return sorted(folder.glob(pattern))


def create_backup(file_path: Path) -> Path:
    """Create a timestamped backup copy in a ``.backups`` sibling directory.

    Returns the path to the backup file.
    """
    backup_dir = file_path.parent / ".backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(file_path, backup_path)
    return backup_path
