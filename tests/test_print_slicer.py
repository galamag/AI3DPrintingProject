"""print_mcp.slicer: running the Bambu Studio CLI, with subprocess.run replaced by a fake."""
from __future__ import annotations

import json
import subprocess
import zipfile
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
SUCCESS = {"error_string": "Success.", "return_code": 0}


def _write(root, kind, name, **data):
    folder = root / kind
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"type": kind, "name": name, **data}
    (folder / f"{name}.json").write_text(json.dumps(payload, indent=4), encoding="utf-8")


@pytest.fixture
def studio(tmp_path, monkeypatch):
    """A fake Bambu Studio folder holding the default P2S profiles and a few wrong ones."""
    studio = tmp_path / "studio"
    root = studio / "resources" / "profiles" / "BBL"
    _write(root, "machine", "fdm_bbl_common", instantiation="false",
           machine_start_gcode="G28 ; home all axes", printable_height="250")
    _write(root, "machine", "P2S template machine_start_gcode", instantiation="false",
           machine_start_gcode=";=== P2S start ===")
    _write(root, "machine", MACHINE, inherits="fdm_bbl_common", instantiation="true",
           nozzle_diameter=["0.4"], include=["P2S template machine_start_gcode"])
    _write(root, "process", "fdm_process_common", instantiation="false",
           sparse_infill_density="15%", inner_wall_speed=["300", "600", "600"],
           standby_temperature_delta="-5", post_process=[""], filename_format="x")
    _write(root, "process", PROCESS, inherits="fdm_process_common", instantiation="true",
           description="Standard profile", wall_loops="2", compatible_printers=[MACHINE])
    _write(root, "filament", "Bambu PLA Lite @base", instantiation="false",
           filament_density=["1.40"], nozzle_temperature=["220"])
    _write(root, "filament", FILAMENT, inherits="Bambu PLA Lite @base", instantiation="true",
           compatible_printers=[MACHINE])
    _write(root, "filament", "Bambu PLA Lite @BBL X1C", inherits="Bambu PLA Lite @base",
           instantiation="true", compatible_printers=["Bambu Lab X1 Carbon 0.4 nozzle"])
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
    """Stands in for subprocess.run and behaves like the Bambu Studio CLI.

    `record` says how the exported project records the process keys changed from the system
    preset: "copy" does what the real CLI does with an STL model (the first entry of the
    process file's different_settings_to_system becomes the project's process entry),
    "empty" leaves it empty, as the CLI does for a Bambu 3mf model, and "missing" writes no
    project settings at all.
    """

    def __init__(self, *, exit_code=0, result=SUCCESS, archive=True, archive_kwargs=None,
                 timeout=False, stdout=b"", stderr=b"", record="copy"):
        self.exit_code = exit_code
        self.result = result
        self.archive = archive
        self.archive_kwargs = archive_kwargs or {}
        self.timeout = timeout
        self.stdout, self.stderr = stdout, stderr
        self.record = record
        self.calls = []

    def __call__(self, args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.calls.append(args)
        self.cwd = Path(kwargs["cwd"])
        self.cwd_existed = self.cwd.is_dir()
        self.export = Path(args[args.index("--export-3mf") + 1])
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
            raise subprocess.TimeoutExpired(args, kwargs.get("timeout"), self.stdout, self.stderr)
        if self.result is not None:
            (self.cwd / "result.json").write_text(json.dumps(self.result), encoding="utf-8")
        if self.archive:
            archive_kwargs = dict(self.archive_kwargs)
            if self.record != "missing":
                passed = self.json["process"].get(slicer.CHANGED_KEYS_RECORD) or [""]
                archive_kwargs.setdefault("project_settings", {
                    "name": "project_settings",
                    "from": "project",
                    "different_settings_to_system": [passed[0] if self.record == "copy" else "", "", ""],
                    "inherits_group": ["", "", ""],
                })
            write_archive(self.export, **archive_kwargs)
        return subprocess.CompletedProcess(args, self.exit_code, self.stdout, self.stderr)


@pytest.fixture
def fake(monkeypatch):
    def install(**options):
        studio = FakeStudio(**options)
        monkeypatch.setattr(slicer.subprocess, "run", studio)
        return studio

    return install


def _files(folder):
    return sorted(path.name for path in folder.iterdir() if path.is_file())


def _assert_nothing_published(result, out, run=None):
    assert result["ok"] is False
    assert not out.exists(), "a failed slice must leave no file at the output path"
    assert not (out.parent / (out.name[: -len(".gcode.3mf")] + ".plate.png")).exists()
    if run is not None:
        assert not run.export.exists(), "the partial export must be removed"


# --- the call -----------------------------------------------------------------


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
        "--export-3mf", str(run.export),
        str(model.resolve()),
    ]
    # The CLI writes beside the output (same volume), never onto the output itself.
    assert run.export.parent == out.parent.resolve()
    assert run.export != out.resolve()
    assert run.export.name.endswith(".gcode.3mf")
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
    # Nothing is overridden, so no profile carries a record of changed keys.
    for kind in ("machine", "process", "filament"):
        assert slicer.CHANGED_KEYS_RECORD not in run.json[kind]

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["error_string"] == "Success."
    assert result["output"] == str(out.resolve())
    assert result["result"] == SUCCESS
    assert result["mismatches"] == []
    assert result["cli_output"] is None
    summary = result["summary"]
    assert summary["path"] == str(out.resolve())
    assert summary["plates"] == 1
    assert summary["layers"] == 100
    assert summary["weight_source"] == "computed"
    assert summary["filament_weight_g"] == pytest.approx(4.28, abs=0.01)
    assert summary["thumbnail"] == str((out.parent / "cube.plate.png").resolve())
    assert _files(out.parent) == ["cube.gcode.3mf", "cube.plate.png"]


def test_cyrillic_and_space_paths_pass_unchanged(studio, work_dir, fake):
    run = fake()
    model = work_dir / "модели с пробелом" / "деталь 1.stl"
    model.parent.mkdir()
    model.write_text("solid x\nendsolid x\n", encoding="utf-8")
    out = work_dir / "срез с пробелом" / "деталь 1.gcode.3mf"

    result = slicer.slice_model(str(model), str(out))

    assert run.args[-1] == str(model.resolve())
    assert run.export.parent == out.parent.resolve()
    assert result["ok"] is True
    assert result["output"] == str(out.resolve())
    assert out.is_file()
    assert result["summary"]["thumbnail"] == str((out.parent / "деталь 1.plate.png").resolve())


def test_stale_output_and_thumbnail_are_removed_before_run(studio, work_dir, model, monkeypatch):
    out = work_dir / "cube.gcode.3mf"
    out.write_bytes(b"stale slice")
    (work_dir / "cube.plate.png").write_bytes(b"stale thumbnail")
    (work_dir / "cube.png").write_bytes(b"someone else's picture")
    seen = {}

    def check_before_run(args, **kwargs):
        seen["output"] = out.exists()
        seen["thumbnail"] = (work_dir / "cube.plate.png").exists()
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(slicer.subprocess, "run", check_before_run)
    result = slicer.slice_model(model, out)

    assert seen == {"output": False, "thumbnail": False}
    _assert_nothing_published(result, out)
    assert result["summary"] is None
    assert result["error_string"]
    assert (work_dir / "cube.png").read_bytes() == b"someone else's picture"


# --- failures leave nothing at the output path ------------------------------


def test_crash_without_result_json(studio, work_dir, model, fake):
    run = fake(exit_code=CRASH, result=None, archive=False, stderr=b"fatal \xff error")
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert result["exit_code"] == CRASH
    assert "0xC0000005" in result["error_string"]
    assert result["result"] is None
    assert result["summary"] is None
    assert "fatal � error" in result["cli_output"]


def test_exit_zero_without_result_json(studio, work_dir, model, fake):
    run = fake(result=None)
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert "result.json" in result["error_string"]
    assert result["cli_output"] == ""


def test_nonzero_exit_with_an_archive(studio, work_dir, model, fake):
    run = fake(exit_code=1, stdout=b"slicing went wrong")
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert result["exit_code"] == 1
    assert result["summary"]["path"] is None, "the discarded slice has no path"
    assert "slicing went wrong" in result["cli_output"]


def test_result_json_with_failure_and_exit_zero(studio, work_dir, model, fake):
    run = fake(result={"error_string": "Nothing to be sliced.", "return_code": -100})
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert result["exit_code"] == 0
    assert result["error_string"] == "Nothing to be sliced."


def test_settings_mismatch(studio, work_dir, model, fake):
    run = fake(archive_kwargs={"process": "0.16mm Standard @BBL P2S"})
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert result["mismatches"] == [
        {"key": "print_settings_id", "expected": PROCESS, "actual": "0.16mm Standard @BBL P2S"}
    ]


def test_more_than_one_plate(studio, work_dir, model, fake):
    run = fake(archive_kwargs={"plates": 2})
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert "2 plates" in result["error_string"]
    assert result["summary"]["plates"] == 2


def test_failed_move_into_place(studio, work_dir, model, fake, monkeypatch):
    run = fake()

    def refuse(src, dst):
        raise PermissionError("output is open in another program")

    monkeypatch.setattr(slicer.os, "replace", refuse)
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out)
    _assert_nothing_published(result, out, run)
    assert "open in another program" in result["error_string"]


def test_timeout(studio, work_dir, model, fake):
    run = fake(timeout=True, stderr=b"still slicing")
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out, timeout=5)
    _assert_nothing_published(result, out, run)
    assert result["error_string"] == "timeout"
    assert result["exit_code"] is None
    assert result["summary"] is None
    assert "still slicing" in result["cli_output"]


def test_cli_output_is_cut_to_the_tail(studio, work_dir, model, fake):
    fake(exit_code=1, archive=False, stderr=b"x" * 5000 + b"END")
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf")
    assert result["cli_output"].endswith("END")
    assert len(result["cli_output"]) < 2100


# --- input checks before the CLI runs ---------------------------------------


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


@pytest.mark.parametrize(
    "kind, name",
    [
        ("machine", "fdm_bbl_common"),
        ("process", "fdm_process_common"),
        ("filament", "Bambu PLA Lite @base"),
    ],
)
def test_base_profiles_are_rejected(studio, work_dir, model, fake, kind, name):
    run = fake()
    with pytest.raises(ValueError, match="instantiable"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", **{kind: name})
    assert run.calls == []


def test_filament_for_another_printer_is_rejected(studio, work_dir, model, fake):
    run = fake()
    with pytest.raises(ValueError, match="compatible"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", filament="Bambu PLA Lite @BBL X1C")
    assert run.calls == []


def test_process_without_compatible_printers_is_rejected(studio, work_dir, model, fake):
    root = studio / "resources" / "profiles" / "BBL"
    _write(root, "process", "0.20mm Loose @BBL P2S", inherits="fdm_process_common",
           instantiation="true")
    run = fake()
    with pytest.raises(ValueError, match="compatible"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", process="0.20mm Loose @BBL P2S")
    assert run.calls == []


# --- overrides ----------------------------------------------------------------


def test_unknown_override_key(studio, work_dir, model, fake):
    run = fake()
    with pytest.raises(ValueError, match="no_such_key"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={"no_such_key": "1"})
    assert run.calls == []


@pytest.mark.parametrize("key", ["filament_density", "printable_height", "nozzle_temperature"])
def test_override_keys_outside_the_process_profile(studio, work_dir, model, fake, key):
    # filament_density lives only in the filament, printable_height only in the machine;
    # nozzle_temperature is a filament key and is denied outright.
    run = fake()
    with pytest.raises(ValueError):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={key: "1"})
    assert run.calls == []


@pytest.mark.parametrize(
    "key",
    [
        "name", "type", "from", "inherits", "include", "setting_id", "instantiation",
        "post_process", "machine_start_gcode", "gcode_add_line_number",
        "standby_temperature_delta", "chamber_temperatures", "filename_format",
        "compatible_printers", "compatible_printers_condition",
        "print_extruder_id", "print_extruder_variant", "different_settings_to_system",
    ],
)
def test_denied_override_keys(studio, work_dir, model, fake, key):
    run = fake()
    with pytest.raises(ValueError, match="cannot be changed"):
        slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={key: "x"})
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


def _project_record(path):
    with zipfile.ZipFile(path) as archive:
        settings = json.loads(archive.read("Metadata/project_settings.config"))
    return settings["different_settings_to_system"]


def test_overrides_are_recorded_as_changed_from_the_system_preset(studio, work_dir, model, fake):
    # The window resets every process key the project does not list as changed, so the
    # process file tells the CLI which keys differ, one ';'-joined entry, sorted.
    run = fake()
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(
        model,
        out,
        overrides={"wall_loops": "4", "sparse_infill_density": "30%", "inner_wall_speed": "250"},
    )

    assert result["ok"] is True, result
    assert run.json["process"][slicer.CHANGED_KEYS_RECORD] == [
        "inner_wall_speed;sparse_infill_density;wall_loops"
    ]
    for kind in ("machine", "filament"):
        assert slicer.CHANGED_KEYS_RECORD not in run.json[kind]
    assert _project_record(out)[0] == "inner_wall_speed;sparse_infill_density;wall_loops"


def test_overrides_equal_to_the_profile_are_not_recorded(studio, work_dir, model, fake):
    # wall_loops is already "2". No entry at all, never an empty list: the CLI reads entry 0.
    run = fake()
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={"wall_loops": "2"})

    assert result["ok"] is True, result
    assert slicer.CHANGED_KEYS_RECORD not in run.json["process"]


def test_only_changed_overrides_are_recorded(studio, work_dir, model, fake):
    run = fake()
    result = slicer.slice_model(
        model,
        work_dir / "cube.gcode.3mf",
        overrides={"wall_loops": "2", "inner_wall_speed": "300"},
    )

    assert result["ok"] is True, result
    # inner_wall_speed was ["300", "600", "600"], so filling it with "300" changes it.
    assert run.json["process"][slicer.CHANGED_KEYS_RECORD] == ["inner_wall_speed"]


def test_project_may_record_more_keys_than_were_overridden(studio, work_dir, model, fake):
    # The CLI itself adds keys such as enable_prime_tower to the process entry.
    fake(archive_kwargs={"project_settings": {
        "different_settings_to_system": ["enable_prime_tower;wall_loops", "", ""],
    }})
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf", overrides={"wall_loops": "4"})
    assert result["ok"] is True, result


@pytest.mark.parametrize("record", ["empty", "missing"])
def test_slice_whose_project_drops_the_overrides_is_refused(studio, work_dir, model, fake, record):
    # Opened in the window, such a file would fall back to the plain system preset.
    run = fake(record=record)
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(
        model, out, overrides={"wall_loops": "4", "sparse_infill_density": "30%"}
    )

    _assert_nothing_published(result, out, run)
    assert "sparse_infill_density, wall_loops" in result["error_string"]
    assert "Bambu Studio window" in result["error_string"]
    assert result["summary"]["path"] is None


@pytest.mark.parametrize(
    "project_settings",
    [
        {"different_settings_to_system": []},
        {"different_settings_to_system": "wall_loops"},
        {"different_settings_to_system": [4, "", ""]},
        ["not", "an", "object"],
    ],
)
def test_malformed_project_record_is_refused(studio, work_dir, model, fake, project_settings):
    run = fake(archive_kwargs={"project_settings": project_settings})
    out = work_dir / "cube.gcode.3mf"
    result = slicer.slice_model(model, out, overrides={"wall_loops": "4"})
    _assert_nothing_published(result, out, run)
    assert "wall_loops" in result["error_string"]


def test_project_record_is_not_checked_without_overrides(studio, work_dir, model, fake):
    fake(record="missing")
    result = slicer.slice_model(model, work_dir / "cube.gcode.3mf")
    assert result["ok"] is True, result


# --- vendor index ---------------------------------------------------------------


def test_filament_named_with_a_slash_through_the_vendor_index(studio, work_dir, model, fake):
    root = studio / "resources" / "profiles" / "BBL"
    support = "Bambu Support For PA/PET @BBL P2S"
    (root / "filament" / "Bambu Support For PA PET @BBL P2S.json").write_text(
        json.dumps({"type": "filament", "name": support, "inherits": "Bambu PLA Lite @base",
                    "instantiation": "true", "compatible_printers": [MACHINE]}),
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
