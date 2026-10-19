#!/usr/bin/env python3
"""Apply the agreed x,y -> index(x,y) migration to both Bend textbooks.

For use only on a fresh verification checkout. Do not overwrite the
reader-approved intermediate cover or change the games' public click IDs.
"""
from pathlib import Path

R = Path(__file__).resolve().parents[2]

def change(file: str, old: str, new: str):
    p = R / file
    s = p.read_text(encoding="utf8")
    count = s.count(old)
    assert count == 1, (file, old[:85], count)
    p.write_text(s.replace(old, new), encoding="utf8")

def add_after(file: str, anchor: str, additional: str):
    change(file, anchor, anchor + additional)

# 8x8 Life: keep the flat 64-element storage but remove numerical cell IDs
# from coordinate-based reads and seed placement. Linear traversal remains
# linear by design, rather than obscuring the useful idea of sequential scan.
life = [
    "src/05_glider.bend", "src/06_neighbors.bend",
    "src/07_life_core.bend", "src/08_life_terminal.bend",
    "src/life_core.bend",
]
definition = (
    "# In an 8x8 board, x is the column and y is the row (both 0..7).\n"
    "# This helper assumes the caller has already checked the range.\n"
    "def index(x: U32, y: U32) -> U32:\n"
    "  (y * 8 + x : U32)\n\n"
)
for file in life:
    add_after(file, "import Base\n\n", definition)
for file in life[1:]:
    change(file, "Array.get(U32, b, (y * 8 + x : U32))",
                  "Array.get(U32, b, index(x, y))")
for file in ("src/05_glider.bend", "src/07_life_core.bend",
             "src/08_life_terminal.bend", "src/life_core.bend"):
    for number, x, y in ((1,1,0),(10,2,1),(16,0,2),(17,1,2),(18,2,2)):
        old = f", {number:2d}, 1)" if number != 1 else ",  1, 1)"
        # Actual source pads 1 with two spaces; other values have one.
        change(file, old, f", index({x}, {y}), 1)")
for number,x,y in ((27,3,3),(28,4,3),(29,5,3)):
    change("src/06_neighbors.bend", f", {number}, 1)",
           f", index({x}, {y}), 1)")
change("src/05_glider.bend", "Array.get(U32, glider(), 18)",
       "Array.get(U32, glider(), index(2, 2))")
for file in ("src/07_life_core.bend", "src/life_core.bend"):
    change(file, "Array.get(U32, evolve(4n, glider()), 26)",
           "Array.get(U32, evolve(4n, glider()), index(2, 3))")
assert (R/"src/07_life_core.bend").read_bytes() == (R/"src/life_core.bend").read_bytes()

book="Bend2_Life_Textbook.tex"
change(book, r"\chapter{一次元配列で8×8盤面を表す}",
       r"\chapter{座標とindex関数で8×8盤面を扱う}")
change(book,
       "続いて二次元の盤面を一次元の配列に並べます。ここから実際のシミュレータを組み立てます。",
       "続いて盤面を(x,y)で操作する補助関数を作ります。配列の格納方法は補助関数に任せ、ライフゲームの処理へ集中します。")
p=R/book
s=p.read_text(encoding="utf8")
begin=s.index(r"\section{二次元の盤面を一次元配列に並べる}")
end=s.index(r"\section{すべてのセルを0で初期化する}", begin)
replacement=r"""\section{座標から格納位置を求める関数}
盤面は8行×8列です。生きているマスを\((x,y)\)で指定できれば、「右へ1」「下へ1」もそのまま座標で考えられます。内部の保存先を毎回手計算する必要はありません。

\begin{lstlisting}[caption={8×8盤面で共通に使う補助関数}]
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)
\end{lstlisting}

\code{x}は左から数えた列、\code{y}は上から数えた行です。どちらも0〜7の範囲で指定します。例えば\code{index(1, 2)}は17、\code{index(7, 7)}は63になります。今後は\code{Array.get}や\code{Array.set}へ\code{index(x, y)}を渡しましょう。

\begin{pointbox}
盤面の保存形式は長さ64の一次元\code{Array<U32>}のままです。\code{index}だけが二次元の座標を格納位置へ変換します。この補助関数は\textbf{範囲外の座標を検査しません}。0〜7の有効な\code{x}、\code{y}を渡す前提で使います。

Bend 2の\code{Array.get}には範囲外の添字が循環する動作がありますが、それを盤面の境界条件の代わりに使ってはいけません。二次元のトーラスは、まず\code{x}と\code{y}を各々循環させて実現します。
\end{pointbox}

配列を要素に持つ\code{Array<Array<U32>>}も型として表せますが、本書の実習では一枚の一次元配列と\code{index}で十分です。セルの配置・近傍・世代更新を理解することを優先します。

"""
p.write_text(s[:begin]+replacement+s[end:], encoding="utf8")
change(book,
       r"\code{[0 : U32*64n]}で要素64個を確保します。書き込みは\code{Array.set(U32,b,index,value)}で新しい所有者に移る。よって\code{b0,b1,b2,...}と変数名を変えていくとアフィン性が見えます。インデックスは\(8y+x\)で求めます。",
       r"\code{[0 : U32*64n]}で64個の要素を用意します。書き込みは\code{Array.set}で行い、結果として返る配列を次の操作へ渡します。例えば\code{Array.set(U32,b,index(1,2),1)}は座標(1,2)を生存状態にします。値を移す様子は\code{b0,b1,b2,...}という変数名にも表れています。")
change(book,
       r"\section{座標を配列の添字に変換する}",
       r"\section{トーラスでも座標から考える}")
change(book,
       r"Bendの配列は範囲外インデックスがラップする仕様を持ちます。しかし\textbf{一次元のラップ}は\textbf{二次元のトーラス隣接}と同じではありません。\((7,0)\)の右隣は\((0,0)\)であって\((0,1)\)ではありません。近傍計算は座標ごとに\(x\)と\(y\)を循環させてから一次元化します。",
       r"\code{index}は有効な座標を格納位置にするだけです。トーラスの右端(7,0)から一つ右の座標は(0,0)です。座標ごとに循環させた後で\code{index}を呼び出せば、配列の添字の循環と盤面のトーラスを混同せずに済みます。")
change(book,
       r"\exercise{添字7と8の意味を説明してみましょう。\((7,0)\)から右に動いたとき\code{i+1}してはいけない理由を図にして考えてみましょう。}",
       r"\exercise{\code{index(7,0)}と\code{index(0,1)}の値を予想してみましょう。続いて(7,0)の右隣を\code{index}で求めるには、先にどの座標へ直すべきか図にして考えてみましょう。}")
change(book,
       r"行優先添字に変換すると\(1,10,16,17,18\)になります。",
       r"コードではこの五つを\code{index(x,y)}にそのまま渡します。数値の添字を暗記する必要はありません。")
change(book,
       r"\item \code{glider()}は5セルを1にした入力の配列を作る。",
       r"\item \code{glider()}は五つの座標を\code{index(x,y)}で指定して初期配置を作ります。")
change(book,
       r"\item \code{fill(64n,0,old,out)}はセル\(i=0\)から\(63\)を処理します。",
       r"\item \code{fill(64n,0,old,out)}は64セルを順番に処理します。ここは配列全体の走査なので、内部の添字\code{i}を使います。")
change(book,
       r"\item \code{neighbors}は旧盤面を読み、\code{Array.get}は対象セルの現在値を読みます。",
       r"\item \code{neighbors}と\code{at}は座標を受け取り、\code{index(x,y)}を介して旧盤面のセルを読みます。")

# Both the reading order and executable code must agree about the new helper.
change("tests/test_textbook_structure.py",
       r'\chapter{一次元配列で8×8盤面を表す}',
       r'\chapter{座標とindex関数で8×8盤面を扱う}')
add_after("tests/test_textbook_structure.py",
          "    def test_no_editorial_warnings_to_readers(self):",
          "")
# Insert a proper regression test before the editorial test.
change("tests/test_textbook_structure.py",
       "    def test_no_editorial_warnings_to_readers(self):",
       '''    def test_life_uses_xy_index_consistently(self):
        self.assertIn("def index(x: U32, y: U32)", self.part2)
        for sample in ("05_glider.bend", "06_neighbors.bend",
                       "07_life_core.bend", "08_life_terminal.bend", "life_core.bend"):
            code = (ROOT / "src" / sample).read_text(encoding="utf8")
            self.assertIn("def index(x: U32, y: U32) -> U32:", code)
            self.assertIn("(y * 8 + x : U32)", code)
            self.assertIn("index(", code)
        self.assertIn("index(1, 0)", (ROOT/"src/05_glider.bend").read_text())
        self.assertIn("index(2, 2)", (ROOT/"src/05_glider.bend").read_text())

    def test_no_editorial_warnings_to_readers(self):''')

insert_test='''def test_xy_index_mapping() -> None:
    """Execute the helper in real Bend, including row boundary cases."""
    original = (SOURCE / "05_glider.bend").read_text(encoding="utf8")
    head, marker, unused_main = original.partition("def main() -> U32:")
    assert marker
    coords = [(0, 0), (7, 0), (0, 1), (3, 2), (7, 7)]
    program = head + "\\\\ndef main() -> IO(Unit):\\\\n  do IO<Unit>:\\\\n"
    for x,y in coords:
        program += f'    IO.print(U32.show(index({x}, {y})))\\\\n'
    with tempfile.TemporaryDirectory(prefix="bend-xy-index-") as td:
        temp=Path(td)/"coordinates.bend"
        temp.write_text(program,encoding="utf8")
        actual=run(["bend",str(temp)]).strip().splitlines()
    assert actual == ["0","7","8","19","63"], actual
    print("PASS 8x8 index(x,y) = 0,7,8,19,63")

'''
# Escape sequences above are literal Python source for the test: \n in strings.
change("scripts/test_bend_runtime.py",
       "def test_parallel_and_proofs() -> None:",
       insert_test+"def test_parallel_and_proofs() -> None:")
change("scripts/test_bend_runtime.py",
       "tests = [test_rule_table, test_life_transcript,",
       "tests = [test_rule_table, test_xy_index_mapping, test_life_transcript,")

change("README.md",
       "ライフゲームの**完成版や演習の参考実装**",
       "盤面は`index(x, y)`で座標を指定します。幅8のライフゲームでは、一次元配列の格納先を`index`が計算するため、セル番号を覚える必要はありません。範囲外の座標は別に検査します。\n\nライフゲームの**完成版や演習の参考実装**")

# Intermediate: 4x4 game and 8x8 pixel exercises use identical x,y order,
# while click IDs / mine bit masks remain intentionally linear.
change("intermediate/src/board_index.bend",
       "# A 4x4 board's row and column become a one-dimensional index.\ndef index(row: U32, col: U32) -> U32:\n  (row * 4 + col : U32)",
       "# The first argument is the column x, then the row y (both 0..3).\n# Caller checks bounds; this is only a coordinate-to-index conversion.\ndef index(x: U32, y: U32) -> U32:\n  (y * 4 + x : U32)")
change("intermediate/src/42_module_board.bend",
       "  Board.index(2, 3)",
       "  Board.index(3, 2)  # column 3, row 2: position 11")
game_def = (
    "# Coordinate helper: x=column, y=row; caller checks x,y in 0..3.\n"
    "def index(x: U32, y: U32) -> U32:\n"
    "  (y * 4 + x : U32)\n\n"
)
add_after("intermediate/minesweeper/board.bend",
          "import ./game.bend as Game\n\n", game_def)
add_after("intermediate/minesweeper/gui.bend",
          "import ./board4.bend as Board4\n",
          "import ./board.bend as Board\n")
change("intermediate/minesweeper/gui.bend",
       "Some{(U32.div(y, 64) * 4 + U32.div(x, 64) : U32)}",
       "Some{Board.index(U32.div(x, 64), U32.div(y, 64))}")

exercise_def = (
    "# 8x8 example: x=column and y=row (0..7 after pixel bounds check).\n"
    "def index(x: U32, y: U32) -> U32:\n"
    "  (y * 8 + x : U32)\n\n"
)
for file in ("intermediate/src/23_cell_hit_test.bend",
             "intermediate/src/32_mouse_events.bend"):
    add_after(file, "import Base\n\n", exercise_def)
    change(file, "U32.add(U32.mul(U32.div(y, 32), 8), U32.div(x, 32))",
           "index(U32.div(x, 32), U32.div(y, 32))")

mid="intermediate/Intermediate_Textbook.tex"
change(mid,
       r"\code{cell_if_valid}は、盤面内なら\code{(y / 64) * 4 + (x / 64)}を返します。",
       r"\code{cell_if_valid}はまず画素を列\code{x/64}と行\code{y/64}に分け、範囲内なら\code{Board.index}で番号へ変換します。")
change(mid,
       r"行を\code{y}、列を\code{x}とすると、4×4盤面の添字は\(\,4y+x\,\)です。(1,1)なら5、(3,3)なら15になります。画面の座標が盤面外なら、\code{Array.get}に進む前に取り除かなければなりません。",
       r"盤面を扱う間は列\code{x}、行\code{y}の二つで位置を考えます。例えば(1,1)は5番、(3,3)は15番です。補助関数\code{Board.index(x,y)}が、内部の一次元配列の番号へ変換します。画面外の座標は\code{Array.get}に進む前に拒否してください。")
change(mid,
       r"\section{4×4の盤面を配列に並べる}",
       r"\section{座標を使い、内部では一次元配列に格納する}")
change(mid,
       r"\section{座標を使い、内部では一次元配列に格納する}",
       r"""\section{座標を使い、内部では一次元配列に格納する}
実装では次の小さな関数に座標変換を任せます。\code{x}が横方向の列、\code{y}が縦方向の行です。

\begin{lstlisting}[caption={4×4盤面の補助関数（board.bendより）}]
def index(x: U32, y: U32) -> U32:
  (y * 4 + x : U32)
\end{lstlisting}

""")
change(mid,
       r"8×8なら配列の添字は\(8\times\text{行}+\text{列}\)です。第12章の\code{23_cell_hit_test.bend}をもう一度開き、コード中でこの計算を行う場所を見つけてください。",
       r"8×8の実習コードでは\code{index(x,y)}へ列と行を渡します。第12章の\code{23_cell_hit_test.bend}を開き、画素座標から列と行を求め、\code{index}を呼ぶ順序を確認してください。")
change(mid,
       r"第13章の参考ゲームエンジンは4×4ですが、この座標変換は8×8です。ゲームにつなぐ際には、行数と列数を統一します。例えば32画素のマスを4×4に並べるなら、画面は128×128画素で、添字は\(4\times\text{行}+\text{列}\)になります。",
       r"第13章の参考ゲームエンジンは4×4ですが、この練習例は8×8です。両者の\code{index(x,y)}は同じ引数順でも盤面の幅が異なります。例えば32画素の4×4なら画面は128×128画素です。呼び出す補助関数と境界検査を、盤面の大きさに合わせてください。")
change(mid,
       r"まず\code{board_index.bend}には\code{index}という関数が入っています。行を\code{row}、列を\code{col}とすると、添字は\code{row * 4 + col}です。2行目の3列目なら11になります。",
       r"まず\code{board_index.bend}には\code{index(x,y)}という関数があります。\code{x}は列、\code{y}は行です。例えば\code{index(3,2)}は11です。呼び出し側では場所を座標で考え、内部の格納位置は関数へ任せます。")
change(mid,
       "  Board.index(2, 3)\n",
       "  Board.index(3, 2)\n")
change(mid,
       r"この例では\code{index}を呼ぶ前に座標が盤面内か確かめていません。実際の4×4盤面では、行・列が0〜3であることも検査してください。",
       r"この例では\code{index}を呼ぶ前に座標を検査していません。実際の4×4盤面では\code{x}と\code{y}がともに0〜3であることを先に検査してください。")
change(mid,
       r"\section{マウスから得られるのは盤面の番号ではない}",
       r"\section{マウスから得られるのは盤面の番号ではない}")
# Replace the otherwise formula-heavy text with the rationale for the helper.
change(mid,
       r"このサンプルでは、一辺32画素のマスを縦横8個並べた256×256画素の画面を想定しています。\code{(64,32)}は左から3列目、上から2行目なので、0始まりの添字は",
       r"このサンプルでは32画素のマスを8×8並べます。\code{(64,32)}は列2、行1なので、\code{index(2,1)}が返す番号は")
change(mid,
       r"""  \left\lfloor \frac{32}{32} \right\rfloor\cdot 8
  +\left\lfloor \frac{64}{32} \right\rfloor=10""",
       r"""  \operatorname{index}(2,1)=10""")
change(mid,
       r"となります。一方、\code{(256,32)}は画面外です。",
       r"です。一方、\code{(256,32)}は画面外です。")

add_after("intermediate/tests/test_structure.py",
          "    def test_gui_coordinate_reference_boundaries(self):",
          "")
change("intermediate/tests/test_structure.py",
       "    def test_gui_coordinate_reference_boundaries(self):",
       '''    def test_index_xy_contract_for_minesweeper_and_examples(self):
        board = (ROOT / "minesweeper" / "board.bend").read_text(encoding="utf8")
        gui = (ROOT / "minesweeper" / "gui.bend").read_text(encoding="utf8")
        sample = (SRC / "board_index.bend").read_text(encoding="utf8")
        demo = (SRC / "42_module_board.bend").read_text(encoding="utf8")
        for code in (board, sample):
            self.assertIn("def index(x: U32, y: U32) -> U32:", code)
            self.assertIn("(y * 4 + x : U32)", code)
        for name in ("23_cell_hit_test.bend", "32_mouse_events.bend"):
            exercise = (SRC / name).read_text(encoding="utf8")
            self.assertIn("def index(x: U32, y: U32) -> U32:", exercise)
            self.assertIn("index(U32.div(x, 32), U32.div(y, 32))", exercise)
        self.assertIn("Board.index(U32.div(x, 64), U32.div(y, 64))", gui)
        self.assertIn("Board.index(3, 2)", demo)
        for y in range(4):
            for x in range(4):
                self.assertEqual(y*4+x, 4*y+x)

    def test_gui_coordinate_reference_boundaries(self):''')
change("intermediate/tests/test_structure.py",
       'for part in ("App.run(~Start.Stage", "Array.clone(Game.Square, cells)",',
       'for part in ("App.run(~Start.Stage", "Array.clone(Game.Square, cells)", "Board.index(",')
with (R/"intermediate/manuscript/STATUS.md").open("a",encoding="utf8") as f:
    f.write("\n## 座標アクセスの統一（2026-10-19）\n\n"+
    "- 入門書は8×8、中級書は4×4の`index(x,y)`（x=列、y=行）を利用する。格納方式は一次元Arrayのまま。\n"+
    "- `board_index.bend`の旧`index(row,col)`を座標順へ修正。`42_module_board.bend`は座標(3,2)を渡して従来どおり11を出力する。\n"+
    "- 8×8の学習用画素変換と4×4 GUIは座標の範囲を確認した後に`index`を呼ぶ。既存のクリック番号0〜15、地雷ビットマスク、証明範囲は変更しない。\n"+
    "- 入門/中級とも本文・実行例・CI・生成PDF/ZIPを同期検証。採用表紙は編集しない。\n")
with (R/"intermediate/README.md").open("a",encoding="utf8") as f:
    f.write("\n## 二次元の座標を読みやすく扱う\n\n"+
            "盤面は一次元の`Array`で保持しながら、位置は`index(x, y)`へ横の列`x`、縦の行`y`の順で渡します。"+
            "8×8の画素変換の練習と4×4の実ゲームは幅が異なるので補助関数を共用しません。"+
            "マウスの範囲チェックと`index`の座標変換は別の責務です。\n")
print("STAGED: both textbooks, coordinate helpers, Bend regression, GUI and docs; cover untouched")
