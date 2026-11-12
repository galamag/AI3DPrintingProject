"""The numpy helpers export_for_print runs inside Blender, run without Blender.

Skipped where numpy is not installed (it is not a dependency of this project; Blender
bundles it).
"""
from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")

from blender_mcp.print_export import MESH_MATH  # noqa: E402

CUBE_VERTICES = [(x, y, z) for z in (0, 1) for y in (0, 1) for x in (0, 1)]
CUBE_TRIANGLES = [
    (0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6), (0, 1, 5), (0, 5, 4),
    (2, 6, 7), (2, 7, 3), (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5),
]
CUBE_EDGES = sorted({tuple(sorted((t[i], t[(i + 1) % 3]))) for t in CUBE_TRIANGLES for i in range(3)})


@pytest.fixture(scope="module")
def math_helpers():
    namespace = {}
    exec(MESH_MATH, namespace)
    return namespace


def _co(vertices):
    return np.asarray(vertices, dtype=np.float32).reshape(-1)


def _two_cubes(inner_inverted=False):
    """A 3-unit cube with a 1-unit cube inside it, as separate shells."""
    outer = [(x * 3, y * 3, z * 3) for x, y, z in CUBE_VERTICES]
    inner = [(x + 1, y + 1, z + 1) for x, y, z in CUBE_VERTICES]
    inner_triangles = [tuple(v + 8 for v in (t[::-1] if inner_inverted else t)) for t in CUBE_TRIANGLES]
    return outer + inner, CUBE_TRIANGLES + inner_triangles


# --- transform and volume -----------------------------------------------------------


def test_world_triangles_apply_matrix_and_units(math_helpers):
    matrix = np.eye(4)
    matrix[:3, :3] *= 2.0
    matrix[:3, 3] = (1.0, 0.0, 0.0)
    triangles, corners = math_helpers["world_triangles"](_co(CUBE_VERTICES), CUBE_TRIANGLES, matrix, 1000.0)
    assert triangles.shape == (12, 3, 3)
    flat = triangles.reshape(-1, 3)
    assert flat.min(axis=0).tolist() == [1000.0, 0.0, 0.0]
    assert flat.max(axis=0).tolist() == [3000.0, 2000.0, 2000.0]
    assert corners.tolist() == [list(t) for t in CUBE_TRIANGLES]


def test_mirroring_reverses_the_winding(math_helpers):
    matrix = np.diag([-1.0, 1.0, 1.0, 1.0])
    triangles, corners = math_helpers["world_triangles"](_co(CUBE_VERTICES), CUBE_TRIANGLES, matrix, 1.0)
    assert corners.tolist() == [list(t[::-1]) for t in CUBE_TRIANGLES]
    assert math.isclose(math_helpers["signed_volumes"](triangles).sum(), 1.0)


def test_signed_volume_of_a_cube(math_helpers):
    triangles, _ = math_helpers["world_triangles"](_co(CUBE_VERTICES), CUBE_TRIANGLES, np.eye(4), 20.0)
    assert math.isclose(math_helpers["signed_volumes"](triangles).sum(), 8000.0)
    inverted = triangles[:, ::-1]
    assert math.isclose(math_helpers["signed_volumes"](inverted).sum(), -8000.0)


# --- edge checks ----------------------------------------------------------------------


def test_closed_cube_has_no_defects(math_helpers):
    counts, bad = math_helpers["edge_checks"](CUBE_TRIANGLES, 8, CUBE_EDGES)
    assert counts == {"boundary_edges": 0, "non_manifold_edges": 0, "inconsistent_edges": 0, "loose_edges": 0}
    assert not bad.any()


def test_open_cube(math_helpers):
    counts, bad = math_helpers["edge_checks"](CUBE_TRIANGLES[:-2], 8, CUBE_EDGES)
    assert counts["boundary_edges"] == 4
    assert counts["non_manifold_edges"] == counts["inconsistent_edges"] == 0
    assert counts["loose_edges"] == 1, "the removed face's diagonal is still a mesh edge"
    assert bad.sum() > 0


def test_one_flipped_triangle(math_helpers):
    triangles = CUBE_TRIANGLES[:-1] + [CUBE_TRIANGLES[-1][::-1]]
    counts, bad = math_helpers["edge_checks"](triangles, 8, CUBE_EDGES)
    assert counts["inconsistent_edges"] == 3
    assert counts["boundary_edges"] == counts["non_manifold_edges"] == 0


def test_three_faces_on_one_edge(math_helpers):
    triangles = [(0, 1, 2), (1, 0, 3), (0, 1, 4)]
    counts, _ = math_helpers["edge_checks"](triangles, 5)
    assert counts["non_manifold_edges"] == 1
    assert counts["boundary_edges"] == 6


def test_loose_edges_are_counted_apart(math_helpers):
    counts, bad = math_helpers["edge_checks"](CUBE_TRIANGLES, 10, CUBE_EDGES + [(8, 9), (0, 8)])
    assert counts["loose_edges"] == 2
    assert counts["boundary_edges"] == counts["non_manifold_edges"] == counts["inconsistent_edges"] == 0
    assert not bad.any()


def test_degenerate_triangle_does_not_count_a_point_as_an_edge(math_helpers):
    counts, _ = math_helpers["edge_checks"](CUBE_TRIANGLES + [(0, 0, 1)], 8, CUBE_EDGES)
    assert counts["non_manifold_edges"] == 1, "edge 0-1 now has more than two triangles"


# --- shells ---------------------------------------------------------------------------


def test_shells_of_two_separate_cubes(math_helpers):
    vertices, triangles = _two_cubes()
    labels, count = math_helpers["shells"](triangles, len(vertices))
    assert count == 2
    assert set(labels[:12].tolist()) != set(labels[12:].tolist())
    assert len(set(labels[:12].tolist())) == 1 and len(set(labels[12:].tolist())) == 1


def test_an_inverted_inner_shell_is_found(math_helpers):
    vertices, triangles = _two_cubes(inner_inverted=True)
    tris, corners = math_helpers["world_triangles"](_co(vertices), triangles, np.eye(4), 1.0)
    volumes = math_helpers["signed_volumes"](tris)
    _, bad = math_helpers["edge_checks"](corners, len(vertices))
    labels, count = math_helpers["shells"](corners, len(vertices))
    shell_volume, closed = math_helpers["shell_volumes"](labels, count, volumes, bad)
    assert sorted(np.round(shell_volume, 6).tolist()) == [-1.0, 27.0]
    assert closed.all()
    assert math.isclose(volumes.sum(), 26.0)


def test_an_open_shell_is_not_closed(math_helpers):
    vertices, triangles = _two_cubes()
    triangles = triangles[:-2]  # open the inner cube
    tris, corners = math_helpers["world_triangles"](_co(vertices), triangles, np.eye(4), 1.0)
    _, bad = math_helpers["edge_checks"](corners, len(vertices))
    labels, count = math_helpers["shells"](corners, len(vertices))
    _, closed = math_helpers["shell_volumes"](labels, count, math_helpers["signed_volumes"](tris), bad)
    assert sorted(closed.tolist()) == [False, True]


def test_shells_of_a_long_strip_converge(math_helpers):
    # A 2000-quad strip numbered so that naive label spreading would take many rounds.
    count = 2000
    order = np.random.default_rng(7).permutation(2 * (count + 1))
    triangles = []
    for i in range(count):
        a, b, c, d = (order[2 * i], order[2 * i + 1], order[2 * i + 2], order[2 * i + 3])
        triangles += [(a, b, d), (a, d, c)]
    labels, shells = math_helpers["shells"](triangles, len(order))
    assert shells == 1 and len(labels) == 2 * count
