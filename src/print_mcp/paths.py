"""Where Bambu Studio is installed and which folders the print tools may touch."""
from __future__ import annotations

import os
from pathlib import Path

DEFAULT_STUDIO_DIR = Path(r"C:\Program Files\Bambu Studio")
STUDIO_DIR_ENV = "BAMBU_STUDIO_DIR"
WORK_DIR_ENV = "PRINT_MCP_WORK_DIR"

# src/print_mcp/paths.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[2]


class PathNotAllowed(ValueError):
    """A model or output path resolves outside the allowed folders."""


def studio_dir() -> Path:
    """Bambu Studio's install folder, from BAMBU_STUDIO_DIR or the default location."""
    value = os.environ.get(STUDIO_DIR_ENV)
    return Path(value) if value else DEFAULT_STUDIO_DIR


def studio_exe() -> Path:
    return studio_dir() / "bambu-studio.exe"


def profiles_dir() -> Path:
    """The bundled Bambu Lab system profiles: machine, process and filament folders."""
    return studio_dir() / "resources" / "profiles" / "BBL"


def allowed_roots() -> list[Path]:
    """The repository, Documents/BlenderMCP and, when set, PRINT_MCP_WORK_DIR."""
    roots = [REPO_ROOT, Path.home() / "Documents" / "BlenderMCP"]
    work_dir = os.environ.get(WORK_DIR_ENV)
    if work_dir:
        roots.append(Path(work_dir))
    return [root.resolve() for root in roots]


def resolve_allowed(path: str | Path) -> Path:
    """Resolve `path` (following `..` and links) and require it to sit inside an allowed root."""
    resolved = Path(path).resolve()
    roots = allowed_roots()
    if any(resolved.is_relative_to(root) for root in roots):
        return resolved
    listed = ", ".join(str(root) for root in roots)
    raise PathNotAllowed(f"{resolved} is outside the allowed folders ({listed})")
