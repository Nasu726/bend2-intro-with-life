#!/usr/bin/env python3
"""Chapter 15-16 teaching exercises, against real Bend verifier in isolated copies.

Never mutate the distributed source. A failing verdict is evidence of rejection,
not proof of the intended error location; report the original output if needed.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "src"


def bend(path: Path, *arguments: str, allow_fail: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["bend", str(path), *arguments], cwd=ROOT.parent,
        env=dict(os.environ, BEND_NO_TELEMETRY="1"),
        capture_output=True, text=True, timeout=180,
    )
    if proc.returncode and not allow_fail:
        raise AssertionError(f"Bend failed {path.name} {arguments}:\n{proc.stdout}\n{proc.stderr}")
    return proc


def accepted(path: Path) -> None:
    bend(path, "--check-only")
    result = bend(path, "--verdict")
    if "ALL PROOFS CHECK" not in result.stdout + result.stderr:
        raise AssertionError(f"Expected verified proof for {path.name}:\n{result.stdout}\n{result.stderr}")


def rejected(path: Path) -> None:
    result = bend(path, "--verdict", allow_fail=True)
    output = result.stdout + result.stderr
    if "ALL PROOFS CHECK" in output:
        raise AssertionError(f"Invalid law/proof was accepted: {path.name}")
    if result.returncode == 0 and not output.strip():
        raise AssertionError(f"No evidence of rejected proof: {path.name}")


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise AssertionError(f"Exercise source changed: expected exactly one {old!r}")
    return source.replace(old, new, 1)


def verify() -> None:
    if not shutil.which("bend"):
        raise AssertionError("Bend is required; this is not a Python-only proof")
    flag = (SAMPLES / "04_flag_laws.bend").read_text(encoding="utf-8")
    nat = (SAMPLES / "33_nat_induction.bend").read_text(encoding="utf-8")
    addition = (
        "\nlaw hidden_is_marked:\n"
        "  {toggle(Hidden{}) == Marked{} : Cover}\n\n"
        "def hidden_is_marked():\n"
        "  {==}\n"
    )
    if "law hidden_is_marked" in flag:
        raise AssertionError("Already added exercise law to reader sample")
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        flag_verified = temp / "flag_verified.bend"
        flag_verified.write_text(flag + addition, encoding="utf-8")
        accepted(flag_verified)
        print("PASS chapter 15: added hidden_is_marked law and proof", flush=True)

        flag_mutant = temp / "flag_mutant.bend"
        flag_mutant.write_text(replace_once(
            flag + addition,
            "case Hidden{}:\n      Marked{}",
            "case Hidden{}:\n      Hidden{}",
        ), encoding="utf-8")
        rejected(flag_mutant)
        print("PASS chapter 15: invalid Hidden toggle does not pass verdict", flush=True)

        nat_changed = temp / "nat_changed.bend"
        nat_changed.write_text(replace_once(
            nat, "def main() -> U32:\n  0", "def main() -> U32:\n  1"
        ), encoding="utf-8")
        accepted(nat_changed)
        executed = bend(nat_changed).stdout.strip()
        if executed != "1":
            raise AssertionError(f"Changed main must print 1; got {executed!r}")
        print("PASS chapter 16: changing main output preserves universal law", flush=True)

        nat_unproved = temp / "nat_unproved.bend"
        nat_unproved.write_text(replace_once(
            nat,
            "      %times_zero(p) : {Nat.mul(p, 0n) == _ : Nat}\n",
            "",
        ), encoding="utf-8")
        rejected(nat_unproved)
        print("PASS chapter 16: removing induction hypothesis rejects proof", flush=True)


if __name__ == "__main__":
    verify()
