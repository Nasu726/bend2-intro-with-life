# 第22章補稿：固定点推論の証明書を別プロセスへ渡す（TeX・PDF未統合）

## なぜファイルで検査するのでしょうか

一つのPython処理の中で推論器と検査器を呼ぶだけでは、将来Bendで証明書を生成するときに入力の受渡しを確認できません。公開数字・別途証明されたマス・推論の各手を、言語に依存しないJSONへ保存して検査してみましょう。**地雷の真の配置や旗を入力してはいけません。**

## Bendの一数字推論と、Pythonの反復処理を区別しましょう

```sh
bend intermediate/minesweeper/nxn_public_local.bend
# 1
```

このBend例の`1`は、公開数字1と別途確定した地雷1番から、3・4番を安全と判定した`Safe`タグです。**複数の数字を反復するBend実装ではありません。** ここから先の反復推論・証明書生成はPython参照実装です。

リポジトリのルートで次を実行します。

```sh
PYTHONPATH=intermediate/solutions python3 - <<'PY'
from dataclasses import asdict
import json
from pathlib import Path
from nxn_single_clue_certificate import certify

shown = ((0, 0), (2, 1), (6, 1))
mines, safe, proof = certify(3, shown)
witness = {
    "version": 1, "size": 3,
    "opened": [list(item) for item in shown],
    "certified_mines": [], "certified_safe": [],
    "steps": [asdict(step) for step in proof],
}
Path("witness.json").write_text(json.dumps(witness), encoding="utf-8")
PY
python3 intermediate/scripts/audit_single_clue_witness.py witness.json
```

```json
{"mines": [5, 7], "safe": [1, 3, 4], "size": 3, "status": "valid", "steps": 3}
```

## 何を確かめているのでしょうか

JSONの`opened`は公開済み数字、`certified_mines`と`certified_safe`は**別途証明済みの初期情報**です。`steps`の各要素は`clue`・`mines`・`safe`を持ちます。検査器は、各手で使った公開数字の残数を再計算し、確定できないマスの追加・重複・途中で切れた証明書を拒否します。最後に単一数字規則の固定点を確認します。

**検査器の独立性：** JSONを読む`audit_single_clue_witness.py`は、
`nxn_single_clue_checker.py`の検証処理だけをimportします。
証明書生成器`nxn_single_clue_certificate.py`と、その生成器が照合に使う
反復推論器`nxn_single_clue_propagation.py`は読み込みません。
同じ誤った推論結果を生成器と検査器が共有する危険を減らすためです。
ただし、局所規則そのものの誤りや初期証拠の誤りまで排除するものではありません。

入力形式は`version=1`、`size=2..100`、昇順で重複のないセル番号、六つの必須トップレベル項目に固定しました。余分な項目・重複JSONキー・真偽値を整数にした入力・64KiB超のファイルは拒否します。成功は終了コード0、形式や証明が不正なら3、引数の誤りは2です。検査器は証明書**生成器**を呼ばず、既存の独立リプレイ規則だけを使います。

**保証の境界：** この検査は公開数字と初期確定情報が正しいことを前提とする局所健全性です。全盤面に整合する地雷配置の存在、二数字以上の連立推論、一般N×Nの運ゲー無し生成を保証しません。Bend側の固定点推論・JSON出力も未実装です。読者ZIPにはこの内部検査器や解答を収録しません。

## 演習

`witness.json`の最初の`safe`から`4`を削り、最後まで検証できるか試してみましょう。次に最後の`steps`を一つ消し、固定点検査が拒否する理由を説明してみましょう。`opened`の数字を変更したときの結果も比較してみましょう。
