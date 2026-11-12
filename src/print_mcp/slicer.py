"""Slicing a model with the Bambu Studio command line.

The CLI prints nothing. The outcome is its exit code, a `result.json` it writes into its
current folder, and the `.gcode.3mf` it exports. It crashes (0xC0000005) when it gets no
machine, process and filament profiles, so all three are always passed.

The CLI applies only the keys in the files it is given and ignores `inherits` and
`include`; everything else falls back to built-in defaults (generic start G-code, filament
density 0). So each profile is flattened into one self-contained file first. The G-code
takes the settings ids from each file's `name`, so the requested names survive.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .inspect3mf import NotSliced, inspect_sliced
from .paths import resolve_allowed, studio_exe
from .profiles import flatten_profile

DEFAULT_MACHINE = "Bambu Lab P2S 0.4 nozzle"
DEFAULT_PROCESS = "0.20mm Standard @BBL P2S"
DEFAULT_FILAMENT = "Bambu PLA Lite @BBL P2S 0.4 nozzle"
DEFAULT_BED_TYPE = "Textured PEI Plate"

MODEL_SUFFIXES = (".stl", ".3mf", ".step", ".stp", ".obj")
OUTPUT_SUFFIX = ".gcode.3mf"

# Settings the sliced G-code must carry exactly as requested.
CHECKED_KEYS = ("printer_settings_id", "print_settings_id", "filament_settings_id", "curr_bed_type")

# Profile identity keys that an override must not change.
_IDENTITY_KEYS = frozenset({"type", "name", "inherits", "include", "from", "setting_id", "instantiation"})


def _first_float(value) -> float | None:
    if isinstance(value, list):
        value = value[0] if value else None
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _apply_overrides(profile: dict, process: str, overrides: dict[str, str]) -> None:
    """Set `overrides` on the flattened process profile, in place.

    A key must exist in the profile. A list value is replaced by a list of the same
    length filled with the new value.
    """
    for key, value in overrides.items():
        if key in _IDENTITY_KEYS:
            raise ValueError(f"override key {key!r} cannot be changed")
        if key not in profile:
            raise ValueError(f"process profile {process!r} has no key {key!r}")
        if not isinstance(value, str):
            raise ValueError(f"override {key!r} must be a string, got {type(value).__name__}")
        current = profile[key]
        profile[key] = [value] * max(len(current), 1) if isinstance(current, list) else value


def _read_result(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _code_text(code: int) -> str:
    return f"{code} (0x{code & 0xFFFFFFFF:08X})"


def slice_model(
    model: str | Path,
    output: str | Path,
    machine: str = DEFAULT_MACHINE,
    process: str = DEFAULT_PROCESS,
    filament: str = DEFAULT_FILAMENT,
    bed_type: str = DEFAULT_BED_TYPE,
    overrides: dict[str, str] | None = None,
    timeout: int = 600,
) -> dict:
    """Slice `model` into `output` (`*.gcode.3mf`) and summarise the result.

    Returns `ok`, `exit_code`, `error_string`, `output`, `result` (the CLI's result.json),
    `mismatches` (requested settings the G-code does not carry) and `summary`
    (`inspect_sliced` of the output, with a `<output stem>.png` plate thumbnail).
    """
    model_path = resolve_allowed(model)
    output_path = resolve_allowed(output)
    name = output_path.name
    if not name.lower().endswith(OUTPUT_SUFFIX) or len(name) == len(OUTPUT_SUFFIX):
        raise ValueError(f"output must end with {OUTPUT_SUFFIX}: {output_path}")
    if model_path.suffix.lower() not in MODEL_SUFFIXES:
        raise ValueError(f"model must be one of {', '.join(MODEL_SUFFIXES)}: {model_path}")
    if model_path == output_path:
        raise ValueError("model and output must be different files")
    if not model_path.is_file():
        raise ValueError(f"model not found: {model_path}")
    if not isinstance(bed_type, str) or not bed_type.strip():
        raise ValueError("bed_type must be a non-empty string")
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    profiles = {
        "machine": flatten_profile("machine", machine),
        "process": flatten_profile("process", process),
        "filament": flatten_profile("filament", filament),
    }
    if overrides:
        _apply_overrides(profiles["process"], process, overrides)
    density = _first_float(profiles["filament"].get("filament_density"))

    # A stale slice or thumbnail must never pass for the new one.
    thumbnail_path = output_path.with_name(name[: -len(OUTPUT_SUFFIX)] + ".png")
    output_path.unlink(missing_ok=True)
    thumbnail_path.unlink(missing_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "ok": False,
        "exit_code": None,
        "error_string": "",
        "output": str(output_path),
        "result": None,
        "mismatches": [],
        "summary": None,
    }

    with tempfile.TemporaryDirectory(prefix="print-mcp-", ignore_cleanup_errors=True) as tmp:
        work = Path(tmp)
        files = {}
        (work / "profiles").mkdir()
        for kind, data in profiles.items():
            # Fixed file names: the G-code takes the settings ids from `name`, not the file.
            files[kind] = work / "profiles" / f"{kind}.json"
            files[kind].write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        if ";" in str(work):
            raise ValueError(f"temporary folder {work} contains ';', which splits --load-settings")
        cwd = work / "cwd"
        cwd.mkdir()
        args = [
            str(studio_exe()),
            "--debug", "3",
            "--curr-bed-type", bed_type,
            "--load-settings", f"{files['machine']};{files['process']}",
            "--load-filaments", str(files["filament"]),
            "--slice", "0",
            "--export-3mf", str(output_path),
            str(model_path),
        ]
        try:
            # stdin and the output pipes are detached so the child can never touch the
            # MCP server's stdio channel.
            completed = subprocess.run(
                args, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            report["error_string"] = "timeout"
            return report
        except OSError as exc:
            report["error_string"] = f"cannot start Bambu Studio: {exc}"
            return report
        result = _read_result(cwd / "result.json")

    exit_code = completed.returncode
    report["exit_code"] = exit_code
    report["result"] = result
    reported = (result or {}).get("error_string") or ""

    problem = None
    if exit_code != 0 or result is None or result.get("return_code", 0) != 0:
        if reported and reported != "Success.":
            problem = reported
        elif result is None:
            problem = f"Bambu Studio exited with code {_code_text(exit_code)} and wrote no result.json"
        else:
            problem = f"Bambu Studio exited with code {_code_text(exit_code)}"

    if output_path.is_file():
        try:
            summary = inspect_sliced(output_path, density=density, thumbnail_to=thumbnail_path)
        except NotSliced as exc:
            problem = problem or str(exc)
        else:
            report["summary"] = summary
            expected = {
                "printer_settings_id": machine,
                "print_settings_id": process,
                "filament_settings_id": filament,
                "curr_bed_type": bed_type,
            }
            report["mismatches"] = [
                {"key": key, "expected": expected[key], "actual": summary["settings"].get(key)}
                for key in CHECKED_KEYS
                if summary["settings"].get(key) != expected[key]
            ]
            if report["mismatches"] and problem is None:
                keys = ", ".join(item["key"] for item in report["mismatches"])
                problem = f"the sliced file does not carry the requested settings: {keys}"
    elif problem is None:
        problem = f"Bambu Studio reported success but wrote no file at {output_path}"

    report["ok"] = problem is None
    report["error_string"] = problem or reported
    return report
