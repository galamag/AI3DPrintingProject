"""Bambu Studio system profiles: name lookup, `inherits` and `include` resolution, listing.

Names map to files through the vendor index next to the profile folder
(`resources/profiles/BBL.json`, entries with `name` and `sub_path`). Without an index a
name maps to `<root>/<kind>/<name>.json`.

A profile resolves as its parent chain (`inherits`), then its `include` templates in the
listed order, then its own keys. That order puts the P2S start, end and filament-change
G-code from the `... template ...` machine files over the generic G-code of
`fdm_bbl_3dp_001_common`; with parents over templates a slice gets no P2S start G-code.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from .paths import profiles_dir

KINDS = ("machine", "process", "filament")

# Never allowed in a name: ";" splits `--load-settings`, ":" names a drive or a stream,
# "\\" separates Windows paths, NUL ends a C string. "/" is allowed only in names the vendor
# index lists, such as "Bambu Support For PA/PET @base".
_FORBIDDEN_CHARS = frozenset({";", ":", "\\", "\0"})

# Keys an `include` template never passes on to the profile that includes it.
_IDENTITY_KEYS = frozenset({"type", "name", "inherits", "include", "from", "setting_id", "instantiation"})
# Keys a flattened profile drops: it has no parent and nothing left to include.
_LINK_KEYS = ("inherits", "include")

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
    """No profile with that kind and name."""


def _check_kind(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"profile kind must be one of {', '.join(KINDS)}, got {kind!r}")


def _check_name(name: str, indexed: bool) -> None:
    if not isinstance(name, str) or not name.strip() or ".." in name or name == ".":
        raise ValueError(f"invalid profile name {name!r}")
    bad = sorted(set(name) & _FORBIDDEN_CHARS)
    if bad:
        raise ValueError(f"profile name {name!r} contains forbidden characters {bad}")
    if "/" in name and not indexed:
        raise ValueError(f"profile name {name!r} contains '/' and is not in the vendor index")


def _read_index(base: Path) -> dict[str, dict[str, Path]] | None:
    """`<base>.json` (e.g. profiles/BBL.json) as {kind: {name: file}}, or None without one."""
    index_file = base.parent / f"{base.name}.json"
    if not index_file.is_file():
        return None
    try:
        data = json.loads(index_file.read_text(encoding="utf-8-sig"))
    except ValueError:
        raise ValueError(f"unreadable vendor index {index_file}") from None
    if not isinstance(data, dict):
        raise ValueError(f"vendor index {index_file} does not hold a JSON object")
    index: dict[str, dict[str, Path]] = {}
    for kind in KINDS:
        entries: dict[str, Path] = {}
        for item in data.get(f"{kind}_list") or []:
            if not isinstance(item, dict):
                continue
            name, sub_path = item.get("name"), item.get("sub_path")
            if not isinstance(name, str) or not isinstance(sub_path, str):
                continue
            parts = PurePosixPath(sub_path.replace("\\", "/")).parts
            # Only files inside <base>/<kind>/: no absolute paths, no "..", and no ":" in any
            # part, since joining "D:" onto a Windows path jumps to another drive.
            if (
                len(parts) < 2
                or parts[0] != kind
                or ".." in parts
                or any(":" in part for part in parts)
                or not sub_path.endswith(".json")
            ):
                continue
            entries[name] = base.joinpath(*parts)
        index[kind] = entries
    return index


def _as_list(value) -> list:
    if value is None or value == "":
        return []
    return [value] if isinstance(value, str) else list(value)


class _Library:
    """One profile folder with its optional vendor index, and caches for one call."""

    def __init__(self, root: Path | None = None) -> None:
        self.base = Path(root) if root is not None else profiles_dir()
        self.index = _read_index(self.base)
        self._files: dict[Path, dict] = {}
        self._resolved: dict[tuple[str, str], dict] = {}
        self._checked: set[Path] = set()

    def path(self, kind: str, name: str) -> Path:
        _check_kind(kind)
        indexed = self.index is not None and isinstance(name, str) and name in self.index[kind]
        _check_name(name, indexed)
        path = self.index[kind][name] if indexed else self.base / kind / f"{name}.json"
        if path not in self._checked:
            # Following links, the file must still sit inside <base>/<kind>/.
            if not path.resolve().is_relative_to((self.base / kind).resolve()):
                raise ValueError(f"{kind} profile {name!r} resolves outside {self.base / kind}")
            self._checked.add(path)
        return path

    def names(self, kind: str) -> list[str]:
        if self.index is not None:
            return sorted(self.index[kind])
        folder = self.base / kind
        return sorted(path.stem for path in folder.glob("*.json")) if folder.is_dir() else []

    def read(self, kind: str, name: str) -> dict:
        path = self.path(kind, name)
        if path not in self._files:
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except FileNotFoundError:
                raise ProfileNotFound(f"no {kind} profile named {name!r} at {path}") from None
            if not isinstance(data, dict):
                raise ValueError(f"{path} does not hold a JSON object")
            self._files[path] = data
        return self._files[path]

    def resolve(self, kind: str, name: str, stack: tuple[str, ...] = ()) -> dict:
        cached = self._resolved.get((kind, name))
        if cached is not None:
            return dict(cached)
        if name in stack:
            raise ValueError(f"cycle in {kind} profiles: {' -> '.join(stack + (name,))}")
        stack = stack + (name,)
        data = self.read(kind, name)
        parent = data.get("inherits")
        merged = self.resolve(kind, parent, stack) if parent else {}
        for template in _as_list(data.get("include")):
            merged.update(self._template(kind, template, stack))
        merged.update(data)
        self._resolved[(kind, name)] = merged
        return dict(merged)

    def _template(self, kind: str, name: str, stack: tuple[str, ...]) -> dict:
        if name in stack:
            raise ValueError(f"cycle in {kind} profiles: {' -> '.join(stack + (name,))}")
        data = self.read(kind, name)
        if data.get("inherits") or data.get("include"):
            # No shipped template does this; refuse rather than guess the merge order.
            raise ValueError(f"{kind} template {name!r} has its own inherits or include")
        return {key: value for key, value in data.items() if key not in _IDENTITY_KEYS}


def profile_path(kind: str, name: str, root: Path | None = None) -> Path:
    """The file for a profile name: from the vendor index, else `<root>/<kind>/<name>.json`.

    `root` defaults to the installed BBL profiles.
    """
    return _Library(root).path(kind, name)


def raw_profile(kind: str, name: str, root: Path | None = None) -> dict:
    """A copy of the profile file's own JSON, with nothing inherited or included."""
    return dict(_Library(root).read(kind, name))


def load_profile(kind: str, name: str, root: Path | None = None) -> dict:
    """A profile with `inherits` and `include` resolved: parents, then templates, then own keys."""
    return _Library(root).resolve(kind, name)


def flatten_profile(kind: str, name: str, root: Path | None = None) -> dict:
    """The resolved profile as one self-contained object, without `inherits` and `include`.

    The Bambu Studio CLI reads only the file it is given, so it must get this form.
    """
    profile = load_profile(kind, name, root)
    for key in _LINK_KEYS:
        profile.pop(key, None)
    return profile


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


def list_profiles(
    printer: str = "P2S",
    nozzle: str = "0.4",
    filament_contains: str | None = None,
    root: Path | None = None,
) -> dict:
    """Instantiable machine, process and filament profiles for one printer and nozzle.

    Machines match `Bambu Lab <printer> <nozzle> nozzle`. Processes and filaments match
    `@BBL <printer>` in the name; a `<X> nozzle` tail must equal `nozzle`, and a name
    without the tail is the 0.4 nozzle profile. Profiles that cannot be loaded by their
    name are left out, since slice_model could not use them.
    """
    library = _Library(root)
    if not library.base.is_dir():
        raise ProfileNotFound(f"no profile folder at {library.base}")
    machine_name = f"Bambu Lab {printer} {nozzle} nozzle"
    needle = filament_contains.casefold() if filament_contains else None

    def collect(kind: str, keys: tuple[str, ...], wanted) -> list[dict]:
        entries = []
        for name in library.names(kind):
            if not wanted(name):
                continue
            try:
                data = library.read(kind, name)
                if data.get("instantiation") != "true" or data.get("name", name) != name:
                    continue
                profile = library.resolve(kind, name)
            except (ValueError, LookupError):
                # e.g. without an index, a parent named "Bambu Support For PA/PET @base".
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
