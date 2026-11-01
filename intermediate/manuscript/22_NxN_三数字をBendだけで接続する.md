# 第22章補稿：公開数字から三数字連立推論までBendで接続（TeX・PDF未統合）

## なぜ手でビット集合を作るだけでは足りないのでしょうか

これまでは、公開数字0・2・7の未知近傍を手で7・13・62に直してから三数字推論器へ渡しました。しかし盤面が変わるたびに手計算していては、公開情報だけで確定手を選ぶプログラムになりません。今回は、公開マスの番号・数字から六ビット変換と三数字の全候補列挙までを、Bendの関数として接続します。

## Bendコードと実行結果

新しい `intermediate/minesweeper/nxn_public_three_bridge.bend` は、既存の `Six.mask_for` を三回呼び、成功した三つのマスクだけを `Three.infer` へ渡します。

```bend
def main() -> U32:
  Three.score(from_public(3, 0, 2, 7, 1, 1, 1,
                         [0, 2, 7], [1, 3, 4, 5, 6, 8], 2, True{}))
```

```sh
bend intermediate/minesweeper/nxn_public_three_bridge.bend --check-only
bend intermediate/minesweeper/nxn_public_three_bridge.bend
# 341
```

公開マスは0・2・7番、六つの未知マスは1・3・4・5・6・8番です。公開数字がすべて1で地雷総数2なら、整合する配置は2通り。確定安全ビット14は3・4・5番、確定地雷ビット1は1番に対応します。341は `models*100 + safe*10 + mines` という教材用の符号であり、確定マス数そのものではありません。

## 仕組みと入力の境界

`Six.mask_for` は `Valid{bits}` と `Invalid{}` を返します。空の未知近傍を表す正しいマスク0と、変換に失敗した `Invalid` は違います。`with_first` → `with_second` → `with_third` で各結果を一度ずつ `match` し、三つとも有効な場合だけ全64候補を調べます。失敗をマスク0として扱いません。

4×4盤面で四つのマスだけを開いたとき、未知マスは12個です。そのうち六つを調べる局所推論に盤面全体の地雷総数を直接使うと、誤った確定手が生まれます。`use_total=True{}` を許すのは、盤面全体の未公開マスがちょうど六つのときだけです。それ以外では拒否します。局所推論のみなら `False{}` を指定します。

この小さなAPIの `Inconsistent` は、無効な入力と制約の矛盾を一つにまとめます。盤面全体に解がないと断定してはいけません。また `revealed` は昇順・重複なし・盤内、`universe` は公開マスを含まない六つの異なる昇順の番号という入力契約があります。未知マス六つの自動選択は未実装です。

## 演習

最初に `True{}` を `False{}` に変え、総地雷数を使わないと出力が400になる理由を、候補数・安全ビット・地雷ビットに分けて考えてみましょう。次に4×4で `revealed=[0,1,2,4]`、`universe=[3,5,6,7,8,9]`、公開数字0・1・4の残数を0・0・1にして、`False{}` で860が得られることを確かめてみましょう。同じ入力で `True{}` にすると拒否される理由も説明してみましょう。

```sh
python3 intermediate/scripts/test_nxn_public_three_bridge.py
# PASS 12 Bend/Python public three-clue bridge cases
```

このテストは独立したPython座標・集合全列挙オラクルと、Bendの型検査・実行結果を照合します。`--oracle-only` はPythonの予備検査だけで、Bend実行の証拠にはなりません。

**未検証・未実装：** 任意N×N盤面のfrontier抽出、四数字以上の一般連立、総地雷数の局所配分、Bend版一般運ゲー無し生成器、10×10 GUI実機、全称証明。TeX本文・PDF・読者ZIPへの統合も別の検収ゲートです。
