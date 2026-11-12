"""print_mcp.slicer: running the Bambu Studio CLI, with subprocess.run replaced by a fake."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from print_mcp import slicer
from print_mcp.paths import PathNotAllowed
from print_mcp.profiles import ProfileNotFound
from test_print_inspect import write_archive

MACHINE = "Bambu Lab P2S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL P2S"
FILAMENT = "Bambu PLA Lite @BBL P2S 0.4 nozzle"
CRASH = 3221225477  # 0xC0000005, access violation


def _write(root, kind, name, **data):
    folder = root / kind
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"type": kind, "name": name, **data}
    (folder / f"{name}.json").write_text(json.dumps(payload, indent=4), encoding="utf-8")


@pytest.fixture
def studio(tmp_path, monkeypatch):
    """A fake Bambu Studio folder holding just the default P2S profiles."""
    studio = tmp_path / "studio"
    root = studio / "resources" / "profiles" / "BBL"
    _write(root, "machine", "fdm_bbl_common", instantiation="false",
           machine_start_gcode="G28 ; home all axes", printable_height="250")
    _write(root, "machine", "P2S template machine_start_gcode", instantiation="false",
           machine_start_gcode=";=== P2S start ===")
    _write(root, "machine", MACHINE, inherits="fdm_bbl_common", instantiation="true",
           nozzle_diameter=["0.4"], include=["P2S template machine_start_gcode"])
    _write(root, "process", "fdm_process_common", instantiation="false",
           sparse_infill_density="15%", inner_wall_speed=["300", "600", "600"])
    _write(root, "process", PROCESS, inherits="fdm_process_common", instantiation="true",
           description="Standard profile", wall_loops="2")
    _write(root, "filament", "Bambu PLA Lite @base", instantiation="false",
           filament_density=["1.40"])
    _write(root, "filament", FILAMENT, inherits="Bambu PLA Lite @base", instantiation="true")
    monkeypatch.setenv("BAMBU_STUDIO_DIR", str(studio))
    return studio


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(work))
    return work


@pytest.fixture
def model(work_dir):
    path = work_dir / "cube.stl"
    path.write_text("solid cube\nendsolid cube\n", encoding="utf-8")
    return path


class FakeStudio:
    """Stands in for subprocess.run and behaves like the Bambu Studio CLI."""

    def __init__(self, *, exit_code=0, write_result=True, archive=True, archive_kwargs=None,
                 timeout=False):
        self.exit_code = exit_code
        self.write_result = write_result
        self.archive = archive
        self.archive_kwargs = archive_kwargs or {}
        self.timeout = timeout
        self.calls = []

    def __call__(self, args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.calls.append(args)
        self.cwd = Path(kwargs["cwd"])
        self.cwd_existed = self.cwd.is_dir()
        out = Path(args[args.index("--export-3mf") + 1])
        self.output_existed = out.exists()
        machine_file, process_file = args[args.index("--load-settings") + 1].split(";")
        self.files = {
            "machine": Path(machine_file),
            "process": Path(process_file),
            "filament": Path(args[args.index("--load-filaments") + 1]),
        }
        self.json = {
            kind: json.loads(path.read_text(encoding="utf-8")) for kind, path in self.files.items()
        }
        if self.timeout:
            raise subprocess.TimeoutExpired(args, kwargs.get("timeout"))
        if self.write_result:
            payload = {"error_string": "Success.", "return_code": 0}
            (self.cwd / "result.json").write_text(json.dumps(payload), encoding="utf-8")
        if self.archive:
            write_archive(out, **self.archive_kwargs)
        return subprocess.CompletedProcess(args, self.exit_code, b"", b"")


@pytest.fixture
def fake(monkeypatch):
    def install(**options):
        studio = FakeStudio(**options)
        monkeypatch.setattr(slicer.subprocess, "run", studio)
        return studio

    return install


def test_arguments_match_verified_call(studio, work_dir, model, fake):
    run = fake()
    out = work_dir / "out" / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)

    folder = run.files["machine"].parent
    assert isinstance(run.args, list)
    assert run.args == [
        str(studio / "bambu-studio.exe"),
        "--debug", "3",
        "--curr-bed-type", "Textured PEI Plate",
        "--load-settings", f"{folder / 'machine.json'};{folder / 'process.json'}",
        "--load-filaments", str(folder / "filament.json"),
        "--slice", "0",
        "--export-3mf", str(out.resolve()),
        str(model.resolve()),
    ]
    assert not folder.is_relative_to(studio), "profiles must be flattened copies, not the originals"
    assert not run.kwargs.get("shell")
    assert run.kwargs["stdin"] == subprocess.DEVNULL
    assert run.kwargs["capture_output"] is True
    assert run.cwd_existed
    assert not run.cwd.exists(), "the temporary working folder must be removed"
    assert not folder.exists(), "the flattened profiles must be removed"

    # Every file is self-contained: parents and include templates are merged in.
    for kind, name in (("machine", MACHINE), ("process", PROCESS), ("filament", FILAMENT)):
        assert run.json[kind]["name"] == name
        assert run.json[kind]["type"] == kind
        assert "inherits" not in run.json[kind]
        assert "include" not in run.json[kind]
    assert run.json["machine"]["machine_start_gcode"] == ";=== P2S start ==="
    assert run.json["machine"]["printable_height"] == "250"
    assert run.json["process"]["sparse_infill_density"] == "15%"
    assert run.json["process"]["wall_loops"] == "2"
    assert run.json["filament"]["filament_density"] == ["1.40"]

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["error_string"] == "Success."
    assert result["output"] == str(out.resolve())
    assert result["result"] == {"error_string": "Success.", "return_code": 0}
    assert result["mismatches"] == []
    summary = result["summary"]
    assert summary["layers"] == 100
    assert summary["weight_source"] == "computed"
    assert summary["filament_weight_g"] == pytest.approx(4.28, abs=0.01)
    assert summary["thumbnail"] == str((out.parent / "cube.png").resolve())
    assert (out.parent / "cube.png").is_file()


def test_cyrillic_and_space_paths_pass_unchanged(studio, work_dir, fake):
    run = fake()
    model = work_dir / "модели с пробелом" / "деталь 1.stl"
    model.parent.mkdir()
    model.write_text("solid x\nendsolid x\n", encoding="utf-8")
    out = work_dir / "срез с пробелом" / "деталь 1.gcode.3mf"

    result = slicer.slice_model(str(model), str(out))

    assert run.args[-1] == str(model.resolve())
    assert run.args[-2] == str(out.resolve())
    assert result["ok"] is True
    assert result["output"] == str(out.resolve())
    assert result["summary"]["thumbnail"] == str((out.parent / "деталь 1.png").resolve())


def test_old_output_is_removed_before_run(studio, work_dir, model, fake):
    run = fake(archive=False)
    out = work_dir / "cube.gcode.3mf"
    out.write_bytes(b"stale slice")
    (work_dir / "cube.png").write_bytes(b"stale thumbnail")

    result = slicer.slice_model(model, out)

    assert run.output_existed is False
    assert not out.exists()
    assert not (work_dir / "cube.png").exists()
    assert result["ok"] is False
    assert result["summary"] is None
    assert result["error_string"]


def test_crash_without_result_json(studio, work_dir, model, fake):
    fake(exit_code=CRASH, write_result=False, archive=False)
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf")
    assert result["ok"] is False
    assert result["exit_code"] == CRASH
    assert result["error_string"]
    assert result["result"] is None
    assert result["summary"] is None


def test_output_outside_roots(studio, work_dir, model, fake, tmp_path_factory):
    run = fake()
    outside = tmp_path_factory.mktemp("outside") / "cube.gcode.3mf"
    with pytest.raises(PathNotAllowed):
        slicer.slice_model(model, outside)
    assert run.calls == []


def test_output_needs_gcode_3mf_suffix(studio, work_dir, model, fake):
    run = fake()
    with pytest.raises(ValueError, match=r"\.gcode\.3mf"):
        slicer.slice_model(model, work_dir / "cube.3mf")
    assert run.calls == []


def test_model_suffix_is_checked(studio, work_dir, fake):
    run = fake()
    model = work_dir / "cube.fbx"
    model.write_bytes(b"x")
    with pytest.raises(ValueError, match="model"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf")
    assert run.calls == []


def test_missing_model(studio, work_dir, fake):
    run = fake()
    with pytest.raises(ValueError):
        slicer.slice_model(work_dir / "absent.stl", work_dir / "cube.gcode.3mf")
    assert run.calls == []


def test_unknown_profile(studio, work_dir, model, fake):
    run = fake()
    with pytest.raises(ProfileNotFound):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", machine="Bambu Lab P2S 0.6 nozzle")
    with pytest.raises(ValueError):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", process="a;b")
    assert run.calls == []


def test_settings_mismatch(studio, work_dir, model, fake):
    fake(archive_kwargs={"process": "0.16mm Standard @BBL P2S"})
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf")
    assert result["ok"] is False
    assert result["mismatches"] == [
        {"key": "print_settings_id", "expected": PROCESS, "actual": "0.16mm Standard @BBL P2S"}
    ]


def test_unknown_override_key(studio, work_dir, model, fake):
    run = fake()
    with pytest.raises(ValueError, match="no_such_key"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={"no_such_key": "1"})
    assert run.calls == []


def test_overrides_go_into_the_flattened_process(studio, work_dir, model, fake):
    run = fake()
    result = slicer.slice_model(
        model,
        work_dir / "cube.gcode.3mf",
        overrides={"sparse_infill_density": "30%", "inner_wall_speed": "250"},
    )
    assert result["ok"] is True

    process = run.json["process"]
    assert process["name"] == PROCESS
    assert "inherits" not in process
    assert process["description"] == "Standard profile"
    assert process["wall_loops"] == "2"
    assert process["sparse_infill_density"] == "30%"
    assert process["inner_wall_speed"] == ["250", "250", "250"]
    assert not run.files["process"].exists(), "the temporary profile must be removed"
    original = studio / "resources" / "profiles" / "BBL" / "process" / f"{PROCESS}.json"
    assert json.loads(original.read_text(encoding="utf-8")).get("sparse_infill_density") is None


@pytest.mark.parametrize("key", ["name", "inherits", "include", "setting_id"])
def test_identity_keys_cannot_be_overridden(studio, work_dir, model, fake, key):
    run = fake()
    with pytest.raises(ValueError, match="cannot be changed"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={key: "x"})
    assert run.calls == []


def test_filament_named_with_a_slash_through_the_vendor_index(studio, work_dir, model, fake):
    root = studio / "resources" / "profiles" / "BBL"
    support = "Bambu Support For PA/PET @BBL P2S"
    (root / "filament" / "Bambu Support For PA PET @BBL P2S.json").write_text(
        json.dumps({"type": "filament", "name": support, "inherits": "Bambu PLA Lite @base",
                    "instantiation": "true"}),
        encoding="utf-8",
    )
    index = {
        "machine_list": [
            {"name": name, "sub_path": f"machine/{name}.json"}
            for name in ("fdm_bbl_common", "P2S template machine_start_gcode", MACHINE)
        ],
        "process_list": [
            {"name": name, "sub_path": f"process/{name}.json"}
            for name in ("fdm_process_common", PROCESS)
        ],
        "filament_list": [
            {"name": "Bambu PLA Lite @base", "sub_path": "filament/Bambu PLA Lite @base.json"},
            {"name": support, "sub_path": "filament/Bambu Support For PA PET @BBL P2S.json"},
        ],
    }
    (root.parent / "BBL.json").write_text(json.dumps(index), encoding="utf-8")
    run = fake(archive_kwargs={"filament": support})

    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf", filament=support)

    assert run.json["filament"]["name"] == support
    assert run.files["filament"].name == "filament.json"
    assert result["ok"] is True, result


def test_timeout(studio, work_dir, model, fake):
    fake(timeout=True)
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf", timeout=5)
    assert result["ok"] is False
    assert result["error_string"] == "timeout"
    assert result["exit_code"] is None
    assert result["summary"] is None
