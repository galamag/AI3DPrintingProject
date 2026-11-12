"""Reading a sliced Bambu Studio `.gcode.3mf` archive: time, layers, filament, settings, thumbnail."""
from __future__ import annotations

import io
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .paths import resolve_allowed

# Keys copied from the G-code config block into the `settings` result.
SETTINGS_KEYS = (
    "printer_model",
    "printer_settings_id",
    "print_settings_id",
    "filament_settings_id",
    "curr_bed_type",
    "layer_height",
    "nozzle_diameter",
    "nozzle_volume_type",
    "nozzle_temperature",
    "textured_plate_temp",
    "filament_type",
    "filament_colour",
    "filament_density",
    "sparse_infill_density",
    "wall_loops",
    "top_shell_layers",
    "enable_support",
)

_PLATE_GCODE = re.compile(r"^Metadata/plate_(\d+)\.gcode$")
_CONFIG_LINE = re.compile(r"^; (\w+) =(?: (.*))?$")
_DURATION_PART = re.compile(r"(\d+)\s*([dhms])")
_DURATION_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
# The header and config block sit at the top of the G-code; stop reading if they never end.
_MAX_PREAMBLE_LINES = 20000


class NotSliced(ValueError):
    """The file is missing, is not a zip archive, or holds no plate G-code."""


def _numbers(value: str | None) -> list[float]:
    numbers = []
    for part in (value or "").split(","):
        try:
            numbers.append(float(part))
        except ValueError:
            pass
    return numbers


def _sum_or_none(value: str | None) -> float | None:
    numbers = _numbers(value)
    return round(sum(numbers), 2) if numbers else None


def _first_or_none(value: str | None) -> float | None:
    numbers = _numbers(value)
    return numbers[0] if numbers else None


def _duration_seconds(text: str | None) -> int | None:
    parts = _DURATION_PART.findall(text or "")
    if not parts:
        return None
    return sum(int(amount) * _DURATION_SECONDS[unit] for amount, unit in parts)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"' and '";"' not in value:
        return value[1:-1]
    return value


def _parse_header_line(line: str, header: dict[str, str]) -> None:
    # "; model printing time: 10m 26s; total estimated time: 10m 27s" holds two pairs.
    body = line[2:] if line.startswith("; ") else line.lstrip("; ")
    for part in body.split("; "):
        key, sep, value = part.partition(":")
        if sep:
            header.setdefault(key.strip(), value.strip())


def _read_preamble(archive: zipfile.ZipFile, entry: str) -> tuple[dict[str, str], dict[str, str]]:
    """Stream the G-code up to CONFIG_BLOCK_END; the toolpath body is never read."""
    header: dict[str, str] = {}
    config: dict[str, str] = {}
    section = None
    with archive.open(entry) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
        for count, line in enumerate(text):
            if count >= _MAX_PREAMBLE_LINES:
                break
            line = line.rstrip("\r\n")
            if line == "; HEADER_BLOCK_START":
                section = "header"
            elif line == "; HEADER_BLOCK_END":
                section = None
            elif line == "; CONFIG_BLOCK_START":
                section = "config"
            elif line == "; CONFIG_BLOCK_END":
                break
            elif section == "header":
                _parse_header_line(line, header)
            elif section == "config":
                match = _CONFIG_LINE.match(line)
                if match:
                    config[match.group(1)] = match.group(2) or ""
    return header, config


def _prediction_seconds(archive: zipfile.ZipFile, plate: int) -> int | None:
    """Predicted print time from Metadata/slice_info.config, in seconds."""
    try:
        root = ET.fromstring(archive.read("Metadata/slice_info.config"))
    except (KeyError, ET.ParseError):
        return None
    for element in root.iter("plate"):
        metadata = {item.get("key"): item.get("value") for item in element.findall("metadata")}
        if metadata.get("index", str(plate)) != str(plate):
            continue
        try:
            return int(float(metadata.get("prediction") or ""))
        except ValueError:
            return None
    return None


def inspect_sliced(
    path: str | Path,
    density: float | None = None,
    thumbnail_to: str | Path | None = None,
) -> dict:
    """Summarise a sliced `.gcode.3mf`; `plates` counts its plate G-code files.

    Time, layers, filament and settings describe the first plate.

    `density` (g/cm3) is used to compute the filament weight when the G-code header
    reports 0 g, as a slice made with a filament profile of density 0 does.
    `thumbnail_to` is a `.png` path that receives the plate picture.
    """
    archive_path = resolve_allowed(path)
    thumbnail_path = None
    if thumbnail_to is not None:
        thumbnail_path = resolve_allowed(thumbnail_to)
        if thumbnail_path.suffix.lower() != ".png":
            raise ValueError(f"thumbnail path must end with .png: {thumbnail_path}")
    if not archive_path.is_file():
        raise NotSliced(f"no such file: {archive_path}")

    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile:
        raise NotSliced(f"not a 3MF archive: {archive_path}") from None

    with archive:
        plates = sorted(
            (int(match.group(1)), name)
            for name in archive.namelist()
            if (match := _PLATE_GCODE.match(name))
        )
        if not plates:
            raise NotSliced(f"no plate G-code inside {archive_path}; slice it first")
        plate, gcode_entry = plates[0]
        header, config = _read_preamble(archive, gcode_entry)
        prediction = _prediction_seconds(archive, plate)

        thumbnail = None
        png_entry = f"Metadata/plate_{plate}.png"
        if thumbnail_path is not None and png_entry in archive.namelist():
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            thumbnail_path.write_bytes(archive.read(png_entry))
            thumbnail = str(thumbnail_path)

    time_text = header.get("total estimated time")
    layers = _first_or_none(header.get("total layer number"))
    length_mm = _sum_or_none(header.get("total filament length [mm]"))
    header_weight = _sum_or_none(header.get("total filament weight [g]"))
    diameter = _first_or_none(header.get("filament_diameter")) or _first_or_none(
        config.get("filament_diameter")
    )

    weight, weight_source = None, None
    if header_weight:
        weight, weight_source = header_weight, "gcode"
    elif density and length_mm is not None and diameter:
        volume_cm3 = length_mm * math.pi * (diameter / 2) ** 2 / 1000
        weight, weight_source = round(volume_cm3 * density, 2), "computed"

    return {
        "path": str(archive_path),
        "plates": len(plates),
        "time_s": prediction if prediction is not None else _duration_seconds(time_text),
        "time_text": time_text,
        "layers": int(layers) if layers is not None else None,
        "filament_length_mm": length_mm,
        "filament_weight_g": weight,
        "weight_source": weight_source,
        "max_z_mm": _first_or_none(header.get("max_z_height")),
        "settings": {
            key: _unquote(config[key]) if key in config else None for key in SETTINGS_KEYS
        },
        "thumbnail": thumbnail,
    }
