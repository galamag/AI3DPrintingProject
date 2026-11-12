"""MCP server `print`: Bambu Studio profiles, slicing, sliced-file inspection and its window.

Run with `uv run --frozen python -m print_mcp.server` (stdio transport).
"""
import asyncio
import json

from mcp.server.fastmcp import FastMCP, Image

from . import inspect3mf, profiles, slicer, studio

INSTRUCTIONS = """\
Prepares prints for the user's Bambu Lab P2S through Bambu Studio.

Workflow: list_print_profiles to pick the machine, process and filament names, slice_model
to slice a model into a .gcode.3mf, then show the user the plate thumbnail, the time and the
filament weight. inspect_sliced reads an existing .gcode.3mf.

The Bambu Studio window is driven in the background, without taking focus or moving the
mouse: studio_windows lists its windows, studio_capture shows one, studio_click clicks a
point found on a fresh capture, studio_open shows a file in it. Button positions are never
fixed; read them from a capture each time. Clicks that start, stop or cancel a print need the
user's explicit consent for that print.

Model and output paths must lie inside the repository, Documents/BlenderMCP or the folder in
PRINT_MCP_WORK_DIR.
"""

mcp = FastMCP("print", instructions=INSTRUCTIONS)

# Errors caused by the request or the current state, returned as text rather than raised.
_USER_ERRORS = (ValueError, LookupError, FileNotFoundError, studio.StudioError)


async def _run(func, *args, **kwargs) -> str:
    """Run blocking work off the event loop; reply with JSON, or with text for bad input."""
    try:
        value = await asyncio.to_thread(func, *args, **kwargs)
    except _USER_ERRORS as exc:
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

    `model` is an .stl, .3mf, .step, .stp or .obj file; `output` must end with .gcode.3mf.
    Both must lie inside the repository, Documents/BlenderMCP or PRINT_MCP_WORK_DIR. Any
    old `output` and its thumbnail are deleted first; the new slice is written there only
    when every check passes, so a failed slice leaves no file at `output`. The plate
    picture is saved next to it as `<name>.plate.png`. Only one plate is supported.

    Profile names come from list_print_profiles. The process and filament must list the
    machine in their compatible_printers; base and template profiles are refused.

    `overrides` changes process settings for this slice only, e.g.
    {"sparse_infill_density": "30%"}. Every key must exist in the process profile.
    G-code, post-processing, file-name, temperature, compatibility and extruder-variant
    keys cannot be overridden.

    Returns JSON: `ok`, `exit_code`, `error_string`, `output`, `result` (the CLI's
    result.json), `mismatches` (requested profile or bed settings the G-code does not
    carry), `summary` (plates, time, layers, filament length and weight, key settings,
    thumbnail path) and `cli_output` (tail of the CLI's stderr and stdout when `ok` is
    false). This only slices; nothing is sent to the printer.
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
    type, layer height, temperatures, filament density, infill, walls, top shell layers,
    supports). When the G-code reports 0 g, pass `density` in g/cm3 (from
    list_print_profiles) to compute the weight.
    `thumbnail_to` is a .png path that receives the plate picture. Paths must lie inside
    the repository, Documents/BlenderMCP or PRINT_MCP_WORK_DIR.
    """
    return await _run(
        inspect3mf.inspect_sliced, path, density=density, thumbnail_to=thumbnail_to
    )


def _list_windows() -> list[dict]:
    return [window.as_dict() for window in studio.list_windows()]


@mcp.tool()
async def studio_windows() -> str:
    """List the open Bambu Studio windows: hwnd, title, position, size and whether minimized.

    The main window's title is "<project> - BambuStudio". Dialogs such as the print-send
    window are separate windows and appear here too. Pass an hwnd to the other studio_*
    tools when more than one window is open.
    """
    return await _run(_list_windows)


@mcp.tool(structured_output=False)
async def studio_capture(
    hwnd: int | None = None,
    title_contains: str | None = None,
    scale: float = 0.5,
    crop: list[int] | None = None,
):
    """Capture a Bambu Studio window as a PNG, even when other windows cover it.

    Does not focus or move the window. `crop` is [left, top, right, bottom] in window
    pixels and is applied before `scale` (0.1 to 1.0). The scale is lowered when needed so
    the image stays within 1568 px and 1.15 MP; crop a region to read small text at full
    size. Returns the image and JSON with the window (including its width and height),
    `scale_x` and `scale_y` actually used, `to_window_px` (the formula from an image pixel
    to the window pixel studio_click expects), `click_hint` (pass the window's width and
    height to studio_click as expected_width and expected_height) and `warnings`, for
    example when the window is disabled because a dialog is open. A minimized window
    cannot be captured.
    """
    try:
        data, info = await asyncio.to_thread(
            studio.capture_window,
            hwnd=hwnd,
            title_contains=title_contains,
            scale=scale,
            crop=tuple(crop) if crop is not None else None,
        )
    except _USER_ERRORS as exc:
        return f"Error: {exc}"
    return [Image(data=data, format="png"), json.dumps(info, ensure_ascii=False, indent=2)]


@mcp.tool()
async def studio_click(
    x: int,
    y: int,
    hwnd: int | None = None,
    title_contains: str | None = None,
    expected_width: int | None = None,
    expected_height: int | None = None,
) -> str:
    """Left-click a point in a Bambu Studio window without focusing it or moving the mouse.

    Always call studio_capture first and take the point from that capture: (x, y) are
    window pixels, so convert image pixels with its `to_window_px`, and pass the captured
    window's width and height as `expected_width` and `expected_height`; the click is
    refused if the window size changed since. Never reuse old coordinates; button positions
    depend on the window size and the Bambu Studio version.

    Never click the window's close, minimize or maximize buttons. Buttons that start, stop,
    pause, resume or cancel a print, including "Print plate" and "Send" in whatever language
    the UI uses, may be clicked only after the user's explicit consent to that particular
    print. A window blocked by a dialog is refused: list the windows and click the dialog by
    its hwnd. Capture again afterwards to check the effect. Returns the window and its size,
    the control that got the click (`class_trail`) and whether the foreground window changed
    (`foreground_changed`).
    """
    return await _run(
        studio.click_window,
        x,
        y,
        hwnd=hwnd,
        title_contains=title_contains,
        expected_width=expected_width,
        expected_height=expected_height,
    )


@mcp.tool()
async def studio_open(path: str, timeout: float = 60.0) -> str:
    """Show a .3mf, .gcode.3mf, .stl, .step, .stp or .obj file in Bambu Studio.

    If a Bambu Studio window is already titled with the file's project name, it is returned
    and nothing is launched (`launched: false`). Matching is by file name only: a window for
    a file with the same name in another folder counts as this file's. Otherwise Bambu
    Studio starts with the file, asked not to take focus, and the call waits up to `timeout`
    seconds for its window; while that launch is still starting, it is not repeated.
    The path must lie inside the repository, Documents/BlenderMCP or PRINT_MCP_WORK_DIR.
    Opening a sliced file does not keep its slice: the window slices again.
    """
    return await _run(studio.open_in_studio, path, timeout=timeout)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
