#!/usr/bin/env python3
"""Build minimal, deterministic learner ZIPs with solutions and maintainer files excluded.

Usage:
  python3 scripts/build_reader_bundle.py intro
  python3 scripts/build_reader_bundle.py intermediate
"""
from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STAMP = (2026, 1, 1, 0, 0, 0)

# Worked examples; finished Life/game reference solutions are excluded.
INTRO_EXAMPLES = (
    "01_hello.bend", "02_arithmetic.bend", "04_array.bend",
    "09_parallel_tree.bend", "10_gpu_tree.bend",
    "11_rule_proofs.bend", "12_affine_probe_INVALID.bend",
    "13_status_adt.bend", "14_list_basics.bend",
    "15_closure.bend", "16_template.bend",
    "17_numbers_strings.bend", "18_module_math.bend",
    "19_module_main.bend", "21_monadic_maybe.bend",
    "24_proof_induction.bend", "27_match_basics.bend",
    "28_data_types.bend", "29_higher_order.bend",
    "30_monad_explicit.bend", "module_math.bend",
)
INTERMEDIATE_EXAMPLES = (
    "01_set.bend", "02_map.bend", "03_list.bend",
    "04_flag_laws.bend", "05_marking.bend",
    "06_parallel.bend", "07_gui_hello.bend",
    "08_args.bend", "09_minesweeper_status.bend",
    "10_board_neighbors.bend", "11_random_io.bend",
    "12_file_write.bend", "13_file_read.bend", "14_local_inference.bend",
    "15_string_parse.bend", "16_map_set_api.bend",
    "17_list_pipeline.bend", "18_array_mutations.bend",
    "19_environment.bend", "20_process_run.bend", "21_io_fork.bend",
    "22_result_and_game.bend",
    "23_cell_hit_test.bend",
    "24_bool_proofs.bend", "25_either_case.bend",
    "26_audio_open.bend", "27_tcp_connect.bend",
    "28_chan_roundtrip.bend",
    "29_io_within.bend", "30_array_clone.bend",
    "31_image_quadrants.bend", "32_mouse_events.bend",
    "33_nat_induction.bend",
)

def readme(track: str) -> str:
    if track == "intro":
        return """# Bend 2 入門 — 学習用セット

このフォルダのPDFを読み、examples/ のサンプルを動かしてください。
Bend 2 の導入方法は公式ガイドを参照してください:
https://github.com/bendlang/bend/blob/main/guide/GUIDE.md

まず bend examples/01_hello.bend を実行します。
12_affine_probe_INVALID.bend は失敗を観察する専用例です。

ライフゲームの完成版や演習の参考実装はこのZIPには入りません。
必要なときだけリポジトリの src/ を参照してください:
https://github.com/Nasu726/bend2-intro-with-life/tree/main/src

原稿・CI・編集用資料もZIPには含めていません。
ライセンスは同梱のLICENSEを参照してください。
"""
    return """# Bend 2を使いこなす — 学習用セット（執筆途中）

PDFを読み、examples/ 内のコードを実行してください。
初稿は執筆途中です。完成版マインスイーパーや
「運ゲー無し」盤面生成はまだ収録していません。

公式ガイド: https://github.com/bendlang/bend/blob/main/guide/GUIDE.md

例: bend examples/01_set.bend
07_gui_hello.bend はウィンドウ表示が可能な環境が必要です。
証明例: bend examples/04_flag_laws.bend --verdict
（Leanのインストールが別途必要です）

進捗・参考実装はリポジトリを参照してください:
https://github.com/Nasu726/bend2-intro-with-life/tree/feat/intermediate-minesweeper-textbook/intermediate

このZIPは学習用です。リポジトリ全体の複製ではありません。
ライセンスは同梱のLICENSEを参照してください。
"""

def build(track: str, outdir: Path) -> Path:
    if track == "intro":
        pdf = ROOT / "ライフゲームで学ぶ_はじめてのBend2.pdf"
        examples_dir = ROOT / "src"
        example_names = INTRO_EXAMPLES
        output = "bend2-intro-reader.zip"
    else:
        pdf = ROOT / "intermediate/Bend2を使いこなす_プレビュー.pdf"
        examples_dir = ROOT / "intermediate/src"
        example_names = INTERMEDIATE_EXAMPLES
        output = "bend2-intermediate-reader-preview.zip"

    for path in (pdf, ROOT / "LICENSE", *(examples_dir / name for name in example_names)):
        if not path.is_file():
            raise FileNotFoundError("Required learner file missing: " + str(path))
    root_name = "bend2-" + ("intro" if track == "intro" else "intermediate") + "-reader"
    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / output
    entries = {
        "README.md": readme(track).encode("utf-8"),
        "LICENSE": (ROOT / "LICENSE").read_bytes(),
        "textbook.pdf": pdf.read_bytes(),
    }
    for name in example_names:
        entries["examples/" + name] = (examples_dir / name).read_bytes()

    # Strict allowlist prevents shipping tests, solutions, TeX and maintainer docs.
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in sorted(entries):
            info = zipfile.ZipInfo(root_name + "/" + rel, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, entries[rel], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"Created {target} with {len(entries)} files ({target.stat().st_size:,} bytes)")
    return target

def main():
    p = argparse.ArgumentParser()
    p.add_argument("track", choices=("intro", "intermediate"))
    p.add_argument("--output-dir", type=Path, default=ROOT / "reader-packages")
    args = p.parse_args()
    build(args.track, args.output_dir)

if __name__ == "__main__":
    main()
