"""print_mcp.server: the FastMCP wrapper exposes exactly the three print tools."""
from __future__ import annotations

import asyncio
import json

from print_mcp import server


def _tools():
    return asyncio.run(server.mcp.list_tools())


def test_exactly_seven_tools():
    names = sorted(tool.name for tool in _tools())
    assert names == [
        "inspect_sliced",
        "list_print_profiles",
        "slice_model",
        "studio_capture",
        "studio_click",
        "studio_open",
        "studio_windows",
    ]


def test_click_description_demands_a_capture_and_consent():
    click = next(tool for tool in _tools() if tool.name == "studio_click")
    text = click.description.lower()
    assert "studio_capture" in text
    assert "consent" in text
    for button in ("close", "minimize", "maximize"):
        assert button in text
    assert {"expected_width", "expected_height"} <= set(click.inputSchema["properties"])


def test_open_description_says_matching_is_by_file_name():
    open_tool = next(tool for tool in _tools() if tool.name == "studio_open")
    assert "file name only" in open_tool.description.lower()


class _NoWindows:
    def windows(self):
        return []


def test_studio_errors_come_back_as_text(monkeypatch):
    from print_mcp import studio

    monkeypatch.setattr(studio, "Win32Backend", _NoWindows)
    for reply in (
        asyncio.run(server.studio_windows()),
        asyncio.run(server.studio_click(x=1, y=1)),
        asyncio.run(server.studio_capture()),
    ):
        text = reply if isinstance(reply, str) else reply[0]
        assert "Bambu Studio is not running" in text or text == "[]", text


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
