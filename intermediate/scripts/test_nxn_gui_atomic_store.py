#!/usr/bin/env python3
"""Linux-only candidate GUI atomic save; does not alter the shipped GUI.

Bend writes a randomized same-directory temporary file and invokes GNU mv -fT
after File.write and File.close. This checks replacement and failure preservation,
not fsync, power-loss durability, or multi-process races.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
SOURCE = GAME / "nxn_gui_atomic_store.bend"
TARGET = "minesweeper_nxn_save.txt"
EXPECTED = b"BEND2-GUI-1|20261029|0|199|END"


def static():
    code = SOURCE.read_text(encoding="utf-8")
    for required in (
        'Process.run("/usr/bin/mv",', '["-fT", "--", temp, "minesweeper_nxn_save.txt"]',
        "File.close(file)", "File.write(file, text)", "IO.random_u32()",
        "History.valid_entries(chronological)", "cleanup_failed(model, temp)",
        "Store.payload(seed, chronological)",
    ):
        assert required in code, required
    assert 'File.open("minesweeper_nxn_save.txt", "w")' not in code
    assert "mines:" not in code and "IO.die(" not in code
    assert shutil.which("/usr/bin/mv"), "Linux GNU mv required"
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        src = base / "src"
        src.write_bytes(EXPECTED)
        dest = base / "dest"
        dest.mkdir()
        p = subprocess.run(("/usr/bin/mv", "-fT", "--", str(src), str(dest)),
                           capture_output=True, timeout=10)
        assert p.returncode != 0 and src.read_bytes() == EXPECTED
        assert dest.is_dir() and not list(dest.iterdir())
    print("PASS static atomic save contract and GNU mv -T guard", flush=True)


def bend_run(path, cwd, *, check=False):
    args = ["bend", str(path)] + (["--check-only"] if check else [])
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       timeout=240, env=dict(os.environ, BEND_NO_TELEMETRY="1"))
    if p.returncode:
        raise AssertionError(f"{args}: {p.returncode}\n{p.stdout}\n{p.stderr}")
    if not check:
        lines = p.stdout.strip().splitlines()
        assert lines and lines[-1] in {"0", "1"}, (p.stdout, p.stderr)
        return lines[-1]


def no_temp(work):
    leaked = list(work.glob(TARGET + ".tmp.*"))
    assert not leaked, f"Leaked temporary files: {leaked}"


def main():
    static()
    if sys.argv[1:] == ["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_atomic_store.py [--static-only]")
    with tempfile.TemporaryDirectory(prefix="bend-gui-atomic-") as td:
        work = Path(td)
        for file in GAME.glob("*.bend"):
            (work / file.name).write_bytes(file.read_bytes())
        entry = work / SOURCE.name
        bend_run(entry, work, check=True)
        target = work / TARGET

        target.write_bytes(b"OLD-CANONICAL-SAVE")
        assert bend_run(entry, work) == "1"
        assert target.read_bytes() == EXPECTED
        no_temp(work)

        target.unlink()
        assert bend_run(entry, work) == "1"
        assert target.read_bytes() == EXPECTED
        no_temp(work)

        target.unlink()
        target.mkdir()
        sentinel = target / "do-not-touch"
        sentinel.write_bytes(b"sentinel")
        assert bend_run(entry, work) == "0"
        assert target.is_dir() and sentinel.read_bytes() == b"sentinel"
        assert list(target.iterdir()) == [sentinel]
        no_temp(work)

        sentinel.unlink()
        target.rmdir()
        assert bend_run(entry, work) == "1"
        assert target.read_bytes() == EXPECTED
        no_temp(work)

        target.unlink()
        referent = work / "referent"
        referent.write_bytes(b"KEEP-REFERENT")
        target.symlink_to(referent)
        assert bend_run(entry, work) == "1"
        assert not target.is_symlink() and target.read_bytes() == EXPECTED
        assert referent.read_bytes() == b"KEEP-REFERENT"
        no_temp(work)
    print("PASS Bend atomic save: existing/fresh, directory failure, recovery, "
          "symlink isolation and temporary cleanup", flush=True)


if __name__ == "__main__":
    main()
