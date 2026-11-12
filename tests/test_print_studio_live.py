"""Live, read-only checks against open Bambu Studio windows. Skipped when there are none.

Lists windows and captures one with PrintWindow. It never clicks, focuses, moves,
resizes or closes anything.
"""
from __future__ import annotations

import os

import pytest

from test_print_png import read_png


def _live_windows():
    if os.name != "nt":
        return []
    from print_mcp.studio import list_windows

    return list_windows()


WINDOWS = _live_windows()
pytestmark = pytest.mark.skipif(not WINDOWS, reason="no Bambu Studio window is open")


def test_windows_are_listed():
    assert WINDOWS
    for window in WINDOWS:
        assert window.title.strip()
        assert window.width >= 200 and window.height >= 200


def test_capture_has_the_window_size_and_real_content():
    from print_mcp.studio import Win32Backend, capture_window

    window = next((w for w in WINDOWS if not w.minimized), None)
    if window is None:
        pytest.skip("every Bambu Studio window is minimized")
    data, info = capture_window(hwnd=window.hwnd)
    width, height, _, _ = read_png(data)
    assert (width, height) == (window.width, window.height)
    assert info["image_size"] == [window.width, window.height]

    _, _, raw = Win32Backend().capture(window.hwnd)
    step = 4 * 997
    colours = {raw[i:i + 3] for i in range(0, len(raw) - 3, step)}
    assert len(colours) > 1, "the capture is a single colour"
