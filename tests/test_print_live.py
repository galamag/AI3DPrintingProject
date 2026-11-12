"""Live slice through the installed Bambu Studio CLI. Skipped where Bambu Studio is absent.

Runs only `bambu-studio.exe --slice` on a 20 mm cube written into pytest's tmp_path.
It never opens the Bambu Studio window and never talks to a printer.
"""
from __future__ import annotations

import pytest

from print_mcp.paths import studio_exe
from print_mcp.profiles import list_profiles
from print_mcp.slicer import slice_model

pytestmark = pytest.mark.skipif(not studio_exe().is_file(), reason="Bambu Studio is not installed")

# (x, y, z) corners of a 20 mm cube, and its 12 outward-facing triangles.
_CORNERS = [(x, y, z) for z in (0, 20) for y in (0, 20) for x in (0, 20)]
_FACES = [
    ((0, 0, -1), (0, 2, 3)), ((0, 0, -1), (0, 3, 1)),
    ((0, 0, 1), (4, 5, 7)), ((0, 0, 1), (4, 7, 6)),
    ((0, -1, 0), (0, 1, 5)), ((0, -1, 0), (0, 5, 4)),
    ((0, 1, 0), (2, 6, 7)), ((0, 1, 0), (2, 7, 3)),
    ((-1, 0, 0), (0, 4, 6)), ((-1, 0, 0), (0, 6, 2)),
    ((1, 0, 0), (1, 3, 7)), ((1, 0, 0), (1, 7, 5)),
]


def _write_cube_stl(path):
    lines = ["solid cube20"]
    for normal, triangle in _FACES:
        lines.append("  facet normal {} {} {}".format(*normal))
        lines.append("    outer loop")
        for index in triangle:
            lines.append("      vertex {} {} {}".format(*_CORNERS[index]))
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid cube20")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


@pytest.fixture
def cube(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(tmp_path))
    return _write_cube_stl(tmp_path / "модель с пробелом" / "куб 20.stl")


def test_real_profiles_list_the_defaults():
    listing = list_profiles(printer="P2S", nozzle="0.4")
    assert [m["name"] for m in listing["machines"]] == ["Bambu Lab P2S 0.4 nozzle"]
    processes = [p["name"] for p in listing["processes"]]
    assert "0.20mm Standard @BBL P2S" in processes
    assert not any(name.endswith("nozzle") for name in processes)
    lite = [f for f in listing["filaments"] if f["name"] == "Bambu PLA Lite @BBL P2S 0.4 nozzle"]
    assert lite and lite[0]["filament_density"] == "1.40"


def test_live_slice_of_a_20mm_cube(cube, tmp_path):
    out = tmp_path / "срез с пробелом" / "куб 20.gcode.3mf"
    result = slice_model(cube, out)

    assert result["ok"] is True, result
    assert result["output"] == str(out.resolve())
    summary = result["summary"]
    assert summary["layers"] == 100
    assert summary["max_z_mm"] == 20.0
    assert summary["weight_source"] == "computed"
    assert 3.5 <= summary["filament_weight_g"] <= 5.0
    assert (out.parent / "куб 20.png").is_file()


def test_live_slice_with_override(cube, tmp_path):
    out = tmp_path / "срез с пробелом" / "куб 20 infill 30.gcode.3mf"
    result = slice_model(cube, out, overrides={"sparse_infill_density": "30%"})

    assert result["ok"] is True, result
    assert result["summary"]["settings"]["sparse_infill_density"] == "30%"
    assert result["summary"]["settings"]["print_settings_id"] == "0.20mm Standard @BBL P2S"
