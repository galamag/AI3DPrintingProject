"""print_mcp.paths: where Bambu Studio lives and which paths the print tools may touch."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import REPO_ROOT
from print_mcp import paths
from print_mcp.paths import PathNotAllowed, resolve_allowed


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(tmp_path))
    return tmp_path


def _make_dir_link(link: Path, target: Path) -> None:
    """Create a directory symlink, or a junction where symlinks need a privilege."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    try:
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    except (ImportError, AttributeError, OSError):
        pytest.skip("cannot create a directory link on this machine")


def test_path_not_allowed_is_value_error():
    assert issubclass(PathNotAllowed, ValueError)


def test_accepts_path_inside_work_dir(work_dir):
    target = work_dir / "part.stl"
    assert resolve_allowed(target) == target.resolve()


def test_accepts_cyrillic_and_spaces(work_dir):
    target = work_dir / "папка с пробелом" / "деталь.stl"
    resolved = resolve_allowed(str(target))
    assert resolved == target.resolve()
    assert resolved.name == "деталь.stl"
    assert resolved.parent.name == "папка с пробелом"


def test_rejects_dotdot_escape(work_dir):
    with pytest.raises(PathNotAllowed):
        resolve_allowed(work_dir / ".." / "x.stl")


def test_rejects_path_outside_roots(work_dir, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "x.stl"
    with pytest.raises(PathNotAllowed):
        resolve_allowed(outside)


def test_rejects_link_pointing_outside(work_dir, tmp_path_factory):
    outside = tmp_path_factory.mktemp("link_target")
    link = work_dir / "link"
    _make_dir_link(link, outside)
    with pytest.raises(PathNotAllowed):
        resolve_allowed(link / "x.stl")


def test_studio_dir_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("BAMBU_STUDIO_DIR", str(tmp_path))
    assert paths.studio_dir() == tmp_path
    assert paths.studio_exe() == tmp_path / "bambu-studio.exe"
    assert paths.profiles_dir() == tmp_path / "resources" / "profiles" / "BBL"


def test_studio_dir_default(monkeypatch):
    monkeypatch.delenv("BAMBU_STUDIO_DIR", raising=False)
    assert paths.studio_dir() == Path(r"C:\Program Files\Bambu Studio")


def test_default_roots_without_work_dir(monkeypatch):
    monkeypatch.delenv("PRINT_MCP_WORK_DIR", raising=False)
    roots = paths.allowed_roots()
    assert roots == [REPO_ROOT.resolve(), (Path.home() / "Documents" / "BlenderMCP").resolve()]


def test_work_dir_is_added_to_roots(work_dir):
    assert work_dir.resolve() in paths.allowed_roots()
