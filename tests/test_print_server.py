"""print_mcp.server: the FastMCP wrapper exposes exactly the three print tools."""
from __future__ import annotations

import asyncio
import json

from print_mcp import server


def _tools():
    return asyncio.run(server.mcp.list_tools())


def test_exactly_three_tools():
    names = sorted(tool.name for tool in _tools())
    assert names == ["inspect_sliced", "list_print_profiles", "slice_model"]


def test_every_tool_has_a_description():
    for tool in _tools():
        assert tool.description and tool.description.strip(), tool.name


def test_errors_come_back_as_text(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(tmp_path))
    reply = asyncio.run(server.inspect_sliced(str(tmp_path / "missing.gcode.3mf")))
    assert reply.startswith("Error: ")


def test_replies_are_json(tmp_path, monkeypatch):
    monkeypatch.setenv("BAMBU_STUDIO_DIR", str(tmp_path / "studio"))
    root = tmp_path / "studio" / "resources" / "profiles" / "BBL"
    for kind in ("machine", "process", "filament"):
        (root / kind).mkdir(parents=True)
    reply = asyncio.run(server.list_print_profiles())
    assert json.loads(reply) == {"machines": [], "processes": [], "filaments": []}
