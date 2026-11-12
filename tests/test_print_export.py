"""blender_mcp.print_export: the export_for_print tool, tested without Blender."""
from __future__ import annotations

import asyncio
import json
import math
import struct

import pytest
from mcp.server.fastmcp import FastMCP

from blender_mcp import blender_scripts, print_export, server
from blender_mcp.print_export import EXPORT_FOR_PRINT, STL_WRITER, register
from test_print_live import _CORNERS, _FACES

REPORT = {
    "filepath": "placeholder",
    "triangles": 12,
    "size_mm": [20.0, 20.0, 20.0],
    "min_mm": [0.0, 0.0, 0.0],
    "max_mm": [20.0, 20.0, 20.0],
    "volume_cm3": 8.0,
    "objects": [{
        "name": "Cube", "triangles": 12, "size_mm": [20.0, 20.0, 20.0], "boundary_edges": 0,
        "non_manifold_edges": 0, "inconsistent_edges": 0, "volume_cm3": 8.0,
    }],
    "watertight": True,
    "warnings": ["2 objects go into one STL", "size below 1 mm on z"],
}


class FakeRunner:
    def __init__(self, result=None, error=None):
        self.result = REPORT if result is None else result
        self.error = error
        self.calls = []

    def __call__(self, script, args):
        self.calls.append((script, args))
        if self.error is not None:
            raise self.error
        return {**self.result, "filepath": args["filepath"]} if "error" not in self.result else self.result


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(tmp_path))
    return tmp_path


def _tool(runner):
    return register(FastMCP("test"), runner)


def _export(runner, **kwargs):
    return asyncio.run(_tool(runner)(**kwargs))


# --- the tool -------------------------------------------------------------------


def test_path_outside_the_allowed_folders(work_dir, tmp_path_factory):
    runner = FakeRunner()
    outside = tmp_path_factory.mktemp("outside") / "part.stl"
    reply = _export(runner, filepath=str(outside))
    assert reply.startswith("Error: ")
    assert runner.calls == []


@pytest.mark.parametrize("name", ["part.obj", "part.3mf", "part.stl.txt", "part"])
def test_only_stl(work_dir, name):
    runner = FakeRunner()
    reply = _export(runner, filepath=str(work_dir / name))
    assert reply.startswith("Error: ") and ".stl" in reply
    assert runner.calls == []


@pytest.mark.parametrize("volume", [0, -5])
def test_build_volume_must_be_positive(work_dir, volume):
    runner = FakeRunner()
    assert _export(runner, filepath=str(work_dir / "p.stl"), build_volume_mm=volume).startswith("Error: ")
    assert runner.calls == []


def test_script_gets_the_absolute_path_and_the_names(work_dir):
    runner = FakeRunner()
    target = work_dir / "папка с пробелом" / "деталь 1.STL"
    _export(runner, filepath=str(target), names=["Cube", "Ручка с пробелом"], build_volume_mm=180)
    ((script, args),) = runner.calls
    assert script is EXPORT_FOR_PRINT
    assert args == {
        "filepath": str(target.resolve()),
        "names": ["Cube", "Ручка с пробелом"],
        "build_volume_mm": 180.0,
    }


def test_no_names_means_the_selection(work_dir):
    runner = FakeRunner()
    _export(runner, filepath=str(work_dir / "p.stl"))
    assert runner.calls[0][1]["names"] == []


def test_reply_carries_sizes_triangles_watertight_and_every_warning(work_dir):
    reply = json.loads(_export(FakeRunner(), filepath=str(work_dir / "p.stl")))
    assert reply["size_mm"] == [20.0, 20.0, 20.0]
    assert reply["triangles"] == 12
    assert reply["watertight"] is True
    assert reply["warnings"] == REPORT["warnings"]
    assert reply["objects"][0]["boundary_edges"] == 0
    assert reply["filepath"] == str((work_dir / "p.stl").resolve())


def test_script_errors_come_back_as_text(work_dir):
    reply = _export(FakeRunner(result={"error": "no object named 'Gear'"}), filepath=str(work_dir / "p.stl"))
    assert reply == "Error: no object named 'Gear'"


def test_connection_errors_come_back_as_text(work_dir):
    reply = _export(FakeRunner(error=ConnectionError("Not connected to Blender")),
                    filepath=str(work_dir / "p.stl"))
    assert reply.startswith("Error: ") and "Not connected to Blender" in reply


def test_tool_is_registered_with_a_description():
    mcp = FastMCP("test")
    register(mcp, FakeRunner())
    (tool,) = asyncio.run(mcp.list_tools())
    assert tool.name == "export_for_print"
    text = tool.description.lower()
    for phrase in ("millimet", "one stl", "scene", "warnings"):
        assert phrase in text, phrase
    names = tool.inputSchema["properties"]["names"]
    assert any(option.get("type") == "null" for option in names.get("anyOf", []))


def test_the_blender_server_offers_the_tool():
    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    assert "export_for_print" in names


# --- the Blender script -----------------------------------------------------------


def test_built_script_compiles():
    code = blender_scripts.build(EXPORT_FOR_PRINT, {"names": ["Cube"], "filepath": "C:/x.stl",
                                                    "build_volume_mm": 256.0})
    compile(code, "export_for_print", "exec")
    compile(STL_WRITER, "stl_writer", "exec")


def test_script_never_uses_operators_or_exits():
    for text in (EXPORT_FOR_PRINT, STL_WRITER):
        assert "bpy.ops" not in text
        assert "SystemExit" not in text and "sys.exit" not in text


def test_script_includes_the_writer_and_frees_temporary_meshes():
    assert STL_WRITER.strip() in EXPORT_FOR_PRINT
    assert "to_mesh_clear()" in EXPORT_FOR_PRINT
    assert ".free()" in EXPORT_FOR_PRINT


# --- the STL writer, run without Blender ------------------------------------------


def _writer():
    namespace = {}
    exec(STL_WRITER, namespace)
    return namespace["write_binary_stl"]


def _cube_coords():
    coords = []
    for _normal, triangle in _FACES:
        for index in triangle:
            coords.extend(float(v) for v in _CORNERS[index])
    return coords


def _read_stl(path):
    data = path.read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    triangles = [struct.unpack_from("<12fH", data, 84 + 50 * i) for i in range(count)]
    return data, count, triangles


def test_writer_round_trip_of_a_cube(tmp_path):
    path = tmp_path / "cube.stl"
    assert _writer()(str(path), _cube_coords()) == 12
    data, count, triangles = _read_stl(path)
    assert len(data) == 84 + 12 * 50
    assert count == 12
    assert not data.startswith(b"solid"), "a binary STL header must not look like ASCII STL"
    for (expected, triangle), record in zip(_FACES, triangles):
        normal = record[0:3]
        assert math.isclose(math.hypot(*normal), 1.0, abs_tol=1e-6)
        assert normal == pytest.approx(expected, abs=1e-6)
        assert record[3:12] == tuple(float(v) for i in triangle for v in _CORNERS[i])
        assert record[12] == 0


def test_writer_handles_a_degenerate_triangle(tmp_path):
    path = tmp_path / "flat.stl"
    _writer()(str(path), [0.0] * 3 + [1.0, 0.0, 0.0] + [2.0, 0.0, 0.0])
    _, count, triangles = _read_stl(path)
    assert count == 1
    assert triangles[0][0:3] == (0.0, 0.0, 0.0)


def test_writer_rejects_a_partial_triangle(tmp_path):
    with pytest.raises(ValueError):
        _writer()(str(tmp_path / "bad.stl"), [0.0] * 10)
    assert not (tmp_path / "bad.stl").exists()


def test_writer_replaces_the_file_whole(tmp_path):
    path = tmp_path / "cube.stl"
    path.write_bytes(b"old")
    _writer()(str(path), _cube_coords())
    assert len(path.read_bytes()) == 684
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cube.stl"]


def test_module_exposes_the_triangle_limit():
    assert print_export.MAX_TRIANGLES == 2_000_000
    assert "2000000" in EXPORT_FOR_PRINT.replace("_", "")
