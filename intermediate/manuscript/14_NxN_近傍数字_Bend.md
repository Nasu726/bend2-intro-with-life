# 第13〜14章補稿：N×N盤面の数字をBendで計算する（PDF未統合）

4×4だけの地雷マスクから10×10の盤面へ進むと、数字を数える際に「右端の隣は次の行の左端なのか」という問題が起きます。地雷の格納と8近傍の判定を分け、**盤外のセルを一度も読まない**ようにしましょう。

## 実際のBendコード

まず minesweeper/nxn_mine_words.bend が地雷の真値を32ビット語列に保存し、minesweeper/nxn_geometry.bend が非トーラス8近傍を判定します。新しい minesweeper/nxn_clues.bend は両者を組み合わせます。

inspect は Geo.neighbor が真のときだけ Mines.has を呼びます。at_valid は中心を除く8方向を順に検査し、MineWords の所有権を戻り値に渡します。

~~~bend
def inspect(board: Mines.MineWords, +n: U32, +x: U32, +y: U32,
            +u: U32, +v: U32) -> Mines.MineWords & U32:
  match Geo.neighbor(n, x, y, u, v):
    case True{}:
      counted(Mines.has(board, Geo.index(n, u, v)))
    case False{}:
      (board, 0)

def main() -> U32:
  result(checked(Mines.set_checked(
    Mines.set_checked(Mines.new(10), 0, True{}), 11, True{}), 1))
~~~

リポジトリのルートで次を実行してみましょう。

~~~sh
bend intermediate/minesweeper/nxn_clues.bend --check-only
bend intermediate/minesweeper/nxn_clues.bend
python3 intermediate/scripts/test_nxn_clues.py
~~~

Bendの出力は 2 です。地雷は添字0（左上）と11（次の行の列1）にあり、添字1（最上段の列1）から見て両方とも8近傍に入ります。検証スクリプトは別のPython集合計算で小盤面の全地雷配置や100×100の境界を照合し、成功すれば PASS Bend N x N clues: ... independent finite checks を表示します。件数はスクリプトが生成した検査式の数です。

## どうしてこの形にするのでしょうか

Mines.has は所有権を持つ MineWords を受け取り、同じ盤面と真偽値の組を返します。counted、plus、next はこの組を順番に受け渡し、8方向の数を合計します。計算結果の組を直接分解する代わりに、関数の引数として受け取るのもBendの書き方です。

U32.sub(0,1) は符号なし整数として折り返しますが、Geo.neighbor が盤外を拒否するため、その添字で配列を読みません。10×10の Array の実容量が128であっても、100〜127は無効です。checked はこのような添字を None にし、有効な数字0と区別します。result が None を99と表示するのは**この実行例の表示専用**であり、ゲーム本体では Maybe を分岐させます。

**重要：この関数が読むのは地雷の真値です。** 数字を公開するゲーム側だけで使用し、運ゲー無し推論器へ地雷語列を渡してはいけません。推論器が受け取るのは公開された数字と総地雷数・旗だけです。

## 演習

地雷を添字0だけにして、添字1の数字が1になることを確かめてみましょう。次に添字9（右上）と10（次の行の左端）が隣接しない理由を座標で説明してみましょう。最後に添字100と127を checked に渡し、None と数字0が異なることを確認してみましょう。

## 検証の境界

この追加でBendによる**近傍数字の有限実行照合**が可能になりますが、N×Nのゲーム状態遷移、0連鎖、GUI実機、公開情報ソルバー、推測不要生成器の一般化、全入力に対する形式的証明は未完了です。補稿はまだTeX/PDF/読者ZIPへ統合していません。
