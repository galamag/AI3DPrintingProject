"""print_mcp.studio: window logic tested against a fake backend; nothing touches real windows."""
from __future__ import annotations

import subprocess

import pytest

from print_mcp import studio
from print_mcp.paths import PathNotAllowed
from print_mcp.studio import (
    StudioError,
    Window,
    capture_window,
    click_window,
    list_windows,
    open_in_studio,
    pack_lparam,
    pick_window,
)
from test_print_png import read_png

W, H = 400, 300


def _pixel(x, y):
    """BGRA of the fake window's pixel (x, y)."""
    return bytes((x % 256, y % 256, (x + y) % 256, 255))


def _image():
    return W, H, b"".join(_pixel(x, y) for y in range(H) for x in range(W))


def _window(hwnd=1, title="cube.gcode - BambuStudio", **fields):
    values = dict(hwnd=hwnd, pid=10, title=title, left=-7, top=-7, width=W, height=H,
                  minimized=False)
    values.update(fields)
    return Window(**values)


class FakeBackend:
    def __init__(self, windows=(), foreground=(500,)):
        self._windows = list(windows)
        self.calls = []
        self._foreground = list(foreground)

    def windows(self):
        return list(self._windows)

    def capture(self, hwnd):
        self.calls.append(("capture", hwnd))
        return _image()

    def resize(self, width, height, bgra, new_width, new_height):
        self.calls.append(("resize", width, height, new_width, new_height))
        out = bytearray()
        for y in range(new_height):
            source_y = y * height // new_height
            for x in range(new_width):
                start = (source_y * width + x * width // new_width) * 4
                out += bgra[start:start + 4]
        return bytes(out)

    def deepest_child(self, hwnd, screen_x, screen_y):
        self.calls.append(("deepest_child", hwnd, screen_x, screen_y))
        return hwnd + 1000, screen_x - 3, screen_y - 4, ["wxWindowNR", "wxWindow"]

    def post_click(self, hwnd, x, y):
        self.calls.append(("post_click", hwnd, x, y))

    def foreground(self):
        return self._foreground.pop(0) if len(self._foreground) > 1 else self._foreground[0]


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(studio, "_SETTLE_S", 0)
    monkeypatch.setattr(studio, "_POLL_S", 0.01)


# --- windows ------------------------------------------------------------------


def test_list_windows_filters_and_marks_minimized():
    backend = FakeBackend([
        _window(1, "cube.gcode - BambuStudio", width=2574, height=1406),
        _window(2, "", width=300, height=30),                     # tooltip
        _window(3, "Hidden", visible=False, width=800, height=600),
        _window(4, "Tip", width=150, height=100),                 # small popup
        _window(5, "   ", width=800, height=600),                 # blank title
        _window(6, "other - BambuStudio", minimized=True, width=1200, height=800),
    ])
    windows = list_windows(backend)
    assert [w.hwnd for w in windows] == [1, 6]
    assert [w.minimized for w in windows] == [False, True]


def test_pick_by_hwnd():
    backend = FakeBackend([_window(1), _window(2, "b - BambuStudio")])
    assert pick_window(hwnd=2, backend=backend).hwnd == 2


def test_pick_unknown_hwnd():
    backend = FakeBackend([_window(1)])
    with pytest.raises(StudioError, match="cube.gcode - BambuStudio"):
        pick_window(hwnd=99, backend=backend)


def test_pick_by_title_ignores_case():
    backend = FakeBackend([_window(1, "Cube.gcode - BambuStudio"), _window(2, "bracket - BambuStudio")])
    assert pick_window(title_contains="cube", backend=backend).hwnd == 1


def test_pick_by_title_ambiguous_or_missing():
    backend = FakeBackend([_window(1, "cube A - BambuStudio"), _window(2, "cube B - BambuStudio")])
    with pytest.raises(StudioError) as error:
        pick_window(title_contains="cube", backend=backend)
    assert "cube A - BambuStudio" in str(error.value) and "cube B - BambuStudio" in str(error.value)
    with pytest.raises(StudioError, match="cube A - BambuStudio"):
        pick_window(title_contains="bracket", backend=backend)


def test_pick_without_choice_needs_a_single_window():
    assert pick_window(backend=FakeBackend([_window(1)])).hwnd == 1
    backend = FakeBackend([_window(1, "a - BambuStudio"), _window(2, "b - BambuStudio")])
    with pytest.raises(StudioError, match="a - BambuStudio"):
        pick_window(backend=backend)


def test_not_running():
    with pytest.raises(StudioError, match="Bambu Studio is not running"):
        pick_window(backend=FakeBackend([]))


# --- capture ------------------------------------------------------------------


def test_capture_full_size():
    data, info = capture_window(backend=FakeBackend([_window()]))
    width, height, _, rows = read_png(data)
    assert (width, height) == (W, H)
    assert rows[0][:3] == bytes((0, 0, 0))
    assert info["image_size"] == [W, H]
    assert info["scale"] == 1.0
    assert info["crop"] is None
    assert info["window"]["hwnd"] == 1
    assert "window_x = crop_left + image_x / scale" in info["to_window_px"]


def test_capture_scaled():
    backend = FakeBackend([_window()])
    data, info = capture_window(scale=0.5, backend=backend)
    assert read_png(data)[:2] == (200, 150)
    assert info["image_size"] == [200, 150]
    assert ("resize", W, H, 200, 150) in backend.calls


def test_capture_cropped():
    data, info = capture_window(crop=(100, 50, 300, 250), backend=FakeBackend([_window()]))
    width, height, _, rows = read_png(data)
    assert (width, height) == (200, 200)
    blue, green, red, _ = _pixel(100, 50)
    assert rows[0][:3] == bytes((red, green, blue))
    blue, green, red, _ = _pixel(299, 249)
    assert rows[199][-3:] == bytes((red, green, blue))
    assert info["crop"] == [100, 50, 300, 250]


@pytest.mark.parametrize(
    "crop",
    [(100, 50, 100, 250), (100, 50, 300, 50), (-1, 0, 10, 10), (0, 0, W + 1, 10),
     (0, 0, 10, H + 1), (300, 0, 100, 10), (1, 2, 3)],
)
def test_bad_crop(crop):
    backend = FakeBackend([_window()])
    with pytest.raises(ValueError):
        capture_window(crop=crop, backend=backend)
    assert backend.calls == []


@pytest.mark.parametrize("scale", [0.05, 1.5, 0])
def test_bad_scale(scale):
    backend = FakeBackend([_window()])
    with pytest.raises(ValueError):
        capture_window(scale=scale, backend=backend)
    assert backend.calls == []


def test_capture_minimized():
    backend = FakeBackend([_window(minimized=True)])
    with pytest.raises(StudioError, match="minimized"):
        capture_window(backend=backend)
    assert backend.calls == []


# --- click --------------------------------------------------------------------


def test_click_translates_window_pixels_to_screen():
    backend = FakeBackend([_window(left=-7, top=-7)], foreground=(500, 500))
    result = click_window(x=135, y=55, backend=backend)
    assert backend.calls == [
        ("deepest_child", 1, 128, 48),
        ("post_click", 1001, 125, 44),
    ]
    assert result["class_trail"] == ["wxWindowNR", "wxWindow"]
    assert (result["client_x"], result["client_y"]) == (125, 44)
    assert result["foreground_before"] == 500
    assert result["foreground_after"] == 500
    assert result["foreground_changed"] is False
    assert result["window"]["hwnd"] == 1


def test_click_reports_a_foreground_change():
    backend = FakeBackend([_window()], foreground=(500, 1))
    assert click_window(x=10, y=10, backend=backend)["foreground_changed"] is True


@pytest.mark.parametrize("x, y", [(-1, 10), (W, 10), (10, -1), (10, H)])
def test_click_outside_the_window(x, y):
    backend = FakeBackend([_window()])
    with pytest.raises(ValueError):
        click_window(x=x, y=y, backend=backend)
    assert backend.calls == []


def test_click_minimized():
    backend = FakeBackend([_window(minimized=True)])
    with pytest.raises(StudioError, match="minimized"):
        click_window(x=10, y=10, backend=backend)
    assert backend.calls == []


def test_click_on_a_window_of_another_process():
    backend = FakeBackend([_window(1)])
    with pytest.raises(StudioError):
        click_window(x=10, y=10, hwnd=4242, backend=backend)
    assert backend.calls == []


def test_pack_lparam():
    assert pack_lparam(-3, 5) == (5 << 16) | 0xFFFD
    assert pack_lparam(10, -2) == (0xFFFE << 16) | 10
    with pytest.raises(ValueError):
        pack_lparam(70000, 5)
    with pytest.raises(ValueError):
        pack_lparam(5, -40000)


# --- open ---------------------------------------------------------------------


@pytest.fixture
def studio_install(tmp_path, monkeypatch):
    folder = tmp_path / "Bambu Studio"
    folder.mkdir()
    (folder / "bambu-studio.exe").write_bytes(b"")
    monkeypatch.setenv("BAMBU_STUDIO_DIR", str(folder))
    return folder


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("PRINT_MCP_WORK_DIR", str(work))
    return work


@pytest.fixture
def sliced(work_dir):
    path = work_dir / "срез с пробелом" / "cube.gcode.3mf"
    path.parent.mkdir()
    path.write_bytes(b"zip")
    return path


class FakePopen:
    def __init__(self, backend=None, new_window=None):
        self.backend, self.new_window = backend, new_window
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.backend is not None and self.new_window is not None:
            self.backend._windows.append(self.new_window)
        process = type("Process", (), {"pid": 777})()
        return process


def test_open_outside_roots(studio_install, work_dir, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "cube.3mf"
    outside.write_bytes(b"zip")
    with pytest.raises(PathNotAllowed):
        open_in_studio(outside, backend=FakeBackend([]))


def test_open_bad_suffix(studio_install, work_dir):
    path = work_dir / "notes.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        open_in_studio(path, backend=FakeBackend([]))


def test_open_missing_file(studio_install, work_dir):
    with pytest.raises(FileNotFoundError):
        open_in_studio(work_dir / "absent.3mf", backend=FakeBackend([]))


def test_open_finds_an_existing_window(studio_install, sliced, monkeypatch):
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    backend = FakeBackend([_window(5, "other - BambuStudio"), _window(6, "cube.gcode - BambuStudio")])
    result = open_in_studio(sliced, backend=backend)
    assert popen.calls == []
    assert result["launched"] is False
    assert result["window"]["hwnd"] == 6
    assert result["foreground_changed"] is False


def test_open_launches_and_waits_for_the_window(studio_install, sliced, monkeypatch):
    backend = FakeBackend([_window(5, "other - BambuStudio")], foreground=(500, 500))
    popen = FakePopen(backend, _window(9, "cube.gcode - BambuStudio"))
    monkeypatch.setattr(studio.subprocess, "Popen", popen)

    result = open_in_studio(sliced, timeout=5, backend=backend)

    (args, kwargs), = popen.calls
    assert args == [str(studio_install / "bambu-studio.exe"), str(sliced.resolve())]
    startupinfo = kwargs["startupinfo"]
    assert startupinfo.wShowWindow == 4
    assert startupinfo.dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert not kwargs.get("shell")
    assert result["launched"] is True
    assert result["window"]["hwnd"] == 9
    assert result["foreground_changed"] is False


def test_open_times_out(studio_install, sliced, monkeypatch):
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    with pytest.raises(StudioError, match="did not show"):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    assert len(popen.calls) == 1


def test_open_does_not_match_a_longer_project_name(studio_install, work_dir, monkeypatch):
    path = work_dir / "cube.3mf"
    path.write_bytes(b"zip")
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    backend = FakeBackend([_window(6, "cube20-green - BambuStudio")])
    with pytest.raises(StudioError):
        open_in_studio(path, timeout=0.1, backend=backend)
    assert len(popen.calls) == 1, "a window for another project must not count as this file's"
