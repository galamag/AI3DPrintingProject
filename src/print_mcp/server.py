"""MCP server `print`: Bambu Studio profiles, slicing and sliced-file inspection.

Run with `uv run --frozen python -m print_mcp.server` (stdio transport).
"""
import asyncio
import json

from mcp.server.fastmcp import FastMCP

from . import inspect3mf, profiles, slicer

INSTRUCTIONS = """\
Prepares prints for the user's Bambu Lab P2S through the Bambu Studio command line.

Workflow: list_print_profiles to pick the machine, process and filament names, slice_model
to slice a model into a .gcode.3mf, then show the user the plate thumbnail, the time and the
filament weight. inspect_sliced reads an existing .gcode.3mf.

Model and output paths must lie inside the repository, Documents/BlenderMCP or the folder in
PRINT_MCP_WORK_DIR. These tools only slice and read files; they never start a print.
"""

mcp = FastMCP("print", instructions=INSTRUCTIONS)


async def _run(func, *args, **kwargs) -> str:
    """Run blocking work off the event loop; reply with JSON, or with text for bad input."""
    try:
        value = await asyncio.to_thread(func, *args, **kwargs)
    except (ValueError, LookupError) as exc:
        return f"Error: {exc}"
    return json.dumps(value, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_print_profiles(
    printer: str = "P2S",
    nozzle: str = "0.4",
    filament_contains: str | None = None,
) -> str:
    """List Bambu Studio's bundled profiles for one printer and nozzle size.

    Returns JSON with `machines` (nozzle diameter, printable height), `processes` (layer
    height, wall loops, sparse infill density) and `filaments` (type, nozzle temperature and
    its range, textured plate temperature, density in g/cm3, max volumetric speed). The
    names are the ones slice_model accepts. `filament_contains` filters filament names,
    ignoring case, e.g. "PLA Lite".
    """
    return await _run(
        profiles.list_profiles, printer=printer, nozzle=nozzle, filament_contains=filament_contains
    )


@mcp.tool()
async def slice_model(
    model: str,
    output: str,
    machine: str = slicer.DEFAULT_MACHINE,
    process: str = slicer.DEFAULT_PROCESS,
    filament: str = slicer.DEFAULT_FILAMENT,
    bed_type: str = slicer.DEFAULT_BED_TYPE,
    overrides: dict[str, str] | None = None,
    timeout: int = 600,
) -> str:
    """Slice a model with the Bambu Studio command line and inspect the result.

    `model` is an .stl, .3mf, .step, .stp or .obj file; `output` must end with .gcode.3mf
    and is replaced if it exists. Both must lie inside the repository,
    Documents/BlenderMCP or PRINT_MCP_WORK_DIR. The plate picture is saved next to the
    output as `<name>.png`. Profile names come from list_print_profiles.

    `overrides` changes process settings for this slice only, e.g.
    {"sparse_infill_density": "30%"}; every key must exist in the process profile.

    Returns JSON: `ok`, `exit_code`, `error_string`, `output`, `result` (the CLI's
    result.json), `mismatches` (requested profile or bed settings the G-code does not
    carry) and `summary` (time, layers, filament length and weight, key settings, thumbnail
    path). This only slices; nothing is sent to the printer.
    """
    return await _run(
        slicer.slice_model,
        model,
        output,
        machine=machine,
        process=process,
        filament=filament,
        bed_type=bed_type,
        overrides=overrides,
        timeout=timeout,
    )


@mcp.tool()
async def inspect_sliced(
    path: str,
    density: float | None = None,
    thumbnail_to: str | None = None,
) -> str:
    """Read a sliced .gcode.3mf archive.

    Returns JSON with the predicted time (`time_s`, `time_text`), `layers`,
    `filament_length_mm`, `filament_weight_g` with its `weight_source`, `max_z_mm`, and
    `settings` recorded in the G-code (printer, process and filament profile names, bed
    type, layer height, temperatures, infill, walls, supports). Command-line slices report
    0 g, so pass `density` in g/cm3 (from list_print_profiles) to compute the weight.
    `thumbnail_to` is a .png path that receives the plate picture. Paths must lie inside
    the repository, Documents/BlenderMCP or PRINT_MCP_WORK_DIR.
    """
    return await _run(
        inspect3mf.inspect_sliced, path, density=density, thumbnail_to=thumbnail_to
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
