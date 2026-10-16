# Bend 2 基本機能監査（第1版）

監査基準: [公式ガイド](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)、[公式README](https://github.com/bendlang/bend)、[Base](https://github.com/bendlang/bend/blob/main/bend2/base.bend)。2026-10-16時点のBend 2.0.36を対象とする。

「掲載済み」は本文・演習・ソースで取り上げたことを意味します。**Bend 2.0.37を使ったCIでは29ファイルの型検査と逐次ライフゲームの実行比較に成功しています**が、掲載したすべてのGUI・GPU・証明用APIの実行を保証するものではありません。

| 仕様分野 | 対応 | サンプル / 実装段階 |
| --- | --- | --- |
| 関数、注釈、U32/Nat、基本演算 | 本文と例 | `02_arithmetic.bend`, `17_numbers_strings.bend` |
| ADT、constructor、match | 本文と例 | `13_status_adt.bend`, `28_data_types.bend` |
| List、再帰、停止性 | 本文と例 | `14_list_basics.bend` |
| Array、アフィン、+/-の量 | 本文と例 | `04_array.bend`, Life更新核, `12_...INVALID.bend` |
| クロージャと高階関数 | 本文と例 | `15_closure.bend`, `29_higher_order.bend` |
| テンプレート（~） | 本文と例 | `16_template.bend` |
| Kind / Type / Data / Quant | 本文と例 | `23_kinds.bend` |
| Bool/Cmp、F32、Char/String、bit | 本文と演習 | `bend base`で定義を参照。F32精度の証明は対象外 |
| Maybe、Result、モナドとdo | 本文と例 | `21_monadic_maybe.bend`, `30_monad_explicit.bend` |
| Map / Set | Mapは例、Setは課題 | `25_map_basics.bend`, `bend base Set` |
| モジュール / import / 構築 | 本文と例 | `module_math.bend`, `19_module_main.bend` |
| IO、File、args、エラー | 本文とFile例 | `20_io_fork.bend`, `26_file_write.bend`（上書き注意） |
| IOの並行性 / Channels | 本文と例 | `20_io_fork.bend` |
| 純粋なCPU並列 / GPU ! | 本文と独立例 | `09_parallel_tree.bend`, `10_gpu_tree.bend`。Life本体は未実装 |
| App / Image / Event | 本文と独立例 | `22_app_preview.bend`。GUI版Lifeは未実装 |
| ファイル以外の標準効果 / FFI | 本文と実験課題 | ネット、音声、プロセス、C/JS拡張は発展扱い |
| 法則、証明、帰納法、verdict | 本文と例 | `11_rule_proofs.bend`, `24_proof_induction.bend` |
| C / JS / mjs ターゲット、BendHub | 本文と実習手順 | publish実行は含めない |

## 既知の未完・未検証事項

1. GitHub Actions上のBend 2.0.37で、意図的に誤った例を除く29ソースファイルの型検査に成功しています。
2. Bendで生死規則の18ケースと8×8の5世代全セルを検査し、Python参照実装と一致しました。
3. 高階関数の42の実行結果と、Maybeのdo/bind各成功・失敗ケースの一致をBend上で検査済みです。
4. 並列GPUのLife本体、ファイルからのパターン読込、可変サイズ、GUI版、盤面全体の形式証明は発展課題。
5. Set、ネットワーク、音声、独自FFI、BendHubについては概念とAPI調査課題を用意。全APIの実演・動作確認はしていない。

## リポジトリ運用

- `Bend2_Life_Textbook.tex`が教科書の正本。PDFは再生成物として併置。
- 最新版とコンパイラの差分をIssuesで報告できるよう、環境・Bend版・実行コマンド・エラーログを添付する。
- 意図的な失敗例 `*_INVALID.bend` を通常の成功テストから除外する。
- `make pdf`は相互参照を解決するためXeLaTeXを3回実行する。
