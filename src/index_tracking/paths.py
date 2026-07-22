"""Locate the project root so notebooks work regardless of the launch directory."""

from __future__ import annotations

import os


def custom_chdir_to_project_root(marker: str = "pyproject.toml", max_up: int = 8) -> str:
    """Walk up from the current directory to the folder containing ``marker`` and chdir there.

    Notebooks launched from ``notebooks/`` (or executed by nbconvert, which uses the
    notebook's own directory as cwd) then resolve relative paths like ``data/`` from the
    repo root. Idempotent - safe to call at the top of every notebook.
    """
    d = os.path.abspath(os.getcwd())
    for _ in range(max_up):
        if os.path.exists(os.path.join(d, marker)):
            os.chdir(d)
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.getcwd()
