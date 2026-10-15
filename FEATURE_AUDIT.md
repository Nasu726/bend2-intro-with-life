# Bend 2 基本機能監査（v1.1）

監査基準: [公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)、[公式README](https://github.com/bendlang/bend)、[Base](https://github.com/bendlang/bend/blob/main/bend2/base.bend)。2026-10-16時点のBend 2.0.36を対象とする。

「掲載済み」は本文・演習・ソースで取り上げたことを意味する。**Bend CLIで正常動作を確認したという意味ではない**。独立PythonテストはBendの型チェックや停止性の証明とは無関係。

| 仕様分野 | 対応 | サンプル / 実装段階 |
| --- | --- | --- |
| 関数、注釈、U32/Nat、基本演算 | 本文と例 | `02_arithmetic.bend`, `17_numbers_strings.bend` |
| ADT、constructor、match | 本文と例 | `13_cell_adt.bend` |
| List、再帰、停止性 | 本文と例 | `14_list_basics.bend` |
| Array、アフィン、+/-の量 | 本文と例 | `04_array.bend`, Life更新核, `12_...INVALID.bend` |
| クロージャと高階関数 | 本文と例 | `15_closure.bend` |
| テンプレート（~） | 本文と例 | `16_template.bend` |
| Kind / Type / Data / Quant | 本文と例 | `23_kinds.bend` |
| Bool/Cmp、F32、Char/String、bit | 本文と演習 | `bend base`で定義を参照。F32精度の証明は対象外 |
| Maybe、Result、モナドとdo | 本文と例 | `21_monadic_maybe.bend` |
| Map / Set | Mapは例、Setは課題 | `25_map_basics.bend`, `bend base Set` |
| モジュール / import / 構築 | 本文と例 | `18_module_math.bend`, `19_module_main.bend` |
| IO、File、args、エラー | 本文とFile例 | `20_io_fork.bend`, `26_file_write.bend`（上書き注意） |
| IOの並行性 / Channels | 本文と例 | `20_io_fork.bend` |
| 純粋なCPU並列 / GPU ! | 本文と独立例 | `09_parallel_tree.bend`, `10_gpu_tree.bend`。Life本体は未実装 |
| App / Image / Event | 本文と独立例 | `22_app_preview.bend`。GUI版Lifeは未実装 |
| ファイル以外の標準効果 / FFI | 本文と実験課題 | ネット、音声、プロセス、C/JS拡張は発展扱い |
| 法則、証明、帰納法、verdict | 本文と例 | `11_rule_proofs.bend`, `24_proof_induction.bend` |
| C / JS / mjs ターゲット、BendHub | 本文と実習手順 | publish実行は含めない |

## 既知の未完・未検証事項

1. Bendが制作環境に存在しないため、全`.bend`例の構文と型の最終確認は未実施。`make bend-check`を導入環境で実行する。
2. 8×8のLife完成版はPythonオラクル6件に対応するBendソースを用意済みだが、Bend CLIでの差分照合は未実施。`make check`で照合する。
3. 並列GPUのLife本体、ファイルからのパターン読込、可変サイズ、GUI版、盤面全体の形式証明は発展課題。
4. Set、ネットワーク、音声、独自FFI、BendHubについては概念とAPI調査課題を用意。全APIの実演・動作確認はしていない。

## リポジトリ運用

- `Bend2_Life_Textbook.tex`が教科書の正本。PDFは再生成物として併置。
- 最新版とコンパイラの差分をIssuesで報告できるよう、環境・Bend版・実行コマンド・エラーログを添付する。
- 意図的な失敗例 `*_INVALID.bend` を通常の成功テストから除外する。
- `make pdf`は相互参照を解決するためXeLaTeXを3回実行する。
