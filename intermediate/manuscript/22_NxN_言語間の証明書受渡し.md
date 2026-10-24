# 第22章補稿：Bendで作る盤面を、別プロセスで検査する（PDF未統合）

## なぜ、証明書をファイルに分けるのでしょうか

これまでのN×N候補生成・独立検査はPythonの一つの処理から呼び出していました。しかし、完成目標はBend製の生成器です。生成器をBendに置き換えるたびにPythonの検査器も書き換えると、生成側と検査側に同じ間違いを入れるおそれがあります。そこで、**生成器の言語に依存しないJSONの受渡し形式**を先に決めます。

## Bendの小さな確定手の例

現時点でBendが実装・検証済みなのは、4×4・地雷2個の限定ソルバーです。`intermediate/minesweeper/public_two_corners.bend` を見てみましょう。

```bend
import Base
import ./public_solver.bend as Solver

def show(result: Maybe<&2, U32>) -> U32:
  match result:
    case Some{bits}:
      bits
    case None{}:
      65536

def main() -> U32:
  show(Solver.provably_safe(Solver.Public{[
    Solver.Number{0, 0}, Solver.Number{15, 0}
  ]}))
```

```sh
bend intermediate/minesweeper/public_two_corners.bend
# 19506
```

この結果は、公開数字0が二つある限定盤面について確実に安全なマスをビット集合で表したものです。**このBendコードはまだN×N生成証明書を出力しません**。次に示すJSONは、別途Python参照生成器で確認した4×4の盤面証明書です。二つを同一の実行結果と混同しないでください。

## 証明書の受渡しと実行結果

リポジトリのルートで、以下のJSONを `witness.json` に保存してみましょう。

```json
{
  "version": 1,
  "size": 4,
  "mine_count": 2,
  "first": 0,
  "mines": [1, 4],
  "clicks": [0, 2, 3],
  "opened_count": 14
}
```

```sh
python3 intermediate/scripts/audit_nxn_witness.py witness.json
# {"checked_clicks": 3, "first": 0, "mine_count": 2, "opened_count": 14, "reason": "", "size": 4, "status": "valid"}
```

この結果はPython独立検査器が再計算したものであり、BendのN×N生成器の実行結果ではありません。`mines` は生成器から検査器へ渡す**検証用の真の配置**です。プレイヤーの推論器へ渡す入力ではありません。検査器は公開数字を再構築し、各クリックがその時点で公開情報から確定できる最小添字の安全マスであることを全候補列挙で確かめます。最初のクリックだけは安全と指定した前提であり、推論で選んだ手ではありません。

`--max-hypotheses 1` を付けると `status` は `limit`、終了コードは2になります。正しい証明書と判定できたときだけ `valid`（終了コード0）です。不正なクリック順や形式は `invalid`（終了コード3）になります。

## なぜ厳密な入力形式が必要なのでしょうか

`version` は1に固定し、七つのフィールドをすべて必須とします。`mines` と `clicks` は整数の配列で、`mine_count` は地雷配列の長さと一致させます。重複したJSONキー、`true` を整数の代わりに書いた入力、余計なフィールド、64KiBを超えるファイルは拒否します。Bend版が将来この形式を出力すれば、Python生成器をimportせずに**別プロセスで同じ検査**を行えます。

ただし、全候補列挙は指数時間です。大きな盤面で `limit` が返ることは、証明書の正しさも誤りも意味しません。Bend N×Nのソルバー・生成器、10×10 GUI、実機受け入れ試験、一般の全称証明は未完成です。

## 演習

`clicks` を `[0, 3, 2]` に入れ替え、検査結果が `invalid` になることを確認してみましょう。`mine_count` を3に変更し、実際の `mines` の要素数と矛盾する場合の結果を観察してみましょう。最後に、`--max-hypotheses 1` を付けた場合と付けない場合の終了コードを比較してみましょう。

## 検証範囲

`tests/test_audit_nxn_witness.py` は、既知の4×4証明書、偽造・不正形式・重複キー・サイズ上限・別プロセスの終了コードを有限個のケースで検査します。検査器は既存の `verify_nxn_certificate.py` を再利用します。これは**BendとPythonの間の入力契約を準備する工程**であって、Bendによる一般サイズの生成・実行照合が完了したという意味ではありません。TeX本文・生成PDF・読者ZIPには未統合です。
