"""print_mcp.inspect3mf: reading a sliced .gcode.3mf archive."""
from __future__ import annotations

import zipfile

import pytest

from print_mcp.inspect3mf import NotSliced, inspect_sliced
from print_mcp.paths import PathNotAllowed

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"plate thumbnail"

HEADER = """\
; HEADER_BLOCK_START
; BambuStudio 02.09.01.70
; model printing time: 10m 26s; total estimated time: 10m 27s
; total layer number: 100
; total filament length [mm] : 1270.15
; total filament weight [g] : {weight}
; filament_diameter: 1.75
; max_z_height: 20.00
; HEADER_BLOCK_END

; CONFIG_BLOCK_START
; curr_bed_type = {bed}
; filament_density = 1.4
; filament_settings_id = "{filament}"
; print_settings_id = {process}
; printer_settings_id = {machine}
; sparse_infill_density = {infill}
; top_shell_layers = 5
; CONFIG_BLOCK_END

G28
G1 X10 Y10 F3000
"""

SLICE_INFO = """\
<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
  </header>
  <plate>
    <metadata key="index" value="1"/>
    <metadata key="prediction" value="627"/>
    <metadata key="weight" value=""/>
  </plate>
</config>
"""


def write_archive(
    path,
    *,
    weight="0.00",
    machine="Bambu Lab P2S 0.4 nozzle",
    process="0.20mm Standard @BBL P2S",
    filament="Bambu PLA Lite @BBL P2S 0.4 nozzle",
    bed="Textured PEI Plate",
    infill="20%",
    gcode=True,
):
    """Write a minimal sliced archive shaped like Bambu Studio's output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        if gcode:
            text = HEADER.format(weight=weight, machine=machine, process=process,
                                 filament=filament, bed=bed, infill=infill)
            archive.writestr("Metadata/plate_1.gcode", text.replace("\n", "\r\n"))
        archive.writestr("Metadata/slice_info.config", SLICE_INFO)
        archive.writestr("Metadata/plate_1.png", PNG_BYTES)
        archive.writestr("3D/3dmodel.model", "<model/>")
    return path


@pytest.fixture(autouse=True)
def work_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def sliced(tmp_path):
    return write_archive(tmp_path / "cube.gcode.3mf")


def test_reads_header_and_slice_info(sliced):
    info = inspect_sliced(sliced)
    assert info["path"] == str(sliced.resolve())
    assert info["time_s"] == 627
    assert info["time_text"] == "10m 27s"
    assert info["layers"] == 100
    assert info["filament_length_mm"] == 1270.15
    assert info["max_z_mm"] == 20.0
    assert info["thumbnail"] is None


def test_settings_are_unquoted_and_complete(sliced):
    settings = inspect_sliced(sliced)["settings"]
    assert settings["filament_settings_id"] == "Bambu PLA Lite @BBL P2S 0.4 nozzle"
    assert settings["print_settings_id"] == "0.20mm Standard @BBL P2S"
    assert settings["printer_settings_id"] == "Bambu Lab P2S 0.4 nozzle"
    assert settings["curr_bed_type"] == "Textured PEI Plate"
    assert settings["sparse_infill_density"] == "20%"
    assert settings["filament_density"] == "1.4"
    assert settings["top_shell_layers"] == "5"
    for key in (
        "printer_model", "printer_settings_id", "print_settings_id", "filament_settings_id",
        "curr_bed_type", "layer_height", "nozzle_diameter", "nozzle_volume_type",
        "nozzle_temperature", "textured_plate_temp", "filament_type", "filament_colour",
        "filament_density", "sparse_infill_density", "wall_loops", "top_shell_layers",
        "enable_support",
    ):
        assert key in settings
    assert settings["wall_loops"] is None


def test_weight_is_computed_from_density(sliced):
    info = inspect_sliced(sliced, density=1.40)
    assert info["filament_weight_g"] == pytest.approx(4.28, abs=0.01)
    assert info["weight_source"] == "computed"


def test_weight_without_density_is_none(sliced):
    info = inspect_sliced(sliced)
    assert info["filament_weight_g"] is None
    assert info["weight_source"] is None


def test_weight_from_gcode_header(tmp_path):
    path = write_archive(tmp_path / "heavy.gcode.3mf", weight="3.95")
    info = inspect_sliced(path, density=1.40)
    assert info["filament_weight_g"] == 3.95
    assert info["weight_source"] == "gcode"


def test_thumbnail_is_extracted(sliced, tmp_path):
    target = tmp_path / "превью с пробелом" / "cube.png"
    info = inspect_sliced(sliced, thumbnail_to=target)
    assert info["thumbnail"] == str(target.resolve())
    assert target.read_bytes() == PNG_BYTES


def test_thumbnail_must_be_png(sliced, tmp_path):
    with pytest.raises(ValueError):
        inspect_sliced(sliced, thumbnail_to=tmp_path / "cube.txt")


def test_not_an_archive(tmp_path):
    path = tmp_path / "fake.gcode.3mf"
    path.write_text("not a zip", encoding="utf-8")
    with pytest.raises(NotSliced):
        inspect_sliced(path)


def test_archive_without_gcode(tmp_path):
    path = write_archive(tmp_path / "unsliced.3mf", gcode=False)
    with pytest.raises(NotSliced):
        inspect_sliced(path)


def test_missing_file(tmp_path):
    with pytest.raises(NotSliced):
        inspect_sliced(tmp_path / "missing.gcode.3mf")


def test_path_outside_roots(tmp_path_factory):
    outside = write_archive(tmp_path_factory.mktemp("outside") / "cube.gcode.3mf")
    with pytest.raises(PathNotAllowed):
        inspect_sliced(outside)
