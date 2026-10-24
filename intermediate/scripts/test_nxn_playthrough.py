#!/usr/bin/env python3
"""N=10 two-region Bend playthrough versus independent Python set/BFS model.

This verifies a 90-safe-cell cascade and terminal victory, not a GUI,
100x100 performance, arbitrary-size no-guess solver, or a formal proof.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_nxn_full_game import expected, source, FILES, GAME

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "minesweeper" / "nxn_playthrough.bend"


def check_oracle():
    wall = tuple(range(50, 60))
    first = (("click", 0),)
    won = first + (("click", 99),)
    assert expected(10, wall, first, 49) == 12  # Right-edge number 2.
    assert expected(10, wall, first, 99) == 0   # Bottom is still hidden.
    assert expected(10, wall, won, 99) == 110  # Won, open zero.
    assert expected(10, wall, won + (("click", 50),), 50) == 100
    assert expected(10, wall, first + (("mark", 99), ("click", 99)), 99) == 1



def check_bend_boundaries():
    """Exercise the actual Bend engine at intermediate and terminal states.

    The original demonstration checks only the final 110. These cases also
    compare flags, mine loss, first-click relocation and frozen terminal input.
    Each expected value comes from the independent Python set/BFS model.
    """
    wall = tuple(range(50, 60))
    cases = (
        (10, wall, (("click", 0),), 49, 12),
        (10, wall, (("click", 0), ("mark", 99), ("click", 99)), 99, 1),
        (10, wall, (("click", 0), ("mark", 99), ("click", 99),
                    ("mark", 99), ("click", 99)), 99, 110),
        (10, wall, (("click", 0), ("click", 50), ("click", 99)), 99, 200),
        (10, wall, (("click", 50),), 50, 11),
        (10, wall, (("click", 99), ("click", 0)), 0, 110),
        (10, wall, (("click", 0), ("click", 99), ("click", 50)), 50, 100),
    )
    # Additional 10x10 checkpoints: invalid input, flags, both flood regions,
    # first-click relocation and terminal input freezing. Fixed expectations
    # are independently checked by the set/BFS oracle before Bend execution.
    cases += (
        (10, wall, (("mark", 0), ("click", 0)), 49, 12),  # Freshの旗は無視
        (10, wall, (("click", 100), ("click", 0)), 49, 12),  # 初手の盤外100
        (10, wall, (("click", 127), ("click", 0)), 49, 12),  # 初手の余剰添字127
        (10, wall, (("click", 0), ("click", 0)), 49, 12),  # 二度目のクリック
        (10, wall, (("click", 0), ("mark", 49)), 49, 12),  # 公開済みマスへの旗
        (10, wall, (("click", 0), ("mark", 99)), 99, 1),  # 下側の安全マスへ旗
        (10, wall, (("click", 0), ("mark", 99), ("mark", 99)), 99, 0),  # 旗を二度切り替える
        (10, wall, (("click", 0), ("click", 99), ("mark", 50)), 50, 100),  # 勝利後の旗は無効
        (10, wall, (("click", 0), ("click", 50), ("mark", 99)), 99, 200),  # 敗北後の旗は無効
        (10, wall, (("click", 0), ("click", 50), ("click", 0)), 0, 210),  # 敗北後のクリックは無効
        (10, wall, (("click", 99),), 60, 12),  # 下側から開始・数字境界
        (10, wall, (("click", 99), ("mark", 0)), 0, 1),  # 下側から開始・上側に旗
        (10, wall, (("click", 99), ("click", 0)), 0, 110),  # 下側から開始・上側を公開
        (10, wall, (("click", 50),), 50, 11),  # 地雷初手の元位置
        (10, wall, (("click", 50), ("click", 50)), 50, 11),  # 地雷初手の再クリック
        (10, wall, (("click", 50), ("click", 0)), 0, 200),  # 地雷移動先への二手目
        (10, wall, (("click", 0), ("mark", 100), ("click", 99)), 99, 110),  # 進行中の盤外旗
        (10, wall, (("click", 0), ("click", 100), ("click", 99)), 99, 110),  # 進行中の盤外クリック
        (10, wall, (("click", 0), ("click", 99), ("click", 127)), 99, 110),  # 勝利後の余剰添字
        (10, wall, (("click", 0),), 40, 12),  # 上側の左端数字
        (10, wall, (("click", 0),), 49, 12),  # 上側の右端数字
        (10, wall, (("click", 0),), 39, 10),  # 上側の0領域
        (10, wall, (("click", 99),), 90, 10),  # 下側の0領域
        (10, wall, (("click", 99),), 60, 12),  # 下側の左端数字
    )
    for n, mines, operations, probe, value in cases:
        assert expected(n, mines, operations, probe) == value
    checks = tuple((n, mines, operations, probe)
                   for n, mines, operations, probe, _ in cases)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name in FILES:
            (directory / name).write_bytes((GAME / name).read_bytes())
        program = directory / "check_playthrough_boundaries.bend"
        program.write_text(source(checks), encoding="utf-8")
        for args in (("bend", str(program), "--check-only"),
                     ("bend", str(program))):
            result = subprocess.run(
                args, cwd=directory, capture_output=True, text=True,
                timeout=360, env=dict(os.environ, BEND_NO_TELEMETRY="1"),
            )
            if result.returncode:
                raise AssertionError(f"{args}: {result.stdout}\\n{result.stderr}")
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(
                    f"Expected {len(checks)} Bend/Python matches: {result.stdout}"
                )
    print(f"PASS {len(checks)} N=10 Bend/Python boundary traces")


def main():
    check_oracle()
    check_bend_boundaries()
    for args in (("bend", str(DEMO), "--check-only"), ("bend", str(DEMO))):
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                timeout=360,
                                env=dict(os.environ, BEND_NO_TELEMETRY="1"))
        if result.returncode:
            raise AssertionError(f"{args}: {result.stdout}\\n{result.stderr}")
        if len(args) == 2 and result.stdout.strip().splitlines()[-1] != "110":
            raise AssertionError(f"10x10 playthrough must win with 110: {result.stdout}")
    print("PASS N=10 mine-wall playthrough: 50+40 safe cells, victory 110")


if __name__ == "__main__":
    main()
