"""Slicing a model with the Bambu Studio command line.

The CLI prints nothing. The outcome is its exit code, a `result.json` it writes into its
current folder, and the `.gcode.3mf` it exports. It crashes (0xC0000005) when it gets no
machine, process and filament profiles, so all three are always passed.

The CLI applies only the keys in the files it is given and ignores `inherits` and
`include`; everything else falls back to built-in defaults (generic start G-code, filament
density 0). So each profile is flattened into one self-contained file first. The G-code
takes the settings ids from each file's `name`, so the requested names survive.

The CLI exports to a partial file beside the output, on the same volume. Only a run that
passes every check is renamed onto the output, so a failed or half-written slice never
appears there.
"""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from .inspect3mf import NotSliced, inspect_sliced
from .paths import resolve_allowed, studio_exe
from .profiles import flatten_profile, raw_profile

DEFAULT_MACHINE = "Bambu Lab P2S 0.4 nozzle"
DEFAULT_PROCESS = "0.20mm Standard @BBL P2S"
DEFAULT_FILAMENT = "Bambu PLA Lite @BBL P2S 0.4 nozzle"
DEFAULT_BED_TYPE = "Textured PEI Plate"

MODEL_SUFFIXES = (".stl", ".3mf", ".step", ".stp", ".obj")
OUTPUT_SUFFIX = ".gcode.3mf"
THUMBNAIL_SUFFIX = ".plate.png"

# Settings the sliced G-code must carry exactly as requested.
CHECKED_KEYS = ("printer_settings_id", "print_settings_id", "filament_settings_id", "curr_bed_type")

# Override keys that are never allowed: profile identity, anything that runs or emits
# G-code or names files, temperatures, compatibility and extruder selection.
_DENIED_OVERRIDES = (
    "type", "name", "inherits", "include", "from", "setting_id", "instantiation",
    "post_process", "*gcode*", "*temperature*", "filename_format", "compatible_*",
    "print_extruder_*",
)

_CLI_OUTPUT_LIMIT = 2000


def _first_float(value) -> float | None:
    if isinstance(value, list):
        value = value[0] if value else None
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _require_instantiable(kind: str, name: str) -> None:
    """Base and template profiles (`instantiation` other than "true") cannot be sliced with."""
    if raw_profile(kind, name).get("instantiation") != "true":
        raise ValueError(
            f"{kind} profile {name!r} is not instantiable (a base or template profile); "
            "pick one from list_print_profiles"
        )


def _require_compatible(kind: str, name: str, profile: dict, machine: str) -> None:
    compatible = profile.get("compatible_printers")
    if not isinstance(compatible, list) or machine not in compatible:
        raise ValueError(
            f"{kind} profile {name!r} is not compatible with {machine!r} "
            f"(compatible_printers: {compatible!r})"
        )


def _apply_overrides(profile: dict, process: str, overrides: dict[str, str]) -> None:
    """Set `overrides` on the flattened process profile, in place.

    A key must exist in the profile and must not match the denylist. A list value is
    replaced by a list of the same length filled with the new value.
    """
    for key, value in overrides.items():
        if any(fnmatch.fnmatchcase(key, pattern) for pattern in _DENIED_OVERRIDES):
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


def _cli_output(stdout, stderr) -> str:
    """The last characters of each stream the CLI wrote, decoded leniently."""
    parts = []
    for label, data in (("stderr", stderr), ("stdout", stdout)):
        if not data:
            continue
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        parts.append(f"[{label}]\n{text[-_CLI_OUTPUT_LIMIT:]}")
    return "\n".join(parts)


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
    `mismatches` (requested settings the G-code does not carry), `summary` (`inspect_sliced`
    of the output, with a `<name>.plate.png` thumbnail) and `cli_output` (the tail of the
    CLI's stderr and stdout when `ok` is false). When `ok` is false there is no file at
    `output`, and `summary`, if present, describes the discarded slice with `path` None.
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

    for kind, profile_name in (("machine", machine), ("process", process), ("filament", filament)):
        _require_instantiable(kind, profile_name)
    profiles = {
        "machine": flatten_profile("machine", machine),
        "process": flatten_profile("process", process),
        "filament": flatten_profile("filament", filament),
    }
    _require_compatible("process", process, profiles["process"], machine)
    _require_compatible("filament", filament, profiles["filament"], machine)
    if overrides:
        _apply_overrides(profiles["process"], process, overrides)
    density = _first_float(profiles["filament"].get("filament_density"))

    stem = name[: -len(OUTPUT_SUFFIX)]
    thumbnail_path = output_path.with_name(stem + THUMBNAIL_SUFFIX)
    partial_path = output_path.with_name(f".{stem}.{uuid.uuid4().hex[:8]}.partial{OUTPUT_SUFFIX}")
    # A stale slice or thumbnail must never pass for the new one.
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
        "cli_output": None,
    }
    problems: list[str] = []
    cli_output = ""
    reported = ""
    summary = None
    published = False
    try:
        with tempfile.TemporaryDirectory(prefix="print-mcp-", ignore_cleanup_errors=True) as tmp:
            work = Path(tmp)
            if ";" in str(work):
                raise ValueError(f"temporary folder {work} contains ';', which splits --load-settings")
            files = {}
            (work / "profiles").mkdir()
            for kind, data in profiles.items():
                # Fixed file names: the G-code takes the settings ids from `name`, not the file.
                files[kind] = work / "profiles" / f"{kind}.json"
                files[kind].write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
            cwd = work / "cwd"
            cwd.mkdir()
            args = [
                str(studio_exe()),
                "--debug", "3",
                "--curr-bed-type", bed_type,
                "--load-settings", f"{files['machine']};{files['process']}",
                "--load-filaments", str(files["filament"]),
                "--slice", "0",
                "--export-3mf", str(partial_path),
                str(model_path),
            ]
            completed = None
            try:
                # stdin and the output pipes are detached so the child can never touch the
                # MCP server's stdio channel.
                completed = subprocess.run(
                    args, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout
                )
            except subprocess.TimeoutExpired as exc:
                problems.append("timeout")
                cli_output = _cli_output(exc.stdout, exc.stderr)
            except OSError as exc:
                problems.append(f"cannot start Bambu Studio: {exc}")
            else:
                cli_output = _cli_output(completed.stdout, completed.stderr)
                report["result"] = _read_result(cwd / "result.json")

        if completed is not None:
            exit_code = completed.returncode
            result = report["result"]
            report["exit_code"] = exit_code
            reported = (result or {}).get("error_string") or ""
            if exit_code != 0 or result is None or result.get("return_code", 0) != 0:
                if reported and reported != "Success.":
                    problems.append(reported)
                elif result is None:
                    problems.append(
                        f"Bambu Studio exited with code {_code_text(exit_code)} and wrote no result.json"
                    )
                else:
                    problems.append(f"Bambu Studio exited with code {_code_text(exit_code)}")

            if partial_path.is_file():
                try:
                    summary = inspect_sliced(partial_path, density=density)
                except NotSliced as exc:
                    problems.append(str(exc))
                else:
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
                    if report["mismatches"]:
                        keys = ", ".join(item["key"] for item in report["mismatches"])
                        problems.append(f"the sliced file does not carry the requested settings: {keys}")
                    if summary["plates"] != 1:
                        problems.append(
                            f"the slice has {summary['plates']} plates; only one plate is supported"
                        )
            elif not problems:
                problems.append("Bambu Studio reported success but wrote no sliced file")

            if not problems:
                try:
                    os.replace(partial_path, output_path)
                except OSError as exc:
                    problems.append(f"cannot move the slice to {output_path}: {exc}")
                else:
                    published = True
                    summary = inspect_sliced(output_path, density=density, thumbnail_to=thumbnail_path)
    finally:
        partial_path.unlink(missing_ok=True)

    if summary is not None and not published:
        summary["path"] = None  # the slice was discarded
    report["summary"] = summary
    report["ok"] = not problems
    report["error_string"] = "; ".join(problems) if problems else reported
    report["cli_output"] = None if report["ok"] else cli_output
    return report
