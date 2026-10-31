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
APP = ROOT / "minesweeper" / "nxn_gui_app_store.bend"
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
    prototype = STATUS_APP.read_text(encoding="utf-8")
    assert "App.run(~State" in prototype
    assert "Feedback.save_report(model)" in prototype
    assert "after_load(model, recovery)" in prototype
    assert "mark1(img, color)" in prototype
    source = APP.read_text(encoding="utf-8")
    assert TITLE in source
    assert "History.Model" in source and "Store.save(model)" in source
    assert "Store.load()" in source and "History.pointer(model" in source
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



# Verification-only visible S/L outcome: assert an actual gutter pixel changes.
STATUS_APP = ROOT / "minesweeper" / "nxn_gui_status_app.bend"

def status_pixel(wid):
    p = subprocess.run(("import", "-window", wid, "png:-"),
                       capture_output=True, timeout=20)
    if p.returncode:
        raise AssertionError(p.stderr.decode(errors="replace"))
    image = Image.open(BytesIO(p.stdout)).convert("RGB")
    image.load()
    assert image.width >= 416 and image.height >= 32
    return image.getpixel((400, 16))

def await_status(wid, former, timeout=15):
    limit = time.monotonic() + timeout
    while time.monotonic() < limit:
        latest = status_pixel(wid)
        if latest != former:
            return latest
        time.sleep(0.2)
    raise AssertionError("GUI did not render a distinct S/L result marker")

def await_status_color(wid, expected, timeout=15):
    # Mouse clicks can clear the marker before the next key event is handled.
    # Wait for the exact target RGB, not merely a change from a stale color.
    until = time.monotonic() + timeout
    last = None
    while time.monotonic() < until:
        last = status_pixel(wid)
        if last == expected:
            return last
        time.sleep(0.2)
    raise AssertionError(f"GUI marker never reached {expected}: last={last}")


def verify_status_app(tmp, output):
    # Verify the *meaning* of all four colors, not just four distinct pixels.
    # Each S/L outcome must leave the playable 10x10 image unchanged.
    colors = {
        "load-failed": (255, 165, 0),  # amber
        "save-ok": (0, 255, 0),        # green
        "load-ok": (0, 0, 255),        # blue
        "save-failed": (255, 0, 0),    # red
    }
    work = Path(tmp) / "status-run"
    work.mkdir()
    binary = work / "nxn_status_gui"
    run("bend", str(STATUS_APP), "-o", str(binary), timeout=240)
    save = work / "minesweeper_nxn_save.txt"
    assert not save.exists()
    with (output / "status_stdout.log").open("wb") as logfile:
        process = subprocess.Popen((str(binary),), cwd=work,
                                   stdout=logfile, stderr=subprocess.STDOUT)
        try:
            wid = find_window(process)
            initial = status_pixel(wid)
            assert initial == (0, 0, 0), f"Fresh gutter is not blank: {initial}"
            fresh_board = shot(wid, output / "status_00_fresh.png")

            def check_board(label):
                current = shot(wid, output / f"status_{label}.png")
                if distinct(current, fresh_board):
                    raise AssertionError(f"{label}: S/L notification modified game cells")

            press(wid, "l")
            failed_load = await_status(wid, initial)
            assert failed_load == colors["load-failed"], failed_load
            assert not save.exists() and process.poll() is None
            check_board("01_missing_load")

            # A right press before the first left click is a public no-op.
            # It clears the notification without generating any mine layout.
            click(wid, 16, 16, 3)
            cleared = await_status(wid, failed_load)
            assert cleared == initial, "Mouse press did not clear notice"
            check_board("02_cleared")

            press(wid, "s")
            saved = await_status(wid, cleared)
            assert saved == colors["save-ok"], saved
            assert save.is_file()
            assert save.read_text(encoding="utf-8") == (
                f"BEND2-GUI-1|{SEED}|1|END"
            ), "S wrote an unexpected public history"
            check_board("03_saved")

            press(wid, "l")
            loaded = await_status(wid, saved)
            assert loaded == colors["load-ok"], loaded
            check_board("04_loaded")

            press(wid, "r")
            assert await_status(wid, loaded) == initial
            check_board("05_reset")

            save.unlink()
            save.mkdir()
            press(wid, "s")
            failed_save = await_status(wid, initial)
            assert failed_save == colors["save-failed"], failed_save
            assert process.poll() is None and save.is_dir()
            assert not list(save.iterdir()), "Failed save modified the directory"
            check_board("06_failed_save")

            # A blank board would not detect an accidental reset. Exercise
            # failed S/L again after opening a real cell, then verify that a
            # successful save and reload restores that same revealed board.
            click(wid, 16, 16, 1)
            opened_board = await_screen(
                wid, fresh_board, output / "status_07_opened.png", True
            )
            await_status_color(wid, initial)

            def check_opened_board(label):
                current = shot(wid, output / f"status_{label}.png")
                if distinct(current, opened_board):
                    raise AssertionError(f"{label}: S/L changed revealed cells")

            press(wid, "l")  # directory at the save path: read failure
            await_status_color(wid, colors["load-failed"])
            assert process.poll() is None and save.is_dir()
            check_opened_board("08_failed_load_revealed")

            press(wid, "s")  # same directory: write failure
            await_status_color(wid, colors["save-failed"])
            assert process.poll() is None and save.is_dir()
            assert not list(save.iterdir())
            check_opened_board("09_failed_save_revealed")

            save.rmdir()
            press(wid, "s")
            await_status_color(wid, colors["save-ok"])
            # The earlier R discarded the pre-first-click right press (1).
            # This save must contain only the subsequent left press (0).
            observed_history = save.read_text(encoding="utf-8")
            assert observed_history == f"BEND2-GUI-1|{SEED}|0|END", (
                f"Reset failed to discard old inputs: {observed_history!r}"
            )
            check_opened_board("10_saved_revealed")

            press(wid, "r")
            await_status_color(wid, initial)
            check_board("11_reset_after_reveal")
            press(wid, "l")
            await_status_color(wid, colors["load-ok"])
            check_opened_board("12_restored_revealed")

            # A corrupted transcript with a valid prefix must not partially
            # replay that prefix over the already revealed live board.
            original_save = save.read_bytes()
            malformed = [
                ("valid_prefix_bad_code", f"BEND2-GUI-1|{SEED}|0|200|END"),
                ("valid_prefix_extra_end", f"BEND2-GUI-1|{SEED}|0|END|END"),
                ("missing_end", f"BEND2-GUI-1|{SEED}|0"),
                ("oversized", f"BEND2-GUI-1|{SEED}|0|END" + "X" * 4097),
            ]
            for label, bad_payload in malformed:
                click(wid, 400, 400, 1)  # outside the game and marker
                await_status_color(wid, initial)
                check_opened_board(f"13_clear_{label}")
                save.write_text(bad_payload, encoding="ascii")
                press(wid, "l")
                await_status_color(wid, colors["load-failed"])
                assert save.read_text(encoding="ascii") == bad_payload
                assert process.poll() is None
                check_opened_board(f"14_rejected_{label}")

            # A rejected load must not poison a subsequent valid recovery.
            click(wid, 400, 400, 1)
            await_status_color(wid, initial)
            save.write_bytes(original_save)
            press(wid, "l")
            await_status_color(wid, colors["load-ok"])
            assert save.read_bytes() == original_save
            check_opened_board("15_recovered_after_rejections")

            press(wid, "Escape")
            process.wait(timeout=15)
            assert process.returncode == 0
            print("PASS X11 S/L exact amber/green/blue/red pixels, "
                  "fresh/revealed board preservation, directory failures "
                  "public-history restore and 4 malformed-file rejections", flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

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
            process = subprocess.Popen((str(binary),), cwd=tmp,
                                       stdout=logfile, stderr=subprocess.STDOUT)
            try:
                wid = find_window(process)
                fresh = shot(wid, output / "00_fresh.png")
                # L on first launch must preserve Fresh and keep the process alive.
                assert not (Path(tmp) / "minesweeper_nxn_save.txt").exists()
                press(wid, "l")
                time.sleep(0.3)
                if process.poll() is not None:
                    raise AssertionError("Missing save file terminated GUI")
                if distinct(fresh, shot(wid, output / "00_missing_file_ignored.png")):
                    raise AssertionError("Missing save changed the GUI")
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
                flagged = await_screen(wid, opened, output / "03_flagged.png", True)
                print("PASS right-click visibly flags a hidden tile", flush=True)
                press(wid, "s")
                save = Path(tmp) / "minesweeper_nxn_save.txt"
                # The pre-first right click is a valid public no-op, retained in history.
                expected = f"BEND2-GUI-1|{SEED}|1|0|{2 * index + 1}|END"
                until = time.monotonic() + 15
                observed = None
                while time.monotonic() < until:
                    if save.is_file():
                        observed = save.read_text()
                        if observed == expected:
                            break
                    if process.poll() is not None:
                        raise AssertionError("GUI exited while saving history")
                    time.sleep(0.1)
                if observed != expected:
                    raise AssertionError(
                        f"S key save mismatch: expected={expected!r}, observed={observed!r}")
                press(wid, "r")
                await_screen(wid, fresh, output / "04_reset.png", False)
                print("PASS reset restores initial screen", flush=True)
                press(wid, "l")
                await_screen(wid, flagged, output / "05_loaded.png", False)
                print("PASS L key restores identical visible game", flush=True)
                press(wid, "r")
                await_screen(wid, fresh, output / "06_reset_again.png", False)
                save.write_text("BEND2-GUI-1|20261029|200|END")
                press(wid, "l")
                await_screen(wid, fresh, output / "07_corrupt_ignored.png", False)
                print("PASS corrupt transcript leaves current GUI untouched", flush=True)
                # A directory at the save path prevents overwrite. S must
                # leave the current game alive, with no partial file.
                save.unlink()
                save.mkdir()
                press(wid, "s")
                time.sleep(0.3)
                if process.poll() is not None:
                    raise AssertionError("Failed save terminated GUI")
                if not save.is_dir() or list(save.iterdir()):
                    raise AssertionError("Failed save modified directory")
                if distinct(fresh, shot(wid, output / "07_write_failed_ignored.png")):
                    raise AssertionError("Failed save altered current board")
                save.rmdir()
                save.write_text(expected)
                press(wid, "Escape")
                process.wait(timeout=15)
                if process.returncode != 0:
                    raise AssertionError(f"Escape exit code: {process.returncode}")
                print("PASS Escape exits the native X11 application", flush=True)
                # Restart in the same working directory: only the on-disk
                # public replay may carry state across processes.
                second = subprocess.Popen((str(binary),), cwd=tmp,
                                          stdout=logfile, stderr=subprocess.STDOUT)
                try:
                    wid2 = find_window(second)
                    second_fresh = shot(wid2, output / "08_restart_fresh.png")
                    if distinct(second_fresh, fresh):
                        raise AssertionError("Restart should begin Fresh before L")
                    press(wid2, "l")
                    await_screen(wid2, flagged, output / "09_restart_loaded.png", False)
                    press(wid2, "Escape")
                    second.wait(timeout=15)
                    if second.returncode != 0:
                        raise AssertionError(f"Restart exit code: {second.returncode}")
                    print("PASS X11 restart + L replays saved public inputs", flush=True)
                finally:
                    if second.poll() is None:
                        second.terminate()
                        second.wait(timeout=5)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)

        verify_status_app(tmp, output)


if __name__ == "__main__":
    main()
