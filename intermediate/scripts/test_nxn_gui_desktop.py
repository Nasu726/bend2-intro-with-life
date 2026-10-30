#!/usr/bin/env python3
"""Native X11 GUI smoke: real window, X11 input, and screenshot comparisons.

Requires xvfb-run, Bend, clang, xdotool, ImageMagick 'import', and Pillow.
This is virtual-display verification, NOT physical-device/GPU verification.
"""
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageChops
from test_nxn_lazy_game import placed

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "minesweeper" / "nxn_gui_app.bend"
SEED = 20261029
TITLE = "Minesweeper 10x10"


def run(*args, timeout=20):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"{args!r} exited {p.returncode}: {p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def target_for_flag():
    # Independent Python flood oracle: choose an unexposed tile for right-click.
    mines = placed(10, 10, SEED, 0)
    opened, pending = set(), [0]
    while pending:
        index = pending.pop()
        if index in opened or index in mines:
            continue
        opened.add(index)
        x, y = index % 10, index // 10
        neighbors = {
            ny * 10 + nx
            for ny in range(max(0, y - 1), min(10, y + 2))
            for nx in range(max(0, x - 1), min(10, x + 2))
            if nx != x or ny != y
        }
        if not neighbors.intersection(mines):
            pending.extend(neighbors - opened)
    hidden = set(range(100)) - opened
    if not hidden:
        raise AssertionError("Initial click unexpectedly exposed all squares")
    return max(hidden)


def preflight():
    assert TITLE in APP.read_text(encoding="utf-8")
    for n in (2, 3, 10):
        for first in (0, n * n - 1):
            for count in (0, n * n - 1):
                mines = placed(n, count, SEED, first)
                assert len(mines) == count and first not in mines
    index = target_for_flag()
    assert 0 < index < 100
    a = Image.new("RGB", (4, 4), "black")
    b = Image.new("RGB", (4, 4), "white")
    assert distinct(a, b) and not distinct(a, a)
    print(f"PASS X11 smoke preflight, hidden flag target {index}", flush=True)


def find_window(process, timeout=60):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if process.poll() is not None:
            raise AssertionError(f"Bend GUI exited before opening: {process.returncode}")
        p = subprocess.run(("xdotool", "search", "--onlyvisible", "--name", TITLE),
                           capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.split()[0]
        time.sleep(0.3)
    raise TimeoutError("No X11 Minesweeper 10x10 window appeared")


def shot(wid, filename):
    p = subprocess.run(("import", "-window", wid, "png:-"),
                       capture_output=True, timeout=20)
    if p.returncode:
        raise AssertionError("X11 screenshot: " + p.stderr.decode(errors="replace"))
    img = Image.open(BytesIO(p.stdout)).convert("RGB")
    img.load()
    if img.width < 320 or img.height < 320:
        raise AssertionError(f"Unexpected GUI dimensions: {img.size}")
    img.save(filename)
    return img.crop((0, 0, 320, 320))


def distinct(a, b):
    return ImageChops.difference(a, b).getbbox() is not None


def await_screen(wid, baseline, filename, difference, timeout=35):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        image = shot(wid, filename)
        if distinct(image, baseline) == difference:
            return image
        time.sleep(0.4)
    raise AssertionError("GUI pixels did not reach the requested state")


def click(wid, x, y, button):
    run("xdotool", "mousemove", "--window", wid, str(x), str(y))
    run("xdotool", "click", str(button))


def press(wid, key):
    run("xdotool", "windowfocus", wid)
    run("xdotool", "key", "--clearmodifiers", key)



# The session app remains verification-only until packaged sources are synced.
SESSION_APP = ROOT / "minesweeper" / "nxn_gui_session_app.bend"
SESSION_SAVE = "minesweeper_nxn_save.txt"


def until_payload(path, expected, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.read_text(encoding="ascii") == expected:
            return
        time.sleep(0.2)
    raise AssertionError("S key did not write expected public GUI replay")


def await_equal(wid, expected, filename, timeout=35):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = shot(wid, filename)
        if not distinct(current, expected):
            return
        time.sleep(0.4)
    raise AssertionError("GUI did not restore expected saved pixels")


def close_gui(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def verify_session_native(output, work):
    """Exercise actual X11 S/L keys, disk replay, restart and corruption fallback."""
    binary = work / "nxn_gui_session"
    run("bend", str(SESSION_APP), "-o", str(binary), timeout=240)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise AssertionError("Bend did not create executable session GUI")
    save = work / SESSION_SAVE
    assert not save.exists()
    index = target_for_flag()
    expected_text = f"BEND2-GUI-1|{SEED}|0|{2 * index + 1}|END"
    with (output / "session_native_stdout.log").open("wb") as logfile:
        process = subprocess.Popen((str(binary),), cwd=work,
                                   stdout=logfile, stderr=subprocess.STDOUT)
        try:
            wid = find_window(process)
            fresh = shot(wid, output / "10_session_fresh.png")
            click(wid, 16, 16, 1)
            opened = await_screen(wid, fresh, output / "11_session_open.png", True)
            click(wid, (index % 10) * 32 + 16, (index // 10) * 32 + 16, 3)
            flagged = await_screen(wid, opened, output / "12_session_flag.png", True)
            press(wid, "s")
            until_payload(save, expected_text)
            press(wid, "r")
            await_equal(wid, fresh, output / "13_session_reset.png")
            press(wid, "l")
            await_equal(wid, flagged, output / "14_session_loaded.png")
            press(wid, "Escape")
            process.wait(timeout=15)
            assert process.returncode == 0, "Session GUI did not exit after Esc"
        finally:
            close_gui(process)
    with (output / "session_restart_stdout.log").open("wb") as logfile:
        process = subprocess.Popen((str(binary),), cwd=work,
                                   stdout=logfile, stderr=subprocess.STDOUT)
        try:
            wid = find_window(process)
            await_equal(wid, fresh, output / "15_session_restarted.png")
            press(wid, "l")
            await_equal(wid, flagged, output / "16_session_restart_loaded.png")
            press(wid, "r")
            await_equal(wid, fresh, output / "17_session_restart_reset.png")
            save.write_text(f"BEND2-GUI-2|{SEED}|0|END", encoding="ascii")
            press(wid, "l")
            time.sleep(0.6)
            await_equal(wid, fresh, output / "18_session_corrupt_rejected.png")
            assert process.poll() is None, "Corrupt save closed the GUI"
            press(wid, "Escape")
            process.wait(timeout=15)
            assert process.returncode == 0, "Session GUI restart did not exit"
        finally:
            close_gui(process)
    print("PASS native X11 S/L File replay, reset, restart, corrupt rejection", flush=True)


def main():
    preflight()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_desktop.py [--static-only]")
    if not os.environ.get("DISPLAY"):
        raise RuntimeError("Use xvfb-run -a to provide DISPLAY")
    for tool in ("bend", "clang", "xdotool", "import"):
        if not shutil.which(tool):
            raise RuntimeError(f"Missing executable {tool}")
    with tempfile.TemporaryDirectory(prefix="bend-x11-gui-") as tmp:
        binary = Path(tmp) / "nxn_minesweeper"
        run("bend", str(APP), "-o", str(binary), timeout=240)
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise AssertionError("Bend did not create an executable GUI")
        output = Path(os.environ.get("GUI_SMOKE_SCREENSHOTS", tmp))
        output.mkdir(parents=True, exist_ok=True)
        with (output / "native_stdout.log").open("wb") as logfile:
            process = subprocess.Popen((str(binary),), cwd=ROOT.parent,
                                       stdout=logfile, stderr=subprocess.STDOUT)
            try:
                wid = find_window(process)
                fresh = shot(wid, output / "00_fresh.png")
                click(wid, 400, 400, 1)  # padding: must not open any cell
                click(wid, 16, 16, 3)   # first right click: must not generate mines
                time.sleep(0.8)
                if distinct(fresh, shot(wid, output / "01_ignored.png")):
                    raise AssertionError("Invalid/pre-first-click input modified screen")
                click(wid, 16, 16, 1)
                opened = await_screen(wid, fresh, output / "02_opened.png", True)
                print("PASS left-click visibly reveals a safe first cell", flush=True)
                index = target_for_flag()
                click(wid, (index % 10) * 32 + 16, (index // 10) * 32 + 16, 3)
                await_screen(wid, opened, output / "03_flagged.png", True)
                print("PASS right-click visibly flags a hidden tile", flush=True)
                press(wid, "r")
                await_screen(wid, fresh, output / "04_reset.png", False)
                print("PASS reset restores initial screen", flush=True)
                press(wid, "Escape")
                process.wait(timeout=15)
                if process.returncode != 0:
                    raise AssertionError(f"Escape exit code: {process.returncode}")
                print("PASS Escape exits the native X11 application", flush=True)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)

        verify_session_native(output, Path(tmp))


if __name__ == "__main__":
    main()
