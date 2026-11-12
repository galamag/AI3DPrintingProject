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
import os
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from .paths import resolve_allowed, studio_exe
from .png import encode_png

STUDIO_IMAGE = "bambu-studio.exe"
MIN_WINDOW_PX = 200
OPEN_SUFFIXES = (".3mf", ".stl", ".step", ".stp", ".obj")
MIN_SCALE, MAX_SCALE = 0.1, 1.0

# Wait after posting a click before reading the foreground window again.
_SETTLE_S = 0.5
# Poll interval while waiting for a launched Bambu Studio to show its window.
_POLL_S = 0.5

_SW_SHOWNOACTIVATE = 4


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

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


# --- window choice ----------------------------------------------------------------


def _backend(backend):
    return backend if backend is not None else Win32Backend()


def list_windows(backend=None) -> list[Window]:
    """Visible Bambu Studio windows with a title and at least 200x200 px.

    Tooltips, menus and hidden helper windows of the process are left out. A minimized
    window keeps its restored size and is marked `minimized`.
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
        f"hwnd {w.hwnd}: {w.title!r}" + (" (minimized)" if w.minimized else "") for w in windows
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


def capture_window(
    hwnd: int | None = None,
    title_contains: str | None = None,
    scale: float = 1.0,
    crop: tuple[int, int, int, int] | None = None,
    backend=None,
) -> tuple[bytes, dict]:
    """PNG of a Bambu Studio window, even when other windows cover it.

    `crop` is (left, top, right, bottom) in window pixels and is applied before `scale`
    (0.1 to 1.0). The returned info explains how to map image pixels back to window pixels.
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
    if scale < 1.0:
        new_width, new_height = max(1, round(width * scale)), max(1, round(height * scale))
        bgra = backend.resize(width, height, bgra, new_width, new_height)
        width, height = new_width, new_height

    info = {
        "window": window.as_dict(),
        "scale": float(scale),
        "crop": list(box) if box is not None else None,
        "image_size": [width, height],
        "to_window_px": (
            "window_x = crop_left + image_x / scale, window_y = crop_top + image_y / scale "
            f"(crop_left={left}, crop_top={top}, scale={float(scale)}); "
            "studio_click takes window_x, window_y"
        ),
    }
    return encode_png(width, height, bgra), info


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
    backend=None,
) -> dict:
    """Post a left click at window pixel (x, y) without focusing the window or moving the mouse."""
    for name, value in (("x", x), ("y", y)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer, got {value!r}")
    backend = _backend(backend)
    window = pick_window(hwnd, title_contains, backend)
    _require_restored(window)
    if not (0 <= x < window.width and 0 <= y < window.height):
        raise ValueError(
            f"point ({x}, {y}) is outside the {window.width}x{window.height} window"
        )
    screen_x, screen_y = window.left + x, window.top + y
    before = backend.foreground()
    target, client_x, client_y, trail = backend.deepest_child(window.hwnd, screen_x, screen_y)
    backend.post_click(target, client_x, client_y)
    time.sleep(_SETTLE_S)
    after = backend.foreground()
    return {
        "window": window.as_dict(),
        "x": x,
        "y": y,
        "screen_x": screen_x,
        "screen_y": screen_y,
        "target_hwnd": target,
        "class_trail": trail,
        "client_x": client_x,
        "client_y": client_y,
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
    project = path.stem.casefold()  # "cube.gcode.3mf" -> "cube.gcode", as Bambu Studio titles it
    return [w for w in windows if _project_name(w.title).casefold() == project]


def open_in_studio(path: str | Path, timeout: float = 60.0, backend=None) -> dict:
    """Show a file in Bambu Studio: reuse a window already titled with it, else launch one.

    A launch asks Windows not to activate the new window (SW_SHOWNOACTIVATE); whether the
    foreground changed anyway is reported in `foreground_changed`.
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
        return {
            "path": str(resolved),
            "window": window.as_dict(),
            "launched": False,
            "pid": window.pid,
            "foreground_changed": False,
        }

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
    deadline = time.monotonic() + timeout
    while True:
        found = _windows_for(resolved, list_windows(backend))
        if found:
            break
        if time.monotonic() >= deadline:
            raise StudioError(
                f"Bambu Studio did not show a window for {resolved.name} within {timeout} s"
            )
        time.sleep(_POLL_S)
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
_CWP_SKIPINVISIBLE, _CWP_SKIPDISABLED = 0x0001, 0x0002
_PW_RENDERFULLCONTENT = 0x00000002
_DPI_PER_MONITOR_AWARE_V2 = -4
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_HALFTONE = 4
_SRCCOPY = 0x00CC0020
_MAX_CHILD_DEPTH = 16


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
    """user32, gdi32 and kernel32 with argtypes and restype set on every function used."""
    global _API
    if _API is not None:
        return _API
    if os.name != "nt":
        raise StudioError("the Bambu Studio window tools need Windows")
    HWND = HDC = HANDLE = HGDIOBJ = ctypes.c_void_p
    BOOL, INT, UINT, DWORD = ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint32
    WPARAM, LPARAM = ctypes.c_size_t, ctypes.c_ssize_t
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    enum_proc = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)

    def sign(library, name, restype, *argtypes):
        function = getattr(library, name)
        function.restype = restype
        function.argtypes = list(argtypes)

    sign(user32, "EnumWindows", BOOL, enum_proc, LPARAM)
    sign(user32, "GetWindowThreadProcessId", DWORD, HWND, ctypes.POINTER(DWORD))
    sign(user32, "IsWindow", BOOL, HWND)
    sign(user32, "IsWindowVisible", BOOL, HWND)
    sign(user32, "IsIconic", BOOL, HWND)
    sign(user32, "GetWindowTextLengthW", INT, HWND)
    sign(user32, "GetWindowTextW", INT, HWND, ctypes.c_wchar_p, INT)
    sign(user32, "GetClassNameW", INT, HWND, ctypes.c_wchar_p, INT)
    sign(user32, "GetWindowRect", BOOL, HWND, ctypes.POINTER(_RECT))
    sign(user32, "GetWindowPlacement", BOOL, HWND, ctypes.POINTER(_WINDOWPLACEMENT))
    sign(user32, "GetForegroundWindow", HWND)
    sign(user32, "PrintWindow", BOOL, HWND, HDC, UINT)
    sign(user32, "GetDC", HDC, HWND)
    sign(user32, "ReleaseDC", INT, HWND, HDC)
    sign(user32, "ScreenToClient", BOOL, HWND, ctypes.POINTER(_POINT))
    sign(user32, "ChildWindowFromPointEx", HWND, HWND, _POINT, UINT)
    sign(user32, "PostMessageW", BOOL, HWND, UINT, WPARAM, LPARAM)
    sign(user32, "SetThreadDpiAwarenessContext", ctypes.c_void_p, ctypes.c_void_p)
    sign(gdi32, "CreateCompatibleDC", HDC, HDC)
    sign(gdi32, "CreateDIBSection", HGDIOBJ, HDC, ctypes.POINTER(_BITMAPINFO), UINT,
         ctypes.POINTER(ctypes.c_void_p), HANDLE, DWORD)
    sign(gdi32, "SelectObject", HGDIOBJ, HDC, HGDIOBJ)
    sign(gdi32, "DeleteObject", BOOL, HGDIOBJ)
    sign(gdi32, "DeleteDC", BOOL, HDC)
    sign(gdi32, "SetStretchBltMode", INT, HDC, INT)
    sign(gdi32, "SetBrushOrgEx", BOOL, HDC, INT, INT, ctypes.c_void_p)
    sign(gdi32, "StretchBlt", BOOL, HDC, INT, INT, INT, INT, HDC, INT, INT, INT, INT, DWORD)
    sign(kernel32, "OpenProcess", HANDLE, DWORD, BOOL, DWORD)
    sign(kernel32, "QueryFullProcessImageNameW", BOOL, HANDLE, DWORD, ctypes.c_wchar_p,
         ctypes.POINTER(DWORD))
    sign(kernel32, "CloseHandle", BOOL, HANDLE)
    _API = SimpleNamespace(user32=user32, gdi32=gdi32, kernel32=kernel32, enum_proc=enum_proc)
    return _API


@contextmanager
def _dpi_aware(api):
    """Per-monitor DPI awareness for this thread, restored afterwards."""
    previous = api.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(_DPI_PER_MONITOR_AWARE_V2))
    try:
        yield
    finally:
        if previous:
            api.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(previous))


class Win32Backend:
    """The only place that calls Windows. No method focuses, moves or resizes a window."""

    def __init__(self) -> None:
        self._api = _api()

    # windows
    def windows(self) -> list[Window]:
        """Every top-level window owned by a bambu-studio.exe process, visible or not."""
        api = self._api
        studio_pids: dict[int, bool] = {}
        found: list[Window] = []

        def visit(hwnd, _lparam):
            try:
                pid = ctypes.c_uint32()
                api.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value not in studio_pids:
                    studio_pids[pid.value] = self._is_studio(pid.value)
                if studio_pids[pid.value]:
                    found.append(self._window(hwnd, pid.value))
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
        )

    def foreground(self) -> int:
        return self._api.user32.GetForegroundWindow() or 0

    # capture
    def _dib(self, dc, width: int, height: int):
        info = _BITMAPINFO()
        header = info.bmiHeader
        header.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = -height  # negative: rows top to bottom
        header.biPlanes = 1
        header.biBitCount = 32
        bits = ctypes.c_void_p()
        bitmap = self._api.gdi32.CreateDIBSection(dc, ctypes.byref(info), 0, ctypes.byref(bits), None, 0)
        if not bitmap or not bits.value:
            raise StudioError(f"CreateDIBSection failed for {width}x{height}")
        return bitmap, bits.value

    def capture(self, hwnd: int) -> tuple[int, int, bytes]:
        """The whole window rectangle as top-down BGRA, drawn by the window itself."""
        api = self._api
        with _dpi_aware(api):
            if not api.user32.IsWindow(hwnd):
                raise StudioError(f"window {hwnd} no longer exists")
            rect = _RECT()
            api.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width, height = rect.right - rect.left, rect.bottom - rect.top
            if width <= 0 or height <= 0:
                raise StudioError(f"window {hwnd} has no area ({width}x{height})")
            screen_dc = api.user32.GetDC(None)
            if not screen_dc:
                raise StudioError("GetDC failed")
            try:
                dc = api.gdi32.CreateCompatibleDC(screen_dc)
                bitmap, bits = self._dib(screen_dc, width, height)
                previous = api.gdi32.SelectObject(dc, bitmap)
                try:
                    if not api.user32.PrintWindow(hwnd, dc, _PW_RENDERFULLCONTENT):
                        raise StudioError(f"PrintWindow failed for window {hwnd}")
                    data = ctypes.string_at(bits, width * height * 4)
                finally:
                    api.gdi32.SelectObject(dc, previous)
                    api.gdi32.DeleteObject(bitmap)
                    api.gdi32.DeleteDC(dc)
            finally:
                api.user32.ReleaseDC(None, screen_dc)
        return width, height, data

    def resize(self, width: int, height: int, bgra: bytes, new_width: int, new_height: int) -> bytes:
        """Downscale BGRA with GDI's HALFTONE StretchBlt, which averages source pixels."""
        api = self._api
        source_dc = api.gdi32.CreateCompatibleDC(None)
        target_dc = api.gdi32.CreateCompatibleDC(None)
        try:
            source, source_bits = self._dib(source_dc, width, height)
            target, target_bits = self._dib(target_dc, new_width, new_height)
            ctypes.memmove(source_bits, bgra, width * height * 4)
            old_source = api.gdi32.SelectObject(source_dc, source)
            old_target = api.gdi32.SelectObject(target_dc, target)
            try:
                api.gdi32.SetStretchBltMode(target_dc, _HALFTONE)
                api.gdi32.SetBrushOrgEx(target_dc, 0, 0, None)
                if not api.gdi32.StretchBlt(target_dc, 0, 0, new_width, new_height,
                                            source_dc, 0, 0, width, height, _SRCCOPY):
                    raise StudioError("StretchBlt failed")
                return ctypes.string_at(target_bits, new_width * new_height * 4)
            finally:
                api.gdi32.SelectObject(source_dc, old_source)
                api.gdi32.SelectObject(target_dc, old_target)
                api.gdi32.DeleteObject(source)
                api.gdi32.DeleteObject(target)
        finally:
            api.gdi32.DeleteDC(source_dc)
            api.gdi32.DeleteDC(target_dc)

    # click
    def _class_name(self, hwnd: int) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        self._api.user32.GetClassNameW(hwnd, buffer, len(buffer))
        return buffer.value

    def _pid(self, hwnd: int) -> int:
        pid = ctypes.c_uint32()
        self._api.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def deepest_child(self, hwnd: int, screen_x: int, screen_y: int) -> tuple[int, int, int, list[str]]:
        """The deepest visible, enabled child under a screen point, and the point in its client area."""
        api = self._api
        with _dpi_aware(api):
            current, trail = hwnd, [self._class_name(hwnd)]
            for _ in range(_MAX_CHILD_DEPTH):
                point = _POINT(screen_x, screen_y)
                api.user32.ScreenToClient(current, ctypes.byref(point))
                child = api.user32.ChildWindowFromPointEx(
                    current, point, _CWP_SKIPINVISIBLE | _CWP_SKIPDISABLED
                )
                if not child or child == current:
                    break
                current = child
                trail.append(self._class_name(current))
            if self._pid(current) != self._pid(hwnd):
                raise StudioError("the control under the point belongs to another process")
            point = _POINT(screen_x, screen_y)
            api.user32.ScreenToClient(current, ctypes.byref(point))
        return int(current), point.x, point.y, trail

    def post_click(self, hwnd: int, x: int, y: int) -> None:
        """Post move, button down and button up at client (x, y); no focus, no cursor move."""
        api = self._api
        lparam = pack_lparam(x, y)
        for message, wparam in ((_WM_MOUSEMOVE, 0), (_WM_LBUTTONDOWN, _MK_LBUTTON), (_WM_LBUTTONUP, 0)):
            if not api.user32.PostMessageW(hwnd, message, wparam, lparam):
                raise StudioError(f"PostMessage failed (error {ctypes.get_last_error()})")
