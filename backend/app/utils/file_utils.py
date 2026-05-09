"""File utility helpers."""

from __future__ import annotations

import os
from pathlib import Path


def get_file_extension(filename: str) -> str:
	"""Return lowercased file extension without the dot."""
	return Path(filename).suffix.replace(".", "").lower()


def ensure_directory(path: str) -> None:
	"""Ensure a directory exists."""
	Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
	"""Normalize a filename for storage."""
	return os.path.basename(filename).replace("..", "").replace("/", "_").replace("\\", "_")
