#!/usr/bin/env python3
"""Live Bend File IO integration test for versioned 4x4 command-history saves.

Run in a temporary directory: never writes a save file into the repository.
The test checks valid replay, corrupted data, unsupported format and input limits.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "minesweeper" / "cli_save.bend"
EXPECTED = "Playing\n2 F . .\n. . . .\n. . . .\n. . . ."


def main():
    with tempfile.TemporaryDirectory() as td:
        working = Path(td)
        savefile = working / "minesweeper_save.txt"

        def call(*args, succeeds=True):
            proc = subprocess.run(
                ["bend", str(ENTRY), *args], cwd=working,
                text=True, capture_output=True, timeout=180,
                env=dict(os.environ, BEND_NO_TELEMETRY="1")
            )
            assert (proc.returncode == 0) == succeeds, (
                args, proc.returncode, proc.stdout, proc.stderr)
            return proc.stdout.strip()

        call("load", succeeds=False)  # Missing file, not a fresh game.
        assert call("save", "c0", "f1") == "Saved minesweeper_save.txt"
        assert savefile.read_text() == "BEND2-SAVE-1|c0|f1|END"
        assert call("load") == EXPECTED
        call("save", "c16", succeeds=False)
        call("save", "f99", succeeds=False)
        call("save", "c0|r", succeeds=False)
        call("save", *(["c0"] * 65), succeeds=False)
        assert savefile.read_text() == "BEND2-SAVE-1|c0|f1|END"
        call("load", "c0", succeeds=False)

        bad_files = (
            "BEND2-SAVE-9|c0|END",  # Unsupported version.
            "BEND2-SAVE-1|c0|END|tail",  # Data after terminator.
            "BEND2-SAVE-1|c0|c16|END",  # Out-of-range command.
            "BEND2-SAVE-1|c0|f1",  # Missing terminator.
            "BEND2-SAVE-1|END",  # Empty history: save() refuses it too.
            "BEND2-SAVE-1|" + "r|" * 65 + "END",  # >64 legal commands.
            "BEND2-SAVE-1|END|" + "X" * 510,  # Oversized and malformed.
        )
        for bad in bad_files:
            savefile.write_text(bad)
            call("load", succeeds=False)

        assert call("save", "c0", "r") == "Saved minesweeper_save.txt"
        assert call("load") == "Fresh: first click with c0..c15"
        # Both directions must accept the same upper boundary.
        assert call("save", *(["r"] * 64)) == "Saved minesweeper_save.txt"
        assert savefile.read_text() == "BEND2-SAVE-1|" + "r|" * 64 + "END"
        assert call("load") == "Fresh: first click with c0..c15"
        call("save", *(["r"] * 65), succeeds=False)
        assert savefile.read_text() == "BEND2-SAVE-1|" + "r|" * 64 + "END"
    print("PASS CLI save/load: replay, malformed histories and 1..64 limit")


if __name__ == "__main__":
    main()
