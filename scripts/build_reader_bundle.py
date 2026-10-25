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
    "34_mine_mask_law.bend",
    "35_string_fields.bend", "36_map_missing.bend",
    "37_u32_dimension.bend",
    "38_list_sort.bend",     "39_array_to_list.bend",     "40_list_map.bend",
    "board_index.bend", "42_module_board.bend",
    "43_target_hello.bend", "44_message_boundary.bend",
    "45_binary_file.bend", "46_elapsed_clock.bend",
    "47_tcp_loopback.bend", "48_udp_loopback.bend",
    "49_map_update_delete.bend", "50_set_from_list.bend",
    "51_atomic_counter.bend", "52_pair_exists.bend",
    "53_chan_poll.bend",
)

# Runnable 4x4 replay lesson and its exact relative-import dependencies.
# This is a game engine example, not a solution to the book exercises.
INTERMEDIATE_GAME_FILES = (
    "game.bend", "board.bend", "board4.bend", "flood.bend",
    "session.bend", "start.bend", "cli_replay.bend", "gui.bend",
    "public_solver.bend", "public_two_corners.bend",
    "noguess_generator.bend", "cli_save.bend",
    # Three small, import-closed N x N public-information learning modules.
    "nxn_geometry.bend", "nxn_neighbors.bend", "nxn_zero_inference.bend",
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
初稿は執筆途中です。GUI、操作列の保存・復元、4×4・地雷2個限定の
「運ゲー無し」盤面生成を含みます。
ただしGUI実機確認、GUI保存、対話CLI、任意サイズの盤面生成は未完成です。

公式ガイド: https://github.com/bendlang/bend/blob/main/guide/GUIDE.md

例: bend examples/01_set.bend
4×4盤面のCLIリプレイ実習（対話入力ではなく引数を一括指定）:
bend examples/minesweeper/cli_replay.bend c0 f1 c1
操作 c番号=左クリック、f番号=旗、r=リセット。
初期地雷マスク33は固定で、表示する盤面には隠れた地雷位置を出しません。

別の起動でも同じCLI盤面へ戻るため、現在のディレクトリへ操作履歴を保存:
bend examples/minesweeper/cli_save.bend save c0 f1
bend examples/minesweeper/cli_save.bend load
保存形式はBEND2-SAVE-1|c0|f1|ENDで、破損した形式は拒否します。
GUIの状態全体を保存する機能ではありません。

公開済みの数字だけで確実にクリアできる候補を生成（4×4・地雷2個・左上開始限定）:
bend examples/minesweeper/noguess_generator.bend
期待結果: mines=40960;moves=0,12,14
\nN×Nの公開数字0から安全候補を探す（2〜100、左上0番の実習）:\nbend examples/minesweeper/nxn_neighbors.bend\nbend examples/minesweeper/nxn_zero_inference.bend\nどちらも期待結果は3。近傍列挙と確定安全候補の個数を区別します。\nこれは一般の連立ソルバーや運ゲー無し生成器ではありません。\n生成器は真の地雷配置を持ちますが、推論器へは公開数字しか渡しません。

4×4マインスイーパーのGUIをネイティブビルドして起動:
bend examples/minesweeper/gui.bend -o minesweeper
./minesweeper
左クリックで公開、右クリックで旗、Rでリセット、Escで終了。
Linuxではlibx11-dev等の環境依存ライブラリが必要です。
GUIのBend型検査・ネイティブコンパイル・純粋な座標処理はCI検査済みですが、
実際のデスクトップ環境でのウィンドウ操作・見た目は別途確認してください。

07_gui_hello.bend はウィンドウ表示が可能な環境が必要です。
証明例: bend examples/04_flag_laws.bend --verdict
帰納法: bend examples/33_nat_induction.bend --verdict
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

    game_dir = ROOT / "intermediate/minesweeper" if track == "intermediate" else None
    game_paths = tuple(game_dir / name for name in INTERMEDIATE_GAME_FILES) if game_dir else ()
    for path in (pdf, ROOT / "LICENSE", *(examples_dir / name for name in example_names), *game_paths):
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
    for path in game_paths:
        entries["examples/minesweeper/" + path.name] = path.read_bytes()

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
