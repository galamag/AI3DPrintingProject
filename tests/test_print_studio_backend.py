"""print_mcp.studio.Win32Backend against a fake user32, gdi32 and kernel32.

The fake records whether each call ran under per-monitor DPI awareness, tracks every GDI
handle, and refuses functions missing from studio._FUNCTIONS, so a function the backend
uses without a signature fails these tests.
"""
from __future__ import annotations

import ctypes
import os
from types import SimpleNamespace

import pytest

from print_mcp import studio
from print_mcp.studio import StudioError, Win32Backend

AWARE = ctypes.c_void_p(-4).value
UNAWARE = 0x11
STOCK_BITMAP = 0xDEAD
WS_EX_TOOLWINDOW = 0x80
STUDIO = r"C:\Program Files\Bambu Studio\bambu-studio.exe"


class FakeWin32:
    def __init__(self):
        self.context = UNAWARE
        self.fail = set()
        self.hung = set()
        self.calls = []
        self.windows, self.top_level, self.children = {}, [], {}
        self.images = {10: STUDIO, 20: r"C:\Windows\explorer.exe"}
        self.live, self.selected, self.buffers = {}, {}, {}
        self.next_handle = 0x1000
        self.posted = []
        self.foreground = 500

    def add(self, hwnd, parent=None, pid=10, title="cube - BambuStudio", rect=(-7, -7, 393, 293),
            visible=True, enabled=True, iconic=False, exstyle=0x100, cls="wxWindowNR"):
        self.windows[hwnd] = dict(pid=pid, title=title, rect=rect, visible=visible, enabled=enabled,
                                  iconic=iconic, exstyle=exstyle, cls=cls)
        if parent is None:
            self.top_level.append(hwnd)
        else:
            self.children.setdefault(parent, []).append(hwnd)

    def api(self):
        return SimpleNamespace(
            user32=FakeLibrary(self, "user32"),
            gdi32=FakeLibrary(self, "gdi32"),
            kernel32=FakeLibrary(self, "kernel32"),
            enum_proc=lambda function: function,
        )

    def calls_of(self, name):
        return [aware for called, aware in self.calls if called == name]

    def _handle(self, kind):
        self.next_handle += 1
        self.live[self.next_handle] = kind
        return self.next_handle

    # user32
    def SetThreadDpiAwarenessContext(self, context):
        if "SetThreadDpiAwarenessContext" in self.fail:
            return None
        previous, self.context = self.context, context.value
        return previous

    def EnumWindows(self, callback, lparam):
        for hwnd in self.top_level:
            if not callback(hwnd, lparam):
                break
        return 1

    def GetWindowThreadProcessId(self, hwnd, pid):
        pid._obj.value = self.windows[hwnd]["pid"]
        return 1

    def IsWindow(self, hwnd):
        return int(hwnd in self.windows)

    def IsWindowVisible(self, hwnd):
        return int(self.windows[hwnd]["visible"])

    def IsWindowEnabled(self, hwnd):
        return int(self.windows[hwnd]["enabled"])

    def IsIconic(self, hwnd):
        return int(self.windows[hwnd]["iconic"])

    def IsHungAppWindow(self, hwnd):
        return int(hwnd in self.hung)

    def GetWindowTextLengthW(self, hwnd):
        return len(self.windows[hwnd]["title"])

    def GetWindowTextW(self, hwnd, buffer, size):
        buffer.value = self.windows[hwnd]["title"][:size - 1]
        return len(buffer.value)

    def GetClassNameW(self, hwnd, buffer, size):
        buffer.value = self.windows[hwnd]["cls"][:size - 1]
        return len(buffer.value)

    def GetWindowRect(self, hwnd, rect):
        rect._obj.left, rect._obj.top, rect._obj.right, rect._obj.bottom = self.windows[hwnd]["rect"]
        return 1

    def GetWindowPlacement(self, hwnd, placement):
        normal = placement._obj.rcNormalPosition
        normal.left, normal.top, normal.right, normal.bottom = self.windows[hwnd]["rect"]
        return 1

    def GetWindowLongPtrW(self, hwnd, index):
        return self.windows[hwnd]["exstyle"] if index == -20 else 0

    def GetForegroundWindow(self):
        return self.foreground

    def GetDC(self, hwnd):
        return 0 if "GetDC" in self.fail else self._handle("screen dc")

    def ReleaseDC(self, hwnd, dc):
        self.live.pop(dc)
        return 1

    def PrintWindow(self, hwnd, dc, flags):
        if "PrintWindow" in self.fail:
            return 0
        width, height, buffer = self.buffers[self.selected[dc]]
        ctypes.memset(buffer, 0x40, width * height * 4)
        return 1

    def ScreenToClient(self, hwnd, point):
        left, top = self.windows[hwnd]["rect"][:2]
        point._obj.x -= left
        point._obj.y -= top
        return 1

    def ChildWindowFromPointEx(self, parent, point, flags):
        left, top, right, bottom = self.windows[parent]["rect"]
        x, y = point.x + left, point.y + top
        for child in self.children.get(parent, []):
            spec = self.windows[child]
            if flags & 1 and not spec["visible"] or flags & 2 and not spec["enabled"]:
                continue
            c_left, c_top, c_right, c_bottom = spec["rect"]
            if c_left <= x < c_right and c_top <= y < c_bottom:
                return child
        return parent if left <= x < right and top <= y < bottom else 0

    def PostMessageW(self, hwnd, message, wparam, lparam):
        self.posted.append((hwnd, message, wparam, lparam))
        return 1

    # gdi32
    def CreateCompatibleDC(self, dc):
        return 0 if "CreateCompatibleDC" in self.fail else self._handle("dc")

    def CreateDIBSection(self, dc, info, usage, bits, section, offset):
        if "CreateDIBSection" in self.fail:
            return 0
        header = info._obj.bmiHeader
        width, height = header.biWidth, -header.biHeight
        buffer = ctypes.create_string_buffer(width * height * 4)
        handle = self._handle("bitmap")
        self.buffers[handle] = (width, height, buffer)
        bits._obj.value = ctypes.addressof(buffer)
        return handle

    def SelectObject(self, dc, obj):
        previous = self.selected.get(dc, STOCK_BITMAP)
        self.selected[dc] = obj
        return previous

    def DeleteObject(self, obj):
        assert obj not in self.selected.values(), "a bitmap must be deselected before deletion"
        self.live.pop(obj)
        return 1

    def DeleteDC(self, dc):
        self.selected.pop(dc, None)
        self.live.pop(dc)
        return 1

    def SetStretchBltMode(self, dc, mode):
        return 1

    def SetBrushOrgEx(self, dc, x, y, point):
        return 1

    def StretchBlt(self, target, tx, ty, tw, th, source, sx, sy, sw, sh, rop):
        if "StretchBlt" in self.fail:
            return 0
        width, height, buffer = self.buffers[self.selected[target]]
        ctypes.memset(buffer, 0x7F, width * height * 4)
        return 1

    # kernel32
    def OpenProcess(self, access, inherit, pid):
        return 9000 + pid if pid in self.images else 0

    def QueryFullProcessImageNameW(self, handle, flags, buffer, size):
        buffer.value = self.images[handle - 9000]
        return 1

    def CloseHandle(self, handle):
        return 1


class FakeLibrary:
    def __init__(self, world, name):
        self._world, self._name = world, name

    def __getattr__(self, function):
        if function not in studio._FUNCTIONS[self._name]:
            raise AttributeError(f"{self._name}.{function} is used without a signature in studio._FUNCTIONS")
        implementation = getattr(self._world, function)

        def call(*args):
            self._world.calls.append((function, self._world.context == AWARE))
            return implementation(*args)

        return call


@pytest.fixture
def world():
    fake = FakeWin32()
    fake.add(1)                                            # main window, 400x300 at (-7, -7)
    fake.add(2, parent=1, rect=(13, 13, 213, 63), cls="wxTabButton")
    fake.add(3, parent=2, rect=(23, 23, 103, 53), cls="wxStaticText")
    return fake


def _backend(world):
    return Win32Backend(api=world.api())


# --- windows ------------------------------------------------------------------


def test_windows_lists_studio_windows_with_their_state(world):
    world.add(4, title="Send print job", rect=(100, 100, 1000, 800), enabled=True, cls="#32770")
    world.add(5, pid=20, title="Explorer")
    world.windows[1]["enabled"] = False
    windows = {w.hwnd: w for w in _backend(world).windows()}
    assert sorted(windows) == [1, 4]
    assert windows[1].enabled is False
    assert (windows[1].left, windows[1].top, windows[1].width, windows[1].height) == (-7, -7, 400, 300)
    assert windows[4].title == "Send print job"


def test_tool_windows_are_left_out(world):
    world.add(6, title="panel", rect=(0, 0, 600, 400), exstyle=0x100 | WS_EX_TOOLWINDOW)
    assert [w.hwnd for w in _backend(world).windows()] == [1]


def test_minimized_window_reports_its_restored_size(world):
    world.windows[1]["iconic"] = True
    (window,) = _backend(world).windows()
    assert window.minimized is True
    assert (window.width, window.height) == (400, 300)


# --- DPI awareness ------------------------------------------------------------


def test_windows_runs_dpi_aware(world):
    _backend(world).windows()
    assert world.calls_of("EnumWindows") == [True]
    assert world.calls_of("GetWindowRect") and all(world.calls_of("GetWindowRect"))
    assert world.context == UNAWARE, "the previous DPI context must be restored"


def test_capture_runs_dpi_aware(world):
    _backend(world).capture(1)
    assert world.calls_of("GetWindowRect") == [True]
    assert world.calls_of("PrintWindow") == [True]
    assert world.context == UNAWARE


def test_deepest_child_runs_dpi_aware(world):
    _backend(world).deepest_child(1, 10, 50, 30)
    assert world.calls_of("ScreenToClient") and all(world.calls_of("ScreenToClient"))
    assert world.calls_of("ChildWindowFromPointEx") and all(world.calls_of("ChildWindowFromPointEx"))
    assert world.context == UNAWARE


def test_failed_dpi_awareness_is_an_error(world):
    world.fail.add("SetThreadDpiAwarenessContext")
    backend = _backend(world)
    for call in (backend.windows, lambda: backend.capture(1), lambda: backend.deepest_child(1, 10, 50, 30)):
        with pytest.raises(StudioError, match="DPI"):
            call()


# --- capture ------------------------------------------------------------------


def test_capture_returns_the_window_pixels_and_frees_everything(world):
    width, height, data = _backend(world).capture(1)
    assert (width, height) == (400, 300)
    assert data == b"\x40" * (400 * 300 * 4)
    assert world.live == {}


@pytest.mark.parametrize("failing", ["GetDC", "CreateCompatibleDC", "CreateDIBSection", "PrintWindow"])
def test_capture_failures_free_everything(world, failing):
    world.fail.add(failing)
    with pytest.raises(StudioError):
        _backend(world).capture(1)
    assert world.live == {}, f"GDI handles leaked after {failing} failed"


def test_hung_window_is_not_captured(world):
    world.hung.add(1)
    with pytest.raises(StudioError, match="not responding"):
        _backend(world).capture(1)
    assert world.calls_of("PrintWindow") == []
    assert world.live == {}


def test_resize_frees_everything(world):
    data = _backend(world).resize(40, 30, bytes(40 * 30 * 4), 20, 15)
    assert data == b"\x7f" * (20 * 15 * 4)
    assert world.live == {}


@pytest.mark.parametrize("failing", ["CreateCompatibleDC", "CreateDIBSection", "StretchBlt"])
def test_resize_failures_free_everything(world, failing):
    world.fail.add(failing)
    with pytest.raises(StudioError):
        _backend(world).resize(40, 30, bytes(40 * 30 * 4), 20, 15)
    assert world.live == {}, f"GDI handles leaked after {failing} failed"


# --- click target -------------------------------------------------------------


def test_deepest_child_descends_to_the_control(world):
    target = _backend(world).deepest_child(1, 10, 50, 30)
    assert target.hwnd == 3
    assert target.class_trail == ["wxWindowNR", "wxTabButton", "wxStaticText"]
    assert (target.client_x, target.client_y) == (27, 7)
    assert target.enabled is True


def test_a_disabled_control_in_the_chain_is_reported(world):
    world.windows[2]["enabled"] = False
    target = _backend(world).deepest_child(1, 10, 50, 30)
    assert target.enabled is False
    assert target.hwnd == 3, "disabled windows are not skipped, so the refusal can see them"


def test_a_disabled_top_level_window_is_reported(world):
    world.windows[1]["enabled"] = False
    assert _backend(world).deepest_child(1, 10, 50, 30).enabled is False


def test_child_of_another_process_is_refused(world):
    world.windows[3]["pid"] = 20
    with pytest.raises(StudioError, match="another process"):
        _backend(world).deepest_child(1, 10, 50, 30)


def test_the_validated_pid_is_used(world):
    with pytest.raises(StudioError, match="another process"):
        _backend(world).deepest_child(1, 99, 50, 30)


def test_post_click_sends_move_down_up(world):
    _backend(world).post_click(3, -3, 5)
    lparam = (5 << 16) | 0xFFFD
    assert world.posted == [(3, 0x0200, 0, lparam), (3, 0x0201, 1, lparam), (3, 0x0202, 0, lparam)]


# --- real signatures ------------------------------------------------------------


@pytest.mark.skipif(os.name != "nt", reason="needs the Windows DLLs")
def test_every_backend_function_has_a_signature():
    api = studio._api()
    for library, names in studio._FUNCTIONS.items():
        for name in names:
            function = getattr(getattr(api, library), name)
            assert function.argtypes is not None, f"{library}.{name} has no argtypes"
            assert function.restype is api.signatures[library][name][0], f"{library}.{name} restype"
    for name in ("GetForegroundWindow", "ChildWindowFromPointEx", "GetDC", "SetThreadDpiAwarenessContext"):
        assert getattr(api.user32, name).restype is ctypes.c_void_p, f"{name} must return a full pointer"
    for name in ("CreateCompatibleDC", "CreateDIBSection", "SelectObject"):
        assert getattr(api.gdi32, name).restype is ctypes.c_void_p, f"{name} must return a full pointer"
    assert api.user32.PostMessageW.argtypes[3] is ctypes.c_ssize_t
