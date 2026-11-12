"""export_for_print: Blender mesh objects as one millimetre STL, with mesh checks.

A fork addition, kept in its own module so upstream merges stay cheap: server.py only
imports this module and calls `register(mcp, _run_script)`.

The export runs as a script through the addon's execute_code (see blender_scripts). It
calls no operators and changes nothing in the scene: it reads each object's evaluated
mesh from the depsgraph (modifiers applied), bakes the world matrix in, converts scene
units to millimetres and writes a binary STL itself. The file path is checked here, on
the server, before Blender sees it.
"""
from __future__ import annotations

import json

from print_mcp.paths import resolve_allowed

MAX_TRIANGLES = 2_000_000

# Runs inside Blender and, in the tests, on its own. Pure Python: Blender's numpy is not
# available to the test environment, and 2,000,000 triangles take under 2 s this way.
STL_WRITER = r'''
import math as _math
import os as _os
import struct as _struct


def write_binary_stl(path, coords, header=b"binary STL in millimetres, written by export_for_print"):
    """Write triangles to `path` as binary STL and return how many were written.

    `coords` holds 9 floats per triangle: three vertices, counter-clockwise seen from
    outside. Each facet normal is computed from its vertices. The file is written beside
    `path` first and renamed over it, so a failed write leaves no partial STL.
    """
    count, extra = divmod(len(coords), 9)
    if extra:
        raise ValueError(f"{len(coords)} coordinates are not whole triangles")
    out = bytearray(84 + 50 * count)
    out[0:80] = bytes(header)[:80].ljust(80, b" ")
    _struct.pack_into("<I", out, 80, count)
    pack = _struct.Struct("<12fH").pack_into
    sqrt = _math.sqrt
    offset = 84
    for i in range(0, count * 9, 9):
        ax, ay, az, bx, by, bz, cx, cy, cz = coords[i:i + 9]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        length = sqrt(nx * nx + ny * ny + nz * nz)
        if length > 0.0:
            nx, ny, nz = nx / length, ny / length, nz / length
        else:
            nx = ny = nz = 0.0
        pack(out, offset, nx, ny, nz, ax, ay, az, bx, by, bz, cx, cy, cz, 0)
        offset += 50
    partial = path + ".partial"
    try:
        with open(partial, "wb") as handle:
            handle.write(out)
        _os.replace(partial, path)
    finally:
        if _os.path.exists(partial):
            _os.remove(partial)
    return count
'''

EXPORT_FOR_PRINT = STL_WRITER + f"\nMAX_TRIANGLES = {MAX_TRIANGLES}\n" + r'''
import os
from array import array

import bmesh
import bpy
import numpy as np

names = list(dict.fromkeys(ARGS.get("names") or []))
filepath = ARGS["filepath"]
build_volume = float(ARGS.get("build_volume_mm") or 256.0)
context = bpy.context

if context.mode != "OBJECT":
    return {"error": f"Blender is in {context.mode} mode; switch to Object mode (Tab in the 3D Viewport) "
                     "and export again"}
if names:
    missing = [name for name in names if bpy.data.objects.get(name) is None]
    if missing:
        return {"error": "no object named " + ", ".join(repr(name) for name in missing)}
    objects = [bpy.data.objects[name] for name in names]
else:
    objects = list(context.selected_objects)
    if not objects:
        return {"error": "nothing is selected; select the objects to export or pass their names"}
not_meshes = [f"{obj.name} ({obj.type})" for obj in objects if obj.type != "MESH"]
if not_meshes:
    return {"error": "only mesh objects can be exported, not " + ", ".join(not_meshes)}
hidden = [obj.name for obj in objects if not obj.visible_get()]
if hidden:
    return {"error": "hidden objects cannot be exported: " + ", ".join(hidden) + "; unhide them first"}
editing = [f"{obj.name} ({obj.mode})" for obj in objects if obj.mode != "OBJECT"]
if editing:
    return {"error": "objects are not in Object mode: " + ", ".join(editing)}

unit_scale = context.scene.unit_settings.scale_length or 1.0
to_mm = unit_scale * 1000.0
depsgraph = context.evaluated_depsgraph_get()


def r(value):
    return round(float(value), 3)


pieces, reports, warnings = [], [], []
total = 0
for obj in objects:
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        count = len(mesh.loop_triangles)
        if total + count > MAX_TRIANGLES:
            return {"error": f"the export would have more than {MAX_TRIANGLES} triangles (at {obj.name}); "
                             "lower Subdivision levels or add a Decimate modifier first"}
        if count == 0:
            warnings.append(f"{obj.name}: has no faces and was left out")
            continue
        co = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", co)
        corners = np.empty(count * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get("vertices", corners)
        matrix = np.array(evaluated.matrix_world, dtype=np.float64)
        points = (co.reshape(-1, 3).astype(np.float64) @ matrix[:3, :3].T + matrix[:3, 3]) * to_mm
        corners = corners.reshape(-1, 3)
        if np.linalg.det(matrix[:3, :3]) < 0:
            # A mirrored transform turns the winding inside out; reverse it so normals face out.
            corners = corners[:, ::-1]
        triangles = points[corners]
        volume_mm3 = float(np.einsum("ij,ij->i", triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum()) / 6.0
        flat = triangles.reshape(-1, 3)
        low, high = flat.min(axis=0), flat.max(axis=0)

        bm = bmesh.new()
        try:
            bm.from_mesh(mesh, face_normals=False, vertex_normals=False)
            boundary = non_manifold = inconsistent = 0
            for edge in bm.edges:
                faces = len(edge.link_faces)
                if faces == 1:
                    boundary += 1
                elif faces != 2:
                    non_manifold += 1
                elif not edge.is_contiguous:
                    inconsistent += 1
        finally:
            bm.free()
    finally:
        evaluated.to_mesh_clear()

    total += count
    pieces.append((triangles.astype(np.float32).reshape(-1), low, high))
    volume_cm3 = volume_mm3 / 1000.0
    reports.append({
        "name": obj.name,
        "triangles": count,
        "size_mm": [r(v) for v in high - low],
        "boundary_edges": boundary,
        "non_manifold_edges": non_manifold,
        "inconsistent_edges": inconsistent,
        "volume_cm3": r(volume_cm3),
    })
    if boundary or non_manifold:
        warnings.append(f"{obj.name}: not watertight ({boundary} boundary and {non_manifold} non-manifold edges); "
                        "the slicer may fill holes or drop parts")
    if inconsistent:
        warnings.append(f"{obj.name}: {inconsistent} edges join faces with opposite normals; recalculate normals")
    if not (boundary or non_manifold or inconsistent) and volume_cm3 < 0:
        warnings.append(f"{obj.name}: normals point inward (volume {r(volume_cm3)} cm3); flip them to face outside")

if not pieces:
    return {"error": "nothing to export: the objects have no faces"}

low = np.min([piece[1] for piece in pieces], axis=0)
high = np.max([piece[2] for piece in pieces], axis=0)
size = high - low
coords = array("f")
coords.frombytes(np.ascontiguousarray(np.concatenate([piece[0] for piece in pieces]), dtype=np.float32).tobytes())
os.makedirs(os.path.dirname(filepath), exist_ok=True)
write_binary_stl(filepath, coords)

too_big = [axis for axis, value in zip("xyz", size) if value > build_volume]
if too_big:
    warnings.append(f"size {r(size[0])} x {r(size[1])} x {r(size[2])} mm exceeds the {build_volume:g} mm "
                    f"build volume on {', '.join(too_big)}")
too_small = [axis for axis, value in zip("xyz", size) if value < 1.0]
if too_small:
    warnings.append(f"size below 1 mm on {', '.join(too_small)}: check the scene units (unit scale {unit_scale:g})")
if len(reports) > 1:
    warnings.append(f"{len(reports)} objects go into one STL: " + ", ".join(rep["name"] for rep in reports))

return {
    "filepath": filepath,
    "triangles": total,
    "size_mm": [r(v) for v in size],
    "min_mm": [r(v) for v in low],
    "max_mm": [r(v) for v in high],
    "volume_cm3": r(sum(rep["volume_cm3"] for rep in reports)),
    "unit_scale": unit_scale,
    "objects": reports,
    "watertight": all(not (rep["boundary_edges"] or rep["non_manifold_edges"] or rep["inconsistent_edges"])
                      for rep in reports),
    "warnings": warnings,
}
'''


def register(mcp, run_script):
    """Add export_for_print to `mcp`; `run_script(script, args)` runs a blender_scripts script."""

    @mcp.tool()
    async def export_for_print(
        filepath: str,
        names: list[str] | None = None,
        build_volume_mm: float = 256.0,
    ) -> str:
        """Export mesh objects as one binary STL in millimetres, ready for a slicer.

        `names` are the objects to export; leave it empty to export the selected objects.
        One STL per call: several objects are merged into that one file. Modifiers are
        applied in the file, world transforms (scale, rotation, parents, mirroring) are
        baked in, and scene units are converted to millimetres. The scene is not changed:
        no operators run, and objects, selection, active object and mode stay as they are.
        Blender must be in Object mode; hidden objects and more than 2,000,000 triangles
        are refused.

        `filepath` must end with .stl and lie inside the repository, Documents/BlenderMCP
        or PRINT_MCP_WORK_DIR, for example designs/<slug>/print/<part>.stl.
        `build_volume_mm` is the printer's build size per axis (256 for the Bambu Lab P2S).

        Returns JSON: size, min and max in millimetres, triangle count, volume in cm3,
        `watertight`, and per object its boundary, non-manifold and inconsistent edges.
        Read `warnings` before slicing: open meshes, inward normals, parts larger than the
        build volume, or smaller than 1 mm (usually a unit mistake).
        """
        try:
            path = resolve_allowed(filepath)
        except ValueError as exc:
            return f"Error: {exc}"
        if path.suffix.lower() != ".stl":
            return f"Error: filepath must end with .stl, got {path.name!r}"
        if isinstance(build_volume_mm, bool) or not build_volume_mm or build_volume_mm <= 0:
            return f"Error: build_volume_mm must be positive, got {build_volume_mm!r}"
        args = {
            "filepath": str(path),
            "names": list(names or []),
            "build_volume_mm": float(build_volume_mm),
        }
        try:
            report = run_script(EXPORT_FOR_PRINT, args)
        except Exception as exc:  # noqa: BLE001 - connection, addon or script failures
            return f"Error: the export did not run in Blender: {exc}"
        if report.get("error"):
            return f"Error: {report['error']}"
        return json.dumps(report, ensure_ascii=False, indent=2)

    return export_for_print
