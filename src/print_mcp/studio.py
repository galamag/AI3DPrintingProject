"""Bambu Studio windows in the background: list, capture, click and open.

Nothing here takes focus, moves the mouse or changes a window's size or state. A capture is
`PrintWindow` into a memory bitmap; a click is `WM_MOUSEMOVE`, `WM_LBUTTONDOWN` and
`WM_LBUTTONUP` posted to the deepest child control under the point. Every Win32 call lives
in `Win32Backend`; the logic around it takes any object with the same methods, so it can be
tested without real windows.

Coordinates are window pixels: (0, 0) is the top-left corner of the window rectangle, the
same pixel as in a capture at scale 1 without a crop. The calling thread is made
per-monitor DPI aware for every call, so window rectangles, captures and clicks all use
physical pixels.
"""
from __future__ import annotations

import ctypes
import dataclasses
import math
import os
import subprocess
import time
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from .paths import resolve_allowed, studio_exe
from .png import encode_png

STUDIO_IMAGE = "bambu-studio.exe"
MIN_WINDOW_PX = 200
OPEN_SUFFIXES = (".3mf", ".stl", ".step", ".stp", ".obj")
MIN_SCALE, MAX_SCALE = 0.1, 1.0

# The model API downscales larger images, which would break the image-to-window formula.
MAX_IMAGE_EDGE = 1568
MAX_IMAGE_PIXELS = 1_150_000

# Wait after posting a click before reading the foreground window again.
_SETTLE_S = 0.5
# Poll interval while waiting for a launched Bambu Studio to show its window.
_POLL_S = 0.5

_SW_SHOWNOACTIVATE = 4

# Bambu Studio processes this module started, by file, so a slow start is not launched twice.
_LAUNCHED: dict[Path, subprocess.Popen] = {}


class StudioError(RuntimeError):
    """A Bambu Studio window cannot be found, picked, captured or clicked."""


@dataclass
class Window:
    hwnd: int
    pid: int
    title: str
    left: int
    top: int
    width: int
    height: int
    minimized: bool
    visible: bool = True
    enabled: bool = True

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class Target:
    """The control a click goes to, and the click point in its client area."""

    hwnd: int
    client_x: int
    client_y: int
    class_trail: list[str]
    enabled: bool


# --- window choice ----------------------------------------------------------------


def _backend(backend):
    return backend if backend is not None else Win32Backend()


def list_windows(backend=None) -> list[Window]:
    """Visible Bambu Studio windows with a title and at least 200x200 px.

    Tooltips, menus and hidden helper windows of the process are left out; dialogs such as
    the print-send window stay in. A minimized window keeps its restored size and is marked
    `minimized`; a window blocked by a modal dialog has `enabled` false.
    """
    return [
        window
        for window in _backend(backend).windows()
        if window.visible
        and window.title.strip()
        and window.width >= MIN_WINDOW_PX
        and window.height >= MIN_WINDOW_PX
    ]


def _describe(windows: list[Window]) -> str:
    return "; ".join(
        f"hwnd {w.hwnd}: {w.title!r}"
        + (" (minimized)" if w.minimized else "")
        + ("" if w.enabled else " (disabled)")
        for w in windows
    )


def pick_window(hwnd: int | None = None, title_contains: str | None = None, backend=None) -> Window:
    """The one window meant: by `hwnd`, else by a title substring, else the only window."""
    windows = list_windows(backend)
    if not windows:
        raise StudioError("Bambu Studio is not running (no Bambu Studio window is open)")
    if hwnd is not None:
        for window in windows:
            if window.hwnd == hwnd:
                return window
        raise StudioError(f"hwnd {hwnd} is not a Bambu Studio window. Open windows: {_describe(windows)}")
    if title_contains:
        needle = title_contains.casefold()
        matches = [w for w in windows if needle in w.title.casefold()]
        if len(matches) == 1:
            return matches[0]
        count = "No" if not matches else str(len(matches))
        raise StudioError(
            f"{count} Bambu Studio windows match {title_contains!r}. Open windows: {_describe(windows)}"
        )
    if len(windows) == 1:
        return windows[0]
    raise StudioError(
        f"{len(windows)} Bambu Studio windows are open; pass hwnd or title_contains. "
        f"Open windows: {_describe(windows)}"
    )


def _require_restored(window: Window) -> None:
    if window.minimized:
        raise StudioError(
            f"window {window.hwnd} ({window.title!r}) is minimized; the tools never restore "
            "windows, so ask the user to restore it"
        )


_DIALOG_OPEN = "a dialog is open; list windows and pick the dialog"


# --- capture ----------------------------------------------------------------------


def _check_crop(crop, width: int, height: int) -> tuple[int, int, int, int]:
    if len(crop) != 4 or not all(isinstance(v, int) and not isinstance(v, bool) for v in crop):
        raise ValueError(f"crop must be four integers (left, top, right, bottom), got {crop!r}")
    left, top, right, bottom = crop
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(
            f"crop {list(crop)} must lie inside the {width}x{height} window and have a positive area"
        )
    return left, top, right, bottom


def _output_size(width: int, height: int, scale: float) -> tuple[int, int, bool]:
    """Integer output size for `scale`, shrunk so the model API will not downscale it again."""
    cap = min(1.0, MAX_IMAGE_EDGE / max(width, height), math.sqrt(MAX_IMAGE_PIXELS / (width * height)))
    effective = min(scale, cap)
    new_width = max(1, int(width * effective + 1e-9))
    new_height = max(1, int(height * effective + 1e-9))
    while max(new_width, new_height) > MAX_IMAGE_EDGE or new_width * new_height > MAX_IMAGE_PIXELS:
        new_width, new_height = max(1, new_width - 1), max(1, new_height - 1)
    return new_width, new_height, effective < scale


def capture_window(
    hwnd: int | None = None,
    title_contains: str | None = None,
    scale: float = 1.0,
    crop: tuple[int, int, int, int] | None = None,
    backend=None,
) -> tuple[bytes, dict]:
    """PNG of a Bambu Studio window, even when other windows cover it.

    `crop` is (left, top, right, bottom) in window pixels and is applied before `scale`
    (0.1 to 1.0). The scale is reduced when needed to keep the image within 1568 px and
    1.15 MP; `scale_x` and `scale_y` are the factors actually used, and `to_window_px`
    maps image pixels back to window pixels with them.
    """
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not MIN_SCALE <= scale <= MAX_SCALE:
        raise ValueError(f"scale must be between {MIN_SCALE} and {MAX_SCALE}, got {scale!r}")
    backend = _backend(backend)
    window = pick_window(hwnd, title_contains, backend)
    _require_restored(window)
    box = _check_crop(crop, window.width, window.height) if crop is not None else None

    width, height, bgra = backend.capture(window.hwnd)
    left = top = 0
    if box is not None:
        left, top, right, bottom = box
        if right > width or bottom > height:
            raise StudioError(f"the window is now {width}x{height}; capture again without this crop")
        stride = width * 4
        bgra = b"".join(bgra[y * stride + left * 4:y * stride + right * 4] for y in range(top, bottom))
        width, height = right - left, bottom - top
    new_width, new_height, reduced = _output_size(width, height, float(scale))
    if (new_width, new_height) != (width, height):
        bgra = backend.resize(width, height, bgra, new_width, new_height)
    scale_x, scale_y = new_width / width, new_height / height

    warnings = []
    if reduced:
        warnings.append(
            f"requested scale {float(scale)} was reduced to {scale_x:.4f} x {scale_y:.4f} so the "
            f"image stays within {MAX_IMAGE_EDGE} px and {MAX_IMAGE_PIXELS / 1e6:.2f} MP; "
            "crop to see more detail"
        )
    if not window.enabled:
        warnings.append(f"the window is disabled: {_DIALOG_OPEN}")
    info = {
        "window": window.as_dict(),
        "requested_scale": float(scale),
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_reduced": reduced,
        "crop": list(box) if box is not None else None,
        "image_size": [new_width, new_height],
        "to_window_px": (
            "window_x = crop_left + image_x / scale_x, window_y = crop_top + image_y / scale_y "
            f"(crop_left={left}, crop_top={top}, scale_x={scale_x:.6f}, scale_y={scale_y:.6f})"
        ),
        "click_hint": (
            f"pass expected_width={window.width}, expected_height={window.height} to studio_click "
            f"together with the window_x, window_y it computes, and hwnd={window.hwnd}"
        ),
        "warnings": warnings,
    }
    return encode_png(new_width, new_height, bgra), info


# --- click ------------------------------------------------------------------------


def pack_lparam(x: int, y: int) -> int:
    """MAKELPARAM for mouse messages: two signed 16-bit client coordinates."""
    for value in (x, y):
        if not -0x8000 <= value <= 0x7FFF:
            raise ValueError(f"client coordinate {value} does not fit in 16 bits")
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def click_window(
    x: int,
    y: int,
    hwnd: int | None = None,
    title_contains: str | None = None,
    expected_width: int | None = None,
    expected_height: int | None = None,
    backend=None,
) -> dict:
    """Post a left click at window pixel (x, y) without focusing the window or moving the mouse.

    `expected_width` and `expected_height` are the window size from the capture the point
    was read from; a different current size is refused before anything is posted.
    """
    for name, value in (("x", x), ("y", y)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer, got {value!r}")
    backend = _backend(backend)
    window = pick_window(hwnd, title_contains, backend)
    _require_restored(window)
    if (expected_width is not None and expected_width != window.width) or (
        expected_height is not None and expected_height != window.height
    ):
        raise StudioError(
            f"the window is now {window.width}x{window.height}, not {expected_width}x{expected_height} "
            "as in the capture; capture again"
        )
    if not (0 <= x < window.width and 0 <= y < window.height):
        raise ValueError(f"point ({x}, {y}) is outside the {window.width}x{window.height} window")
    if not window.enabled:
        raise StudioError(f"window {window.hwnd} is disabled: {_DIALOG_OPEN}")
    screen_x, screen_y = window.left + x, window.top + y
    before = backend.foreground()
    target = backend.deepest_child(window.hwnd, window.pid, screen_x, screen_y)
    if not target.enabled:
        raise StudioError(
            f"the control under ({x}, {y}) or a window above it is disabled "
            f"({' > '.join(target.class_trail)}): {_DIALOG_OPEN}"
        )
    backend.post_click(target.hwnd, target.client_x, target.client_y)
    time.sleep(_SETTLE_S)
    after = backend.foreground()
    return {
        "window": window.as_dict(),
        "x": x,
        "y": y,
        "screen_x": screen_x,
        "screen_y": screen_y,
        "target_hwnd": target.hwnd,
        "class_trail": target.class_trail,
        "client_x": target.client_x,
        "client_y": target.client_y,
        "foreground_before": before,
        "foreground_after": after,
        "foreground_changed": before != after,
    }


# --- open -------------------------------------------------------------------------


def _project_name(title: str) -> str:
    """'cube.gcode - BambuStudio' -> 'cube.gcode'; a trailing '*' marks unsaved changes."""
    name = title.rsplit(" - ", 1)[0] if " - " in title else title
    return name.strip().rstrip("*").strip()


def _windows_for(path: Path, windows: list[Window]) -> list[Window]:
    # By file name only: "cube.gcode.3mf" -> "cube.gcode", as Bambu Studio titles it. Two
    # files with the same name in different folders cannot be told apart by the title.
    project = path.stem.casefold()
    return [w for w in windows if _project_name(w.title).casefold() == project]


def open_in_studio(path: str | Path, timeout: float = 60.0, backend=None) -> dict:
    """Show a file in Bambu Studio: reuse a window already titled with it, else launch one.

    A launch asks Windows not to activate the new window (SW_SHOWNOACTIVATE); whether the
    foreground changed anyway is reported in `foreground_changed`. While a Bambu Studio this
    module launched for the same file is still running without its window, it is not
    launched again.
    """
    resolved = resolve_allowed(path)
    if not resolved.name.lower().endswith(OPEN_SUFFIXES):
        raise ValueError(f"Bambu Studio opens {', '.join(OPEN_SUFFIXES)} files, not {resolved.name}")
    if not resolved.is_file():
        raise FileNotFoundError(f"no such file: {resolved}")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError(f"timeout must be a positive number of seconds, got {timeout!r}")
    backend = _backend(backend)

    existing = _windows_for(resolved, list_windows(backend))
    if existing:
        window = existing[0]
        _LAUNCHED.pop(resolved, None)
        return {
            "path": str(resolved),
            "window": window.as_dict(),
            "launched": False,
            "pid": window.pid,
            "foreground_changed": False,
        }

    starting = _LAUNCHED.get(resolved)
    if starting is not None and starting.poll() is None:
        raise StudioError(
            f"Bambu Studio (pid {starting.pid}) launched for {resolved.name} is still starting; "
            "call studio_windows or studio_open again in a moment"
        )

    exe = studio_exe()
    if not exe.is_file():
        raise StudioError(f"Bambu Studio not found at {exe}")
    before = backend.foreground()
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = _SW_SHOWNOACTIVATE
    process = subprocess.Popen(
        [str(exe), str(resolved)],
        startupinfo=startupinfo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _LAUNCHED[resolved] = process
    deadline = time.monotonic() + timeout
    while True:
        found = _windows_for(resolved, list_windows(backend))
        if found:
            break
        if time.monotonic() >= deadline:
            raise StudioError(
                f"Bambu Studio (pid {process.pid}) did not show a window for {resolved.name} "
                f"within {timeout} s; it may still be starting"
            )
        time.sleep(_POLL_S)
    _LAUNCHED.pop(resolved, None)
    after = backend.foreground()
    return {
        "path": str(resolved),
        "window": found[0].as_dict(),
        "launched": True,
        "pid": process.pid,
        "foreground_changed": before != after,
    }


# --- Win32 ------------------------------------------------------------------------

_WM_MOUSEMOVE, _WM_LBUTTONDOWN, _WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
_MK_LBUTTON = 0x0001
# Invisible children are skipped; disabled ones are kept so a click on them can be refused.
_CWP_SKIPINVISIBLE = 0x0001
_PW_RENDERFULLCONTENT = 0x00000002
_DPI_PER_MONITOR_AWARE_V2 = -4
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_GWL_EXSTYLE = -20
_WS_EX_TOOLWINDOW = 0x00000080
_HALFTONE = 4
_SRCCOPY = 0x00CC0020
_MAX_CHILD_DEPTH = 16

# Every Win32 function the backend calls. `_api` gives each one argtypes and restype.
_FUNCTIONS = {
    "user32": (
        "EnumWindows", "GetWindowThreadProcessId", "IsWindow", "IsWindowVisible", "IsWindowEnabled",
        "IsIconic", "IsHungAppWindow", "GetWindowTextLengthW", "GetWindowTextW", "GetClassNameW",
        "GetWindowRect", "GetWindowPlacement", "GetWindowLongPtrW", "GetForegroundWindow",
        "PrintWindow", "GetDC", "ReleaseDC", "ScreenToClient", "ChildWindowFromPointEx",
        "PostMessageW", "SetThreadDpiAwarenessContext",
    ),
    "gdi32": (
        "CreateCompatibleDC", "CreateDIBSection", "SelectObject", "DeleteObject", "DeleteDC",
        "SetStretchBltMode", "SetBrushOrgEx", "StretchBlt",
    ),
    "kernel32": ("OpenProcess", "QueryFullProcessImageNameW", "CloseHandle"),
}


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int32), ("y", ctypes.c_int32)]


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_int32), ("top", ctypes.c_int32),
                ("right", ctypes.c_int32), ("bottom", ctypes.c_int32)]


class _WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint32), ("flags", ctypes.c_uint32), ("showCmd", ctypes.c_uint32),
                ("ptMinPosition", _POINT), ("ptMaxPosition", _POINT), ("rcNormalPosition", _RECT)]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32), ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16), ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32), ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32), ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32), ("biClrImportant", ctypes.c_uint32)]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 3)]


_API = None


def _api() -> SimpleNamespace:
    """user32, gdi32 and kernel32 with argtypes and restype set on every function in _FUNCTIONS."""
    global _API
    if _API is not None:
        return _API
    if os.name != "nt":
        raise StudioError("the Bambu Studio window tools need Windows")
    HWND = HDC = HANDLE = HGDIOBJ = ctypes.c_void_p
    BOOL, INT, UINT, DWORD = ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint32
    WPARAM, LPARAM, LONG_PTR = ctypes.c_size_t, ctypes.c_ssize_t, ctypes.c_ssize_t
    enum_proc = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
    signatures = {
        "user32": {
            "EnumWindows": (BOOL, [enum_proc, LPARAM]),
            "GetWindowThreadProcessId": (DWORD, [HWND, ctypes.POINTER(DWORD)]),
            "IsWindow": (BOOL, [HWND]),
            "IsWindowVisible": (BOOL, [HWND]),
            "IsWindowEnabled": (BOOL, [HWND]),
            "IsIconic": (BOOL, [HWND]),
            "IsHungAppWindow": (BOOL, [HWND]),
            "GetWindowTextLengthW": (INT, [HWND]),
            "GetWindowTextW": (INT, [HWND, ctypes.c_wchar_p, INT]),
            "GetClassNameW": (INT, [HWND, ctypes.c_wchar_p, INT]),
            "GetWindowRect": (BOOL, [HWND, ctypes.POINTER(_RECT)]),
            "GetWindowPlacement": (BOOL, [HWND, ctypes.POINTER(_WINDOWPLACEMENT)]),
            "GetWindowLongPtrW": (LONG_PTR, [HWND, INT]),
            "GetForegroundWindow": (HWND, []),
            "PrintWindow": (BOOL, [HWND, HDC, UINT]),
            "GetDC": (HDC, [HWND]),
            "ReleaseDC": (INT, [HWND, HDC]),
            "ScreenToClient": (BOOL, [HWND, ctypes.POINTER(_POINT)]),
            "ChildWindowFromPointEx": (HWND, [HWND, _POINT, UINT]),
            "PostMessageW": (BOOL, [HWND, UINT, WPARAM, LPARAM]),
            "SetThreadDpiAwarenessContext": (ctypes.c_void_p, [ctypes.c_void_p]),
        },
        "gdi32": {
            "CreateCompatibleDC": (HDC, [HDC]),
            "CreateDIBSection": (HGDIOBJ, [HDC, ctypes.POINTER(_BITMAPINFO), UINT,
                                           ctypes.POINTER(ctypes.c_void_p), HANDLE, DWORD]),
            "SelectObject": (HGDIOBJ, [HDC, HGDIOBJ]),
            "DeleteObject": (BOOL, [HGDIOBJ]),
            "DeleteDC": (BOOL, [HDC]),
            "SetStretchBltMode": (INT, [HDC, INT]),
            "SetBrushOrgEx": (BOOL, [HDC, INT, INT, ctypes.c_void_p]),
            "StretchBlt": (BOOL, [HDC, INT, INT, INT, INT, HDC, INT, INT, INT, INT, DWORD]),
        },
        "kernel32": {
            "OpenProcess": (HANDLE, [DWORD, BOOL, DWORD]),
            "QueryFullProcessImageNameW": (BOOL, [HANDLE, DWORD, ctypes.c_wchar_p, ctypes.POINTER(DWORD)]),
            "CloseHandle": (BOOL, [HANDLE]),
        },
    }
    libraries = {name: ctypes.WinDLL(name, use_last_error=True) for name in _FUNCTIONS}
    for library, names in _FUNCTIONS.items():
        if set(names) != set(signatures[library]):
            raise StudioError(f"the {library} signature table does not match _FUNCTIONS")
        for name in names:
            function = getattr(libraries[library], name)
            function.restype, argtypes = signatures[library][name]
            function.argtypes = argtypes
    _API = SimpleNamespace(enum_proc=enum_proc, signatures=signatures, **libraries)
    return _API


@contextmanager
def _dpi_aware(api):
    """Per-monitor DPI awareness for this thread, restored afterwards."""
    previous = api.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(_DPI_PER_MONITOR_AWARE_V2))
    if not previous:
        raise StudioError("SetThreadDpiAwarenessContext failed; window coordinates would not be physical pixels (DPI)")
    try:
        yield
    finally:
        api.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(previous))


class Win32Backend:
    """The only place that calls Windows. No method focuses, moves or resizes a window.

    `api` is for tests: a namespace with user32, gdi32, kernel32 and enum_proc.
    """

    def __init__(self, api: SimpleNamespace | None = None) -> None:
        self._api = api if api is not None else _api()

    # windows
    def windows(self) -> list[Window]:
        """Top-level windows owned by a bambu-studio.exe process, without tool windows."""
        api = self._api
        studio_pids: dict[int, bool] = {}
        found: list[Window] = []

        def visit(hwnd, _lparam):
            try:
                pid = self._pid(hwnd)
                if pid not in studio_pids:
                    studio_pids[pid] = self._is_studio(pid)
                if studio_pids[pid] and not api.user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE) & _WS_EX_TOOLWINDOW:
                    found.append(self._window(hwnd, pid))
            except Exception:  # noqa: BLE001 - never raise through a Win32 callback
                pass
            return True

        callback = api.enum_proc(visit)
        with _dpi_aware(api):
            api.user32.EnumWindows(callback, 0)
        return found

    def _is_studio(self, pid: int) -> bool:
        api = self._api
        handle = api.kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = ctypes.c_uint32(len(buffer))
            if not api.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return False
            return Path(buffer.value).name.lower() == STUDIO_IMAGE
        finally:
            api.kernel32.CloseHandle(handle)

    def _window(self, hwnd: int, pid: int) -> Window:
        api = self._api
        length = api.user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        api.user32.GetWindowTextW(hwnd, title, length + 1)
        minimized = bool(api.user32.IsIconic(hwnd))
        rect = _RECT()
        if minimized:
            # A minimized window sits at -32000; report the size it will have when restored.
            placement = _WINDOWPLACEMENT()
            placement.length = ctypes.sizeof(_WINDOWPLACEMENT)
            api.user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
            rect = placement.rcNormalPosition
        else:
            api.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return Window(
            hwnd=int(hwnd),
            pid=pid,
            title=title.value,
            left=rect.left,
            top=rect.top,
            width=rect.right - rect.left,
            height=rect.bottom - rect.top,
            minimized=minimized,
            visible=bool(api.user32.IsWindowVisible(hwnd)),
            enabled=bool(api.user32.IsWindowEnabled(hwnd)),
        )

    def foreground(self) -> int:
        return self._api.user32.GetForegroundWindow() or 0

    # capture
    def _dib(self, dc, width: int, height: int):
        """A top-down 32-bit DIB section and its pixel address; the caller deletes the bitmap."""
        info = _BITMAPINFO()
        header = info.bmiHeader
        header.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = -height  # negative: rows top to bottom
        header.biPlanes = 1
        header.biBitCount = 32
        bits = ctypes.c_void_p()
        bitmap = self._api.gdi32.CreateDIBSection(dc, ctypes.byref(info), 0, ctypes.byref(bits), None, 0)
        if not bitmap:
            raise StudioError(f"CreateDIBSection failed for {width}x{height}")
        if not bits.value:
            self._api.gdi32.DeleteObject(bitmap)
            raise StudioError(f"CreateDIBSection returned no pixels for {width}x{height}")
        return bitmap, bits.value

    def _memory_dc(self, stack: ExitStack, compatible_with=None):
        gdi32 = self._api.gdi32
        dc = gdi32.CreateCompatibleDC(compatible_with)
        if not dc:
            raise StudioError("CreateCompatibleDC failed")
        stack.callback(gdi32.DeleteDC, dc)
        return dc

    def _selected_dib(self, stack: ExitStack, dc, width: int, height: int):
        """A DIB section selected into `dc`; deselected, then deleted, when `stack` closes."""
        gdi32 = self._api.gdi32
        bitmap, bits = self._dib(dc, width, height)
        stack.callback(gdi32.DeleteObject, bitmap)
        previous = gdi32.SelectObject(dc, bitmap)
        stack.callback(gdi32.SelectObject, dc, previous)
        return bits

    def capture(self, hwnd: int) -> tuple[int, int, bytes]:
        """The whole window rectangle as top-down BGRA, drawn by the window itself."""
        api = self._api
        with _dpi_aware(api), ExitStack() as stack:
            if not api.user32.IsWindow(hwnd):
                raise StudioError(f"window {hwnd} no longer exists")
            if api.user32.IsHungAppWindow(hwnd):
                raise StudioError(f"window {hwnd} is not responding; try again later")
            rect = _RECT()
            api.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width, height = rect.right - rect.left, rect.bottom - rect.top
            if width <= 0 or height <= 0:
                raise StudioError(f"window {hwnd} has no area ({width}x{height})")
            screen_dc = api.user32.GetDC(None)
            if not screen_dc:
                raise StudioError("GetDC failed")
            stack.callback(api.user32.ReleaseDC, None, screen_dc)
            dc = self._memory_dc(stack, screen_dc)
            bits = self._selected_dib(stack, dc, width, height)
            if not api.user32.PrintWindow(hwnd, dc, _PW_RENDERFULLCONTENT):
                raise StudioError(f"PrintWindow failed for window {hwnd}")
            data = ctypes.string_at(bits, width * height * 4)
        return width, height, data

    def resize(self, width: int, height: int, bgra: bytes, new_width: int, new_height: int) -> bytes:
        """Downscale BGRA with GDI's HALFTONE StretchBlt, which averages source pixels."""
        gdi32 = self._api.gdi32
        with ExitStack() as stack:
            source_dc = self._memory_dc(stack)
            target_dc = self._memory_dc(stack)
            source_bits = self._selected_dib(stack, source_dc, width, height)
            target_bits = self._selected_dib(stack, target_dc, new_width, new_height)
            ctypes.memmove(source_bits, bgra, width * height * 4)
            gdi32.SetStretchBltMode(target_dc, _HALFTONE)
            gdi32.SetBrushOrgEx(target_dc, 0, 0, None)
            if not gdi32.StretchBlt(target_dc, 0, 0, new_width, new_height,
                                    source_dc, 0, 0, width, height, _SRCCOPY):
                raise StudioError("StretchBlt failed")
            return ctypes.string_at(target_bits, new_width * new_height * 4)

    # click
    def _class_name(self, hwnd: int) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        self._api.user32.GetClassNameW(hwnd, buffer, len(buffer))
        return buffer.value

    def _pid(self, hwnd: int) -> int:
        pid = ctypes.c_uint32()
        self._api.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def deepest_child(self, hwnd: int, pid: int, screen_x: int, screen_y: int) -> Target:
        """The deepest visible child under a screen point, and the point in its client area.

        `pid` is the process of the validated top-level window; a control of any other
        process is refused. `enabled` is false when any window in the chain is disabled.
        """
        api = self._api
        with _dpi_aware(api):
            chain = [hwnd]
            for _ in range(_MAX_CHILD_DEPTH):
                point = _POINT(screen_x, screen_y)
                api.user32.ScreenToClient(chain[-1], ctypes.byref(point))
                child = api.user32.ChildWindowFromPointEx(chain[-1], point, _CWP_SKIPINVISIBLE)
                if not child or child == chain[-1]:
                    break
                chain.append(int(child))
            target = chain[-1]
            if self._pid(target) != pid:
                raise StudioError("the control under the point belongs to another process")
            point = _POINT(screen_x, screen_y)
            api.user32.ScreenToClient(target, ctypes.byref(point))
            return Target(
                hwnd=target,
                client_x=point.x,
                client_y=point.y,
                class_trail=[self._class_name(window) for window in chain],
                enabled=all(api.user32.IsWindowEnabled(window) for window in chain),
            )

    def post_click(self, hwnd: int, x: int, y: int) -> None:
        """Post move, button down and button up at client (x, y); no focus, no cursor move."""
        api = self._api
        lparam = pack_lparam(x, y)
        for message, wparam in ((_WM_MOUSEMOVE, 0), (_WM_LBUTTONDOWN, _MK_LBUTTON), (_WM_LBUTTONUP, 0)):
            if not api.user32.PostMessageW(hwnd, message, wparam, lparam):
                raise StudioError(f"PostMessage failed (error {ctypes.get_last_error()})")
