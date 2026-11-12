"""Bambu Studio system profiles: reading one with its `inherits` chain, and listing a printer's."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .paths import profiles_dir

KINDS = ("machine", "process", "filament")

# Characters that would let a name leave its folder, or split `--load-settings` (";").
_BAD_NAME_CHARS = frozenset('/\\;:\0')

# "<anything> @BBL <printer>" with an optional " <X> nozzle" tail.
_BBL_NAME = re.compile(r"^.+ @BBL (?P<printer>\S+?)(?: (?P<nozzle>\d+(?:\.\d+)?) nozzle)?$")
_DEFAULT_NOZZLE = "0.4"

_MACHINE_KEYS = ("nozzle_diameter", "printable_height", "default_bed_type")
_PROCESS_KEYS = ("description", "layer_height", "wall_loops", "sparse_infill_density")
_FILAMENT_KEYS = (
    "filament_type",
    "nozzle_temperature",
    "nozzle_temperature_range_low",
    "nozzle_temperature_range_high",
    "textured_plate_temp",
    "filament_density",
    "filament_max_volumetric_speed",
)
_WHOLE_LIST_KEYS = frozenset({"filament_max_volumetric_speed"})


class ProfileNotFound(LookupError):
    """No profile file with that kind and name."""


def _check_kind(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"profile kind must be one of {', '.join(KINDS)}, got {kind!r}")


def _check_name(name: str) -> None:
    if not isinstance(name, str) or not name.strip() or name in (".", ".."):
        raise ValueError(f"invalid profile name {name!r}")
    bad = sorted(set(name) & _BAD_NAME_CHARS)
    if bad:
        raise ValueError(f"profile name {name!r} contains forbidden characters {bad}")


def profile_path(kind: str, name: str, root: Path | None = None) -> Path:
    """`<root>/<kind>/<name>.json`, with `root` defaulting to the installed BBL profiles."""
    _check_kind(kind)
    _check_name(name)
    base = Path(root) if root is not None else profiles_dir()
    return base / kind / f"{name}.json"


def _read_json(path: Path, kind: str, name: str, cache: dict[Path, dict] | None) -> dict:
    if cache is not None and path in cache:
        return cache[path]
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise ProfileNotFound(f"no {kind} profile named {name!r} at {path}") from None
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not hold a JSON object")
    if cache is not None:
        cache[path] = data
    return data


def _load(kind: str, name: str, root: Path | None, cache: dict[Path, dict] | None) -> dict:
    _check_kind(kind)
    _check_name(name)
    chain: list[dict] = []
    seen: list[str] = []
    current: str | None = name
    while current:
        if current in seen:
            raise ValueError(f"inherits cycle in {kind} profiles: {' -> '.join(seen + [current])}")
        seen.append(current)
        data = _read_json(profile_path(kind, current, root), kind, current, cache)
        chain.append(data)
        current = data.get("inherits") or None
    merged: dict = {}
    for data in reversed(chain):
        merged.update(data)
    return merged


def load_profile(kind: str, name: str, root: Path | None = None) -> dict:
    """Load a profile with its `inherits` chain resolved; child keys override parent keys."""
    return _load(kind, name, root, None)


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _summary(name: str, profile: dict, keys: tuple[str, ...]) -> dict:
    summary = {"name": name}
    for key in keys:
        value = profile.get(key)
        summary[key] = value if key in _WHOLE_LIST_KEYS else _first(value)
    return summary


def _fits(name: str, printer: str, nozzle: str) -> bool:
    match = _BBL_NAME.match(name)
    if not match or match.group("printer") != printer:
        return False
    return (match.group("nozzle") or _DEFAULT_NOZZLE) == nozzle


def _usable_name(name: str) -> bool:
    try:
        _check_name(name)
    except ValueError:
        return False
    return True


def _listable(profile_file: Path, cache: dict[Path, dict]) -> bool:
    """Instantiable, and named like its file, so slice_model can load it by that name."""
    try:
        data = _read_json(profile_file, "", profile_file.stem, cache)
    except (ValueError, ProfileNotFound):
        return False
    return data.get("instantiation") == "true" and data.get("name", profile_file.stem) == profile_file.stem


def list_profiles(
    printer: str = "P2S",
    nozzle: str = "0.4",
    filament_contains: str | None = None,
    root: Path | None = None,
) -> dict:
    """Instantiable machine, process and filament profiles for one printer and nozzle.

    Machines match `Bambu Lab <printer> <nozzle> nozzle`. Processes and filaments match
    `@BBL <printer>` in the name; a `<X> nozzle` tail must equal `nozzle`, and a name
    without the tail is the 0.4 nozzle profile.
    """
    base = Path(root) if root is not None else profiles_dir()
    if not base.is_dir():
        raise ProfileNotFound(f"no profile folder at {base}")
    cache: dict[Path, dict] = {}
    machine_name = f"Bambu Lab {printer} {nozzle} nozzle"
    needle = filament_contains.casefold() if filament_contains else None

    def collect(kind: str, keys: tuple[str, ...], wanted) -> list[dict]:
        folder = base / kind
        if not folder.is_dir():
            return []
        entries = []
        for profile_file in sorted(folder.glob("*.json")):
            name = profile_file.stem
            if not wanted(name) or not _usable_name(name) or not _listable(profile_file, cache):
                continue
            try:
                profile = _load(kind, name, base, cache)
            except (ValueError, LookupError):
                # e.g. a parent named "Bambu Support For PA/PET @base" has no file of that name.
                continue
            entries.append(_summary(name, profile, keys))
        return entries

    return {
        "machines": collect("machine", _MACHINE_KEYS, lambda name: name == machine_name),
        "processes": collect("process", _PROCESS_KEYS, lambda name: _fits(name, printer, nozzle)),
        "filaments": collect(
            "filament",
            _FILAMENT_KEYS,
            lambda name: _fits(name, printer, nozzle) and (needle is None or needle in name.casefold()),
        ),
    }
