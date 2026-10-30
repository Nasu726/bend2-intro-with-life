#!/usr/bin/env python3
"""Disk-backed GUI session replay; independent format and public-state oracle."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from test_nxn_gui_adapter import oracle

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minesweeper"
STORE = GAME / "nxn_gui_store.bend"
SEED = 20261029
FORMAT = f"BEND2-GUI-1|{SEED}|0|199|END"
SAVE = "minesweeper_nxn_save.txt"

PURE = [
    ("normal", FORMAT, 1),
    ("fresh", f"BEND2-GUI-1|{SEED}|END", 300),
    ("first", f"BEND2-GUI-1|{SEED}|0|END",
     oracle(10,10,SEED,((0,0,0),),99)),
    ("first-opened-zero", f"BEND2-GUI-1|{SEED}|0|END",
     oracle(10,10,SEED,((0,0,0),),0), 0),
    ("flag-toggle", f"BEND2-GUI-1|{SEED}|0|199|199|END", 0),
    ("before-first-flag", f"BEND2-GUI-1|{SEED}|199|0|END", 0),
    ("bad-header", f"BEND2-GUI-0|{SEED}|0|199|END", 600),
    ("bad-seed", "BEND2-GUI-1|nope|0|END", 600),
    ("missing-seed", "BEND2-GUI-1|", 600),
    ("no-end", f"BEND2-GUI-1|{SEED}|0", 600),
    ("middle-end", f"BEND2-GUI-1|{SEED}|END|0|END", 600),
    ("extra-end", f"BEND2-GUI-1|{SEED}|0|END|END", 600),
    ("bad-code", f"BEND2-GUI-1|{SEED}|200|END", 600),
    ("negative-code", f"BEND2-GUI-1|{SEED}|-1|END", 600),
    ("empty-code", f"BEND2-GUI-1|{SEED}|0||199|END", 600),
    ("trailing-data", FORMAT+"|junk", 600),
    ("too-long", FORMAT+"X"*4097, 600),
    ("too-many-commands", f"BEND2-GUI-1|{SEED}|"+"0|"*513+"END", 600),
]

def quote_bend(s):
    return '"' + s.replace("\\","\\\\").replace('"','\\"') + '"'

def pure_source(batch):
    out = [
        "import Base",
        "import ./nxn_gui_store.bend as Store",
        "import ./nxn_gui_history.bend as History",
        "def bool_u32(ok: Bool) -> U32:",
        "  match ok:",
        "    case True{}:",
        "      1",
        "    case False{}:",
        "      0",
        "",
    ]
    for i, item in enumerate(batch):
        _,data,want,*probe = item
        cell = probe[0] if probe else 99
        out += [
            f"def test_{i}() -> U32:",
            f"  bool_u32(U32.is_eq(History.recovered_snapshot(Store.deserialize({quote_bend(data)}), {cell}), {want}))",
            ""
        ]
    out += ["def main() -> U32:", "  ("+" + ".join(f"test_{i}()" for i in range(len(batch)))+" : U32)"]
    return "\n".join(out)+"\n"

WRITE = """import Base
import ./nxn_gui_store.bend as Store
import ./nxn_gui_history.bend as History
def main() -> IO(Unit):
  do IO<Unit>:
    state: History.Model <- Store.save(
      History.pointer(History.pointer(History.new(20261029),0,0,0),319,319,1))
    IO.print(U32.show(History.snapshot(state,99)))
"""

READ = """import Base
import ./nxn_gui_store.bend as Store
import ./nxn_gui_history.bend as History
def main() -> IO(Unit):
  do IO<Unit>:
    recovery: History.Recovery <- Store.load()
    IO.print(U32.show(History.recovered_snapshot(recovery,99)))
"""

SESSION_WRITE = """import Base
import ./nxn_gui_session.bend as Session
import ./nxn_gui_history.bend as History
def output(value: Maybe<History.Model>) -> U32:
  match value:
    case None{}:
      600
    case Some{model}:
      History.snapshot(model, 99)
def main() -> IO(Unit):
  do IO<Unit>:
    result: Maybe<History.Model> <- Session.tick(
      [Mouse{0, 0, 0, True{}}, Mouse{319, 319, 1, True{}},
       Key{115, True{}}], History.new(20261029))
    IO.print(U32.show(output(result)))
"""

SESSION_LOAD = """import Base
import ./nxn_gui_session.bend as Session
import ./nxn_gui_history.bend as History
def output(value: Maybe<History.Model>) -> U32:
  match value:
    case None{}:
      600
    case Some{model}:
      History.snapshot(model, 99)
def main() -> IO(Unit):
  do IO<Unit>:
    result: Maybe<History.Model> <- Session.tick(
      [Key{108, True{}}], History.new(20261029))
    IO.print(U32.show(output(result)))
"""

def static():
    src = STORE.read_text(encoding="utf-8")
    session = (GAME / "nxn_gui_session.bend").read_text(encoding="utf-8")
    app = (GAME / "nxn_gui_session_app.bend").read_text(encoding="utf-8")
    assert "App.run(~History.Model" in app
    assert "Session.view, Session.tick" in app
    assert "Store.save(model)" in session and "Store.load()" in session
    assert "History.pointer(model, x, y, button)" in session
    assert "History.reset(model)" in session
    for key in (115, 83, 108, 76):
        assert f"Key{{{key}, True{{}}}}" in session
    assert "BEND2-GUI-1|" in src
    assert "File.write(file, text)" in src and "File.read(file, 4097)" in src
    assert "History.valid_entries(chronological)" in src
    assert "512n" in src and "4096n" in src
    assert "History.Model{game, +newest_first, +seed}" in src
    assert "File.close(file)" in src
    assert "Words.has(" not in src and "mines:" not in src
    assert len(PURE)==18 and len(set(x[0] for x in PURE))==18
    assert PURE[0][2]==1 and PURE[1][2]==300 and PURE[11][2]==600
    # Independent canonical parser verifies every allowed 0..199.
    def reference(text):
        if len(text)>4096:
            return False
        parts=text.split("|")
        if len(parts)<3 or parts[0]!="BEND2-GUI-1" or parts[-1]!="END":
            return False
        try:
            seed=int(parts[1])
        except ValueError:
            return False
        return (0<=seed<2**32 and len(parts[2:-1])<=512 and
                all(s.isdecimal() and 0<=int(s)<200 for s in parts[2:-1]))
    for label,data,want,*probe in PURE:
        assert reference(data)==(want!=600),label
    print("PASS 18 canonical and rejected GUI File payloads",flush=True)

def bend_run(source_path, expected, cwd):
    env=dict(os.environ,BEND_NO_TELEMETRY="1")
    for cmd in (("bend",str(source_path),"--check-only"),
                ("bend",str(source_path))):
        proc=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,
                            env=env,timeout=700)
        if proc.returncode:
            raise AssertionError(f"{cmd} failed:\n{proc.stdout}\n{proc.stderr}")
        if len(cmd)==2 and proc.stdout.strip().splitlines()[-1]!=str(expected):
            raise AssertionError(f"{cmd}: expected {expected}; {proc.stdout!r}")

def main():
    static()
    if sys.argv[1:]==["--static-only"]:
        return
    if sys.argv[1:]:
        raise SystemExit("usage: test_nxn_gui_store.py [--static-only]")
    with tempfile.TemporaryDirectory() as tmp:
        work=Path(tmp)
        for file in GAME.glob("*.bend"):
            (work/file.name).write_bytes(file.read_bytes())
        for start in range(0,len(PURE),4):
            batch=PURE[start:start+4]
            path=work/f"gui_store_pure_{start}.bend"
            path.write_text(pure_source(batch),encoding="utf-8")
            bend_run(path,len(batch),work)
        writer=work/"gui_store_write.bend"
        writer.write_text(WRITE,encoding="utf-8")
        bend_run(writer,1,work)
        target=work/SAVE
        assert target.read_bytes()==FORMAT.encode("ascii")
        reader=work/"gui_store_read.bend"
        reader.write_text(READ,encoding="utf-8")
        bend_run(reader,1,work)
        for label,payload in [
            ("range",f"BEND2-GUI-1|{SEED}|200|END"),
            ("missing-end",f"BEND2-GUI-1|{SEED}|0"),
            ("unknown-version",f"BEND2-GUI-2|{SEED}|0|END"),
            ("truncated",FORMAT+"X"*4097),
        ]:
            target.write_text(payload,encoding="ascii")
            bend_run(reader,600,work)
        candidate = work / "nxn_gui_session_app.bend"
        checked = subprocess.run(("bend", str(candidate), "--check-only"), cwd=work,
                                 capture_output=True, text=True, timeout=240,
                                 env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        assert checked.returncode == 0, checked.stdout + checked.stderr
        session_writer = work / "gui_session_write.bend"
        session_writer.write_text(SESSION_WRITE, encoding="utf-8")
        bend_run(session_writer, 1, work)
        assert target.read_bytes() == FORMAT.encode("ascii")
        session_reader = work / "gui_session_load.bend"
        session_reader.write_text(SESSION_LOAD, encoding="utf-8")
        bend_run(session_reader, 1, work)
        target.write_text(f"BEND2-GUI-1|{SEED}|200|END", encoding="ascii")
        bend_run(session_reader, 0, work)
        print("PASS 18 Bend format cases, File I/O, 4 corrupt reloads, GUI S/L event wiring",flush=True)

if __name__=="__main__":
    main()
