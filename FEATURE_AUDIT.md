# 基本文法の掲載・検証一覧

第1版は基本文法の学習とライフゲームの実装を扱います。監査資料として、本文と付属コードの対応を記録します。

| 項目 | 本文・コード |
| --- | --- |
| データ型、型注釈、関数、演算 | `02_arithmetic.bend`, `17_numbers_strings.bend`, `28_data_types.bend` |
| ユーザー定義型、パターンマッチ | `13_status_adt.bend`, `27_match_basics.bend` |
| 配列、所有権、利用回数の制約 | `04_array.bend`, `12_affine_probe_INVALID.bend` |
| 再帰的リスト、Maybe、Result | `14_list_basics.bend`, `21_monadic_maybe.bend` |
| 高階関数、クロージャ | `29_higher_order.bend`, `15_closure.bend` |
| テンプレート | `16_template.bend` |
| モナド、do、bind | `21_monadic_maybe.bend`, `30_monad_explicit.bend` |
| モジュールとimport | `module_math.bend`, `19_module_main.bend` |
| 入出力（表示） | `01_hello.bend`, `08_life_terminal.bend` |
| ライフゲームの全体実装 | `03_rule.bend` ～ `08_life_terminal.bend` |

**検証:** GitHub Actions上のBend 2.0.37で型検査、18件の生死規則、5世代の盤面照合、高階関数とモナドの実行結果を検査する構成です。Pythonの参照テストと教材構成テストもCIで実行します。未実行の版では結果を保証しません。

全ての標準ライブラリAPIや外部パッケージの網羅を意味する資料ではありません。

## 本編に復帰させた中核機能

- CPU並列呼び出し：`src/09_parallel_tree.bend`, `src/31_parallel_life_pair.bend`
- GPU呼び出し：`src/10_gpu_tree.bend`, `src/32_gpu_life_call.bend`
- `law`、証明用の`def`、数学的帰納法：`src/11_rule_proofs.bend`, `src/24_proof_induction.bend`

形式的証明の対象は局所規則などの明示された命題のみです。盤面全体について証明したという主張はしません。
