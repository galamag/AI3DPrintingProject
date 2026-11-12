"""export_for_print: Blender mesh objects as one millimetre STL, with mesh checks.

A fork addition, kept in its own module so upstream merges stay cheap: server.py only
imports this module and calls `register(mcp, _run_script)`.

The export runs as a script through the addon's execute_code (see blender_scripts). It
calls no operators and changes nothing in the scene: it reads each object's evaluated
mesh from the depsgraph (modifiers applied), bakes the world matrix in, converts scene
units to millimetres and writes a binary STL itself. The file path is checked here, on
the server, before Blender sees it.

The script is assembled from three parts: STL_WRITER (pure Python) and MESH_MATH (numpy
only) run without Blender too, so the tests can execute them; the rest needs bpy.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from print_mcp.paths import REPO_ROOT, resolve_allowed

MAX_TRIANGLES = 2_000_000

# Pure Python: Blender's numpy is not available to the test environment, and 2,000,000
# triangles take under 2 s this way.
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

# numpy only. Triangles are (n, 3) vertex indices from Mesh.loop_triangles; the edge
# checks on triangles equal those on polygons, since a triangulation's inner diagonals
# always join two consistently wound triangles of the same polygon.
MESH_MATH = r'''
import numpy as _np


def world_triangles(co, corners, matrix, to_mm):
    """(triangles, corners): triangles as (n, 3, 3) world coordinates times `to_mm`.

    `co` holds 3 floats per vertex, `corners` 3 vertex indices per triangle. Under a
    mirroring matrix (negative determinant) the winding is reversed, so normals that
    faced out in object space still face out.
    """
    matrix = _np.asarray(matrix, dtype=_np.float64)
    points = _np.asarray(co, dtype=_np.float64).reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    corners = _np.asarray(corners, dtype=_np.int64).reshape(-1, 3)
    if _np.linalg.det(matrix[:3, :3]) < 0:
        corners = corners[:, ::-1]
    return points[corners] * to_mm, corners


def signed_volumes(triangles):
    """Signed volume of the tetrahedron each triangle spans with the origin."""
    return _np.einsum("ij,ij->i", triangles[:, 0], _np.cross(triangles[:, 1], triangles[:, 2])) / 6.0


def edge_checks(corners, vertex_count, edges=None):
    """Edge defect counts, and a flag per triangle that touches a defective edge.

    boundary: one face; non_manifold: three or more faces; inconsistent: two faces wound
    the same way along the edge; loose: mesh `edges` (pairs of vertex indices) with no face.
    """
    corners = _np.asarray(corners, dtype=_np.int64).reshape(-1, 3)
    count = len(corners)
    starts = corners.reshape(-1)
    ends = corners[:, [1, 2, 0]].reshape(-1)
    owners = _np.repeat(_np.arange(count), 3)
    real = starts != ends
    starts, ends, owners = starts[real], ends[real], owners[real]
    keys = _np.minimum(starts, ends) * vertex_count + _np.maximum(starts, ends)
    order = _np.argsort(keys, kind="stable")
    keys, forward, owners = keys[order], (starts < ends)[order], owners[order]
    unique, first, uses = _np.unique(keys, return_index=True, return_counts=True)
    boundary = uses == 1
    non_manifold = uses > 2
    pairs = _np.flatnonzero(uses == 2)
    inconsistent = _np.zeros(len(unique), dtype=bool)
    inconsistent[pairs] = forward[first[pairs]] == forward[first[pairs] + 1]
    defective = _np.repeat(boundary | non_manifold | inconsistent, uses)
    bad_triangles = _np.zeros(count, dtype=bool)
    bad_triangles[owners[defective]] = True
    loose = 0
    if edges is not None and len(edges):
        edges = _np.asarray(edges, dtype=_np.int64).reshape(-1, 2)
        edge_keys = _np.minimum(edges[:, 0], edges[:, 1]) * vertex_count + _np.maximum(edges[:, 0], edges[:, 1])
        loose = int(_np.count_nonzero(~_np.isin(edge_keys, unique)))
    counts = {
        "boundary_edges": int(boundary.sum()),
        "non_manifold_edges": int(non_manifold.sum()),
        "inconsistent_edges": int(inconsistent.sum()),
        "loose_edges": loose,
    }
    return counts, bad_triangles


def shells(corners, vertex_count):
    """(label per triangle, shell count): triangles sharing a vertex are one shell."""
    corners = _np.asarray(corners, dtype=_np.int64).reshape(-1, 3)
    if not len(corners):
        return _np.zeros(0, dtype=_np.int64), 0
    parent = _np.arange(vertex_count, dtype=_np.int64)
    u = _np.concatenate([corners[:, 0], corners[:, 1]])
    v = _np.concatenate([corners[:, 1], corners[:, 2]])
    while True:
        # Every entry of `parent` is a root here; hook each larger root under a smaller one.
        ru, rv = parent[u], parent[v]
        low, high = _np.minimum(ru, rv), _np.maximum(ru, rv)
        join = low != high
        if not join.any():
            break
        _np.minimum.at(parent, high[join], low[join])
        while True:
            jumped = parent[parent]
            if _np.array_equal(jumped, parent):
                break
            parent = jumped
    _, labels = _np.unique(parent[corners[:, 0]], return_inverse=True)
    labels = labels.reshape(-1)
    return labels, int(labels.max()) + 1


def shell_volumes(labels, count, volumes, bad_triangles):
    """(signed volume per shell, whether each shell is closed)."""
    volume = _np.bincount(labels, weights=volumes, minlength=count)
    defects = _np.bincount(labels, weights=bad_triangles.astype(_np.float64), minlength=count)
    return volume, defects == 0
'''

EXPORT_FOR_PRINT = STL_WRITER + MESH_MATH + f"\nMAX_TRIANGLES = {MAX_TRIANGLES}\n" + r'''
SIZE_TOLERANCE_MM = 0.01

import os
from array import array

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
layer_objects = context.view_layer.objects
outside = [obj.name for obj in objects if layer_objects.get(obj.name) is None]
if outside:
    return {"error": "not in the current view layer (in an excluded collection, or not linked to this scene): "
                     + ", ".join(outside) + "; include its collection in the view layer first"}
hidden = [obj.name for obj in objects if not obj.visible_get()]
if hidden:
    return {"error": "hidden objects cannot be exported: " + ", ".join(hidden) + "; unhide them first"}
editing = [f"{obj.name} ({obj.mode})" for obj in objects if obj.mode != "OBJECT"]
if editing:
    return {"error": "objects are not in Object mode: " + ", ".join(editing)}

unit_scale = context.scene.unit_settings.scale_length or 1.0
to_mm = unit_scale * 1000.0
depsgraph = context.evaluated_depsgraph_get()

# Instances (geometry nodes, particles, instanced collections) are not part of to_mesh().
exported = {obj.name for obj in objects}
instances = {}
for item in depsgraph.object_instances:  # an iterator only; keep no references to items
    if item.is_instance and item.parent is not None:
        source = item.parent.original
        if source is not None and source.name in exported:
            instances[source.name] = instances.get(source.name, 0) + 1


def r(value):
    return round(float(value), 3)


def too_many(name):
    return {"error": f"the export would have more than {MAX_TRIANGLES} triangles (at {name}); "
                     "lower Subdivision levels or add a Decimate modifier first"}


pieces, reports, warnings = [], [], []
total = 0
for obj in objects:
    evaluated = obj.evaluated_get(depsgraph)
    data = evaluated.data
    # Each polygon of n corners makes n - 2 triangles; checked before anything is copied.
    if total + len(data.loops) - 2 * len(data.polygons) > MAX_TRIANGLES:
        return too_many(obj.name)
    mesh = evaluated.to_mesh()
    try:
        if total + len(mesh.loops) - 2 * len(mesh.polygons) > MAX_TRIANGLES:
            return too_many(obj.name)
        mesh.calc_loop_triangles()
        count = len(mesh.loop_triangles)
        instanced = instances.get(obj.name, 0)
        if count == 0:
            if instanced:
                return {"error": f"{obj.name}: has no faces of its own; its {instanced} instances are not "
                                 "included; add a Realize Instances node or make them real"}
            warnings.append(f"{obj.name}: has no faces and was left out")
            continue
        vertex_count = len(mesh.vertices)
        co = np.empty(vertex_count * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", co)
        corners = np.empty(count * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get("vertices", corners)
        edges = np.empty(len(mesh.edges) * 2, dtype=np.int32)
        mesh.edges.foreach_get("vertices", edges)
        matrix = np.array(evaluated.matrix_world, dtype=np.float64)
    finally:
        evaluated.to_mesh_clear()

    triangles, corners = world_triangles(co, corners, matrix, to_mm)
    volumes = signed_volumes(triangles)
    checks, bad_triangles = edge_checks(corners, vertex_count, edges)
    labels, shell_count = shells(corners, vertex_count)
    shell_volume, shell_closed = shell_volumes(labels, shell_count, volumes, bad_triangles)
    inward_shells = int(np.count_nonzero(shell_closed & (shell_volume < 0)))
    flat = triangles.reshape(-1, 3)
    low, high = flat.min(axis=0), flat.max(axis=0)

    total += count
    pieces.append((triangles.astype(np.float32).reshape(-1), low, high))
    volume_cm3 = float(volumes.sum()) / 1000.0
    watertight = not (checks["boundary_edges"] or checks["non_manifold_edges"] or checks["inconsistent_edges"])
    reports.append({
        "name": obj.name,
        "triangles": count,
        "size_mm": [r(v) for v in high - low],
        **checks,
        "shells": shell_count,
        "inward_shells": inward_shells,
        "volume_cm3": r(volume_cm3),
    })
    if checks["boundary_edges"] or checks["non_manifold_edges"]:
        warnings.append(f"{obj.name}: not watertight ({checks['boundary_edges']} boundary and "
                        f"{checks['non_manifold_edges']} non-manifold edges); the slicer may fill holes or drop parts")
    if checks["inconsistent_edges"]:
        warnings.append(f"{obj.name}: {checks['inconsistent_edges']} edges join faces with opposite normals; "
                        "recalculate normals")
    whole_inward = watertight and volume_cm3 < 0
    if whole_inward:
        warnings.append(f"{obj.name}: normals point inward (volume {r(volume_cm3)} cm3); flip them to face outside")
    if inward_shells and not (whole_inward and inward_shells == shell_count):
        warnings.append(f"{obj.name}: {inward_shells} of {shell_count} shells are closed with inward normals "
                        "(negative volume); right for an intended inner cavity, otherwise flip them")
    if checks["loose_edges"]:
        warnings.append(f"{obj.name}: {checks['loose_edges']} loose edges without faces; they are not printed")
    if instanced:
        warnings.append(f"{obj.name}: {instanced} instances are not included; add a Realize Instances node "
                        "or make them real")

if not pieces:
    return {"error": "nothing to export: the objects have no faces"}

low = np.min([piece[1] for piece in pieces], axis=0)
high = np.max([piece[2] for piece in pieces], axis=0)
size = high - low
coords = array("f")
coords.frombytes(np.ascontiguousarray(np.concatenate([piece[0] for piece in pieces]), dtype=np.float32).tobytes())
os.makedirs(os.path.dirname(filepath), exist_ok=True)
write_binary_stl(filepath, coords)

too_big = [axis for axis, value in zip("xyz", size) if value > build_volume + SIZE_TOLERANCE_MM]
if too_big:
    warnings.append(f"size {r(size[0])} x {r(size[1])} x {r(size[2])} mm exceeds the {build_volume:g} mm "
                    f"build volume on {', '.join(too_big)}")
too_small = [axis for axis, value in zip("xyz", size) if value < 1.0 - SIZE_TOLERANCE_MM]
if too_small:
    warnings.append(f"size below 1 mm on {', '.join(too_small)}: check the scene units (unit scale {unit_scale:.6g})")
if len(reports) > 1:
    warnings.append(f"{len(reports)} objects go into one STL: " + ", ".join(rep["name"] for rep in reports))

return {
    "filepath": filepath,
    "triangles": total,
    "size_mm": [r(v) for v in size],
    "min_mm": [r(v) for v in low],
    "max_mm": [r(v) for v in high],
    "volume_cm3": r(sum(rep["volume_cm3"] for rep in reports)),
    "unit_scale": float(f"{unit_scale:.6g}"),
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
        overwrite: bool = False,
    ) -> str:
        """Export mesh objects as one binary STL in millimetres, ready for a slicer.

        `names` are the objects to export; leave it empty to export the selected objects.
        One STL per call: several objects are merged into that one file. Modifiers are
        applied with their viewport settings, world transforms (scale, rotation, parents,
        mirroring) are baked in, and scene units are converted to millimetres. Instances
        (geometry nodes, particles, instanced collections) are not included; a warning
        names them. The scene is not changed: no operators run, and objects, selection,
        active object and mode stay as they are. Blender must be in Object mode; hidden
        objects, objects outside the view layer and more than 2,000,000 triangles are refused.

        `filepath` must end with .stl and lie inside the repository, Documents/BlenderMCP
        or PRINT_MCP_WORK_DIR; a relative path starts at the repository, for example
        designs/<slug>/print/<part>.stl. An existing file is refused unless `overwrite` is
        true. `build_volume_mm` is the printer's build size per axis (256 for the P2S).

        Returns JSON: size, min and max in millimetres, triangle count, volume in cm3,
        `watertight`, and per object its boundary, non-manifold, inconsistent and loose
        edges, shells and inward shells. `watertight` means no boundary, non-manifold or
        inconsistent edges; loose edges do not count against it. It does not check
        self-intersections, shells that touch at a single vertex, or inner shells inside
        others. Read `warnings` before slicing: open meshes, inward normals, left-out
        instances, loose edges, parts larger than the build volume, or smaller than 1 mm
        (usually a unit mistake).
        """
        raw = Path(filepath)
        try:
            path = resolve_allowed(raw if raw.is_absolute() else REPO_ROOT / raw)
        except ValueError as exc:
            return f"Error: {exc}"
        if path.suffix.lower() != ".stl":
            return f"Error: filepath must end with .stl, got {path.name!r}"
        if (
            isinstance(build_volume_mm, bool)
            or not isinstance(build_volume_mm, (int, float))
            or not math.isfinite(build_volume_mm)
            or build_volume_mm <= 0
        ):
            return f"Error: build_volume_mm must be a positive finite number, got {build_volume_mm!r}"
        if path.exists() and not overwrite:
            return f"Error: {path} already exists; pass overwrite=true to replace it"
        args = {
            "filepath": str(path),
            "names": list(names or []),
            "build_volume_mm": float(build_volume_mm),
        }
        try:
            report = run_script(EXPORT_FOR_PRINT, args)
        except Exception as exc:  # noqa: BLE001 - connection, addon or script failures
            return f"Error: the export failed in Blender: {exc}"
        if report.get("error"):
            return f"Error: {report['error']}"
        return json.dumps(report, ensure_ascii=False, indent=2)

    return export_for_print
