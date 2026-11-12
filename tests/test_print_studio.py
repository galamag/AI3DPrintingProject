"""print_mcp.studio: window logic tested against a fake backend; nothing touches real windows."""
from __future__ import annotations

import subprocess

import pytest

from print_mcp import studio
from print_mcp.paths import PathNotAllowed
from print_mcp.studio import (
    StudioError,
    Target,
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


def _window(hwnd=1, title="cube.gcode - BambuStudio", **fields):
    values = dict(hwnd=hwnd, pid=10, title=title, left=-7, top=-7, width=W, height=H,
                  minimized=False)
    values.update(fields)
    return Window(**values)


class FakeBackend:
    def __init__(self, windows=(), foreground=(500,), target_enabled=True):
        self._windows = list(windows)
        self.calls = []
        self._foreground = list(foreground)
        self.target_enabled = target_enabled

    def windows(self):
        return list(self._windows)

    def capture(self, hwnd):
        self.calls.append(("capture", hwnd))
        window = next(w for w in self._windows if w.hwnd == hwnd)
        width, height = window.width, window.height
        if width * height > 200_000:
            return width, height, bytes(width * height * 4)
        return width, height, b"".join(_pixel(x, y) for y in range(height) for x in range(width))

    def resize(self, width, height, bgra, new_width, new_height):
        self.calls.append(("resize", width, height, new_width, new_height))
        return bytes(new_width * new_height * 4)

    def deepest_child(self, hwnd, pid, screen_x, screen_y):
        self.calls.append(("deepest_child", hwnd, pid, screen_x, screen_y))
        return Target(hwnd=hwnd + 1000, client_x=screen_x - 3, client_y=screen_y - 4,
                      class_trail=["wxWindowNR", "wxWindow"], enabled=self.target_enabled)

    def post_click(self, hwnd, x, y):
        self.calls.append(("post_click", hwnd, x, y))

    def foreground(self):
        return self._foreground.pop(0) if len(self._foreground) > 1 else self._foreground[0]


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    monkeypatch.setattr(studio, "_SETTLE_S", 0)
    monkeypatch.setattr(studio, "_POLL_S", 0.01)
    monkeypatch.setattr(studio, "_LAUNCHED", {})


# --- windows ------------------------------------------------------------------


def test_list_windows_filters_and_marks_minimized():
    backend = FakeBackend([
        _window(1, "cube.gcode - BambuStudio", width=2574, height=1406),
        _window(2, "", width=300, height=30),                     # tooltip
        _window(3, "Hidden", visible=False, width=800, height=600),
        _window(4, "Tip", width=150, height=100),                 # small popup
        _window(5, "   ", width=800, height=600),                 # blank title
        _window(6, "other - BambuStudio", minimized=True, width=1200, height=800),
        _window(7, "Send print job", enabled=True, width=900, height=700),  # a dialog stays listed
    ])
    windows = list_windows(backend)
    assert [w.hwnd for w in windows] == [1, 6, 7]
    assert [w.minimized for w in windows] == [False, True, False]


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
    backend = FakeBackend([_window()])
    data, info = capture_window(backend=backend)
    width, height, _, rows = read_png(data)
    assert (width, height) == (W, H)
    assert rows[0][:3] == bytes((0, 0, 0))
    assert info["image_size"] == [W, H]
    assert (info["requested_scale"], info["scale_x"], info["scale_y"]) == (1.0, 1.0, 1.0)
    assert info["scale_reduced"] is False
    assert info["crop"] is None
    assert info["window"]["hwnd"] == 1
    assert "window_x = crop_left + image_x / scale_x" in info["to_window_px"]
    assert "window_y = crop_top + image_y / scale_y" in info["to_window_px"]
    assert f"expected_width={W}" in info["click_hint"] and f"expected_height={H}" in info["click_hint"]
    assert info["warnings"] == []
    assert not any(call[0] == "resize" for call in backend.calls)


def test_capture_scaled():
    backend = FakeBackend([_window()])
    data, info = capture_window(scale=0.5, backend=backend)
    assert read_png(data)[:2] == (200, 150)
    assert info["image_size"] == [200, 150]
    assert (info["scale_x"], info["scale_y"]) == (0.5, 0.5)
    assert info["scale_reduced"] is False
    assert ("resize", W, H, 200, 150) in backend.calls


def test_scale_per_axis_comes_from_the_integer_size():
    backend = FakeBackend([_window(width=401, height=301)])
    _, info = capture_window(scale=0.5, backend=backend)
    width, height = info["image_size"]
    assert info["scale_x"] == width / 401
    assert info["scale_y"] == height / 301


@pytest.mark.parametrize(
    "width, height",
    [(2000, 300), (1200, 1000), (2574, 1406)],
)
def test_capture_is_capped_for_the_model_api(width, height):
    backend = FakeBackend([_window(width=width, height=height)])
    data, info = capture_window(scale=1.0, backend=backend)
    out_width, out_height = info["image_size"]
    assert read_png(data)[:2] == (out_width, out_height)
    assert max(out_width, out_height) <= 1568
    assert out_width * out_height <= 1_150_000
    assert info["scale_reduced"] is True
    assert info["scale_x"] == out_width / width and info["scale_y"] == out_height / height
    assert any("reduced" in warning for warning in info["warnings"])


def test_a_small_crop_at_scale_one_stays_unscaled():
    backend = FakeBackend([_window(width=2574, height=1406)])
    data, info = capture_window(crop=(0, 30, 700, 80), backend=backend)
    assert read_png(data)[:2] == (700, 50)
    assert (info["scale_x"], info["scale_y"]) == (1.0, 1.0)
    assert info["scale_reduced"] is False
    assert not any(call[0] == "resize" for call in backend.calls)


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


def test_capture_of_a_disabled_window_warns():
    _, info = capture_window(backend=FakeBackend([_window(enabled=False)]))
    assert any("disabled" in warning for warning in info["warnings"])


# --- click --------------------------------------------------------------------


def test_click_translates_window_pixels_to_screen():
    backend = FakeBackend([_window(left=-7, top=-7)], foreground=(500, 500))
    result = click_window(x=135, y=55, backend=backend)
    assert backend.calls == [
        ("deepest_child", 1, 10, 128, 48),
        ("post_click", 1001, 125, 44),
    ]
    assert result["class_trail"] == ["wxWindowNR", "wxWindow"]
    assert (result["client_x"], result["client_y"]) == (125, 44)
    assert result["foreground_before"] == 500
    assert result["foreground_after"] == 500
    assert result["foreground_changed"] is False
    assert result["window"]["hwnd"] == 1
    assert (result["window"]["width"], result["window"]["height"]) == (W, H)


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


def test_click_on_a_disabled_window_is_refused():
    backend = FakeBackend([_window(enabled=False)])
    with pytest.raises(StudioError, match="a dialog is open; list windows and pick the dialog"):
        click_window(x=10, y=10, backend=backend)
    assert backend.calls == []


def test_click_on_a_disabled_control_is_refused():
    backend = FakeBackend([_window()], target_enabled=False)
    with pytest.raises(StudioError, match="a dialog is open"):
        click_window(x=10, y=10, backend=backend)
    assert not any(call[0] == "post_click" for call in backend.calls)


@pytest.mark.parametrize("expected", [(W + 1, H), (W, H - 1)])
def test_click_refuses_a_changed_window_size(expected):
    backend = FakeBackend([_window()])
    with pytest.raises(StudioError, match="capture again"):
        click_window(x=10, y=10, expected_width=expected[0], expected_height=expected[1],
                     backend=backend)
    assert backend.calls == []


def test_click_with_the_expected_size():
    backend = FakeBackend([_window()])
    click_window(x=10, y=10, expected_width=W, expected_height=H, backend=backend)
    assert any(call[0] == "post_click" for call in backend.calls)


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


class FakeProcess:
    def __init__(self, pid, alive=True):
        self.pid, self.alive = pid, alive

    def poll(self):
        return None if self.alive else 0


class FakePopen:
    def __init__(self, backend=None, new_window=None):
        self.backend, self.new_window = backend, new_window
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.backend is not None and self.new_window is not None:
            self.backend._windows.append(self.new_window)
        return FakeProcess(777 + len(self.calls))


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
    assert result["pid"] == 778
    assert result["window"]["hwnd"] == 9
    assert result["foreground_changed"] is False


def test_open_times_out_with_the_pid(studio_install, sliced, monkeypatch):
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    with pytest.raises(StudioError, match=r"pid 778.*did not show"):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    assert len(popen.calls) == 1


def test_open_does_not_launch_twice_while_starting(studio_install, sliced, monkeypatch):
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    with pytest.raises(StudioError):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    with pytest.raises(StudioError, match="still starting"):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    assert len(popen.calls) == 1


def test_open_launches_again_after_the_process_ended(studio_install, sliced, monkeypatch):
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    with pytest.raises(StudioError):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    studio._LAUNCHED[sliced.resolve()].alive = False
    with pytest.raises(StudioError, match="did not show"):
        open_in_studio(sliced, timeout=0.1, backend=FakeBackend([]))
    assert len(popen.calls) == 2


def test_open_does_not_match_a_longer_project_name(studio_install, work_dir, monkeypatch):
    path = work_dir / "cube.3mf"
    path.write_bytes(b"zip")
    popen = FakePopen()
    monkeypatch.setattr(studio.subprocess, "Popen", popen)
    backend = FakeBackend([_window(6, "cube20-green - BambuStudio")])
    with pytest.raises(StudioError):
        open_in_studio(path, timeout=0.1, backend=backend)
    assert len(popen.calls) == 1, "a window for another project must not count as this file's"
