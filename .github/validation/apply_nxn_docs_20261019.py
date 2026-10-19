#!/usr/bin/env python3
"""One-off verification-branch transformation. Never touch the adopted cover."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def edit(path,old,new):
    p=ROOT/path
    s=p.read_text(encoding="utf8")
    assert s.count(old)==1,(path,old[:90],s.count(old))
    p.write_text(s.replace(old,new),encoding="utf8")
def append(path,s):
    p=ROOT/path
    with p.open("a",encoding="utf8") as stream:
        stream.write("\n"+s+"\n")

lesson=r"""\section{10×10の盤面では、配列の余りを使わない}
先ほどの4×4実装は、全16マスを調べる法則や反例を確かめる\textbf{検証用の小例}です。実際に遊ぶゲームはN×Nを基本とし、本書では\textbf{N=10、100マス}を例にします。

\code{Array.new}の第2引数は個数ではなく深さです。100要素ぴったりの深さはないので、深さ7で128要素を確保し、\textbf{0から99までだけ}をゲームのマスとして扱います。残る100から127は、格納領域が存在しても\textbf{盤面の外}です。

\begin{lstlisting}[caption={N×N用の座標変換（board_n.bendより）}]
def index(n: U32, x: U32, y: U32) -> U32:
  (y * n + x : U32)
\end{lstlisting}

\code{x}が列、\code{y}が行である点は前巻と同じです。盤面の幅も指定するため\code{n}を引数に加えています。N=10なら\code{index(10,9,9)}は99です。ただし\code{index}自体では範囲検査をしません。

\begin{lstlisting}[language={},caption={N=10で確保した配列と旗の挙動}]
bend examples/minesweeper/nxn_layout_demo.bend
128
1
9
\end{lstlisting}

一行目の128は物理的な配列の長さです。99番に旗を立て、100番への旗操作も試しますが、100番は無効なので99番の旗は残り、二行目が1になります。三行目の9は、100番への読み取りで返る\code{None}を表示のために数値へ置き換えた結果です。9というマスの値を読んだわけではありません。

\code{board_n.bend}はN=2〜32を受け入れ、地雷の真値を\code{Array<Bool>}、表示状態を\code{Array<Game.Square>}として分離します。10×10では16ビットの地雷マスクを使えないためです。サイズ10の有効な位置・余剰位置・操作の拒否など、11個の\code{law}を別ファイルで検証します。

\begin{pointbox}
\textbf{まだ完成した10×10ゲームではありません。}今回動いたのは盤面の確保、境界検査、旗操作だけです。初手安全、数字の計算、0領域の連鎖公開、勝敗、GUIはまだN×Nへ移植していません。4×4の既存実装は証明・有限テスト用に維持します。
\end{pointbox}

\exercise{N=12では有効なマスは何個で、\code{Array.new}の深さはいくつ必要でしょうか。N=10の99番と100番の違いを説明した後、実行結果の9が\code{None}とどう対応しているか確かめてみましょう。}

"""
edit("intermediate/Intermediate_Textbook.tex",r"\chapter{表示と入力をテストする}",lesson+r"\chapter{表示と入力をテストする}")
edit("intermediate/README.md","bend examples/minesweeper/gui.bend -o minesweeper","bend examples/minesweeper/nxn_layout_demo.bend\nbend examples/minesweeper/gui.bend -o minesweeper")
edit("intermediate/README.md","通常サンプル53本（import用補助モジュール1本を含む）とゲーム実習12本","通常サンプル53本（import用補助モジュール1本を含む）とゲーム実習14本")
append("intermediate/README.md","""## N×N盤面の基礎実習

`examples/minesweeper/nxn_layout_demo.bend`はN=10の論理100マス・物理128要素を区別します。出力は`128`、`1`、`9`（無効な読み取り`None`の表示用符号）です。
`board_n.bend`はN=2〜32のサイズを受け付け、地雷は`Array<Bool>`、表示は`Array<Game.Square>`に分離します。現段階は盤面の確保・境界・旗操作のみです。**10×10を遊べる完成ゲームではありません。**初手安全・0展開・勝敗・GUIの移植は今後の課題です。法則と証明はリポジトリだけにあり、読者ZIPには参考解答を含めません。""")
append("intermediate/COVERAGE.md","""## N×N基礎エンジンの検証（2026-10-19）

`minesweeper/board_n.bend`はN=2〜32のパディング付き一次元配列、旗・安全な読み取りを実装。`NXN_LAWS.bend`の11法則と同名の証明を`NXN_PROOF.bend`で検査する。N=10の128要素中100マスのみ有効、無効100/127の操作拒否を確認。既存の4×4・43法則とは別。汎用初手安全・0連鎖・勝敗・GUI・運ゲー無しは未実装、未証明。""")
append("intermediate/manuscript/STATUS.md","""## 2026-10-19：N×NのBend盤面コア（検証・配布物同期）

- N=2〜32の`board_n.bend`、11 lawの`NXN_LAWS.bend`と証明`NXN_PROOF.bend`、読者用`nxn_layout_demo.bend`を追加。
- N=10は`Array.new`深さ7、128スロット中100のみ有効。99番の旗、100番の拒否、`Maybe`の`None`返却を実行照合。
- 4×4固定のゲームと43件の証明は維持。N×Nの全ゲームロジック、10×10 GUIや運ゲー無しソルバーの一般化は未完。
- 第13章へ必要性・実コード・実測結果・仕組み・演習を追加し、PDF/ZIPを再生成。採用済み表紙`cover_art.tex`は変更しない。""")
append("intermediate/minesweeper/REQUIREMENTS.md","""## N×NのBendコア第一段階（2026-10-19）

`board_n.bend`はN=2〜32の安全なサイズ入力と、地雷真値`Array<Bool>`・公開表示`Array<Game.Square>`を保持する。N=10なら物理128要素のうち0〜99だけを有効とする。`mark_checked`は100/127を無視し、`read_checked`は`None`を返す。検証用の`NXN_LAWS.bend`の11法則を`NXN_PROOF.bend --verdict`で証明済み。底辺の全xを量化した一般境界法則など、未形式化の部分はPythonの有限検査のみ。4×4の既存法則・証明には変更を加えない。

この段階は**ゲームの土台であり10×10のプレイ可能なゲームではない**。公開情報の分離、数字・0展開・勝敗・初手安全・GUIのN×N化と実機確認は残る。""")
append("intermediate/COMPLETION_PLAN.md","""## 2026-10-19：N×Nの基礎実装の到達点

N×NのBend盤面コア、サイズ検査、論理マスと余剰スロットの分離、旗操作、11 lawの証明とN=10実習を追加した。第13章本文・PDF・ZIPを同期する。最終ゲームの初手安全・数字・連鎖公開・勝敗・10×10 GUIは実装・実機検収が必要。従来4×4の有限検査は残す。""")
edit("scripts/build_reader_bundle.py",
     '    "noguess_generator.bend", "cli_save.bend",',
     '    "noguess_generator.bend", "cli_save.bend",\n    "board_n.bend", "nxn_layout_demo.bend",')
edit("scripts/build_reader_bundle.py","4×4盤面のCLIリプレイ実習（対話入力ではなく引数を一括指定）:",
     "10×10の盤面記憶領域の実習（まだ遊べるゲームではありません）:\nbend examples/minesweeper/nxn_layout_demo.bend\n出力は128、1、9（9はNoneの表示用符号）。\n\n4×4盤面のCLIリプレイ実習（対話入力ではなく引数を一括指定）：")
test=r'''    def test_nxn_core_lesson_and_proofs(self):
        from build_reader_bundle import INTERMEDIATE_GAME_FILES
        book = BOOK.read_text(encoding="utf8")
        self.assertIn("10×10の盤面では、配列の余りを使わない", book)
        self.assertIn("bend examples/minesweeper/nxn_layout_demo.bend", book)
        self.assertIn("100から127", book)
        self.assertIn("まだ完成した10×10ゲームではありません", book)
        self.assertIn("board_n.bend", INTERMEDIATE_GAME_FILES)
        self.assertIn("nxn_layout_demo.bend", INTERMEDIATE_GAME_FILES)
        self.assertNotIn("NXN_PROOF.bend", INTERMEDIATE_GAME_FILES)
        laws=(ROOT/"minesweeper/NXN_LAWS.bend").read_text(encoding="utf8")
        proof=(ROOT/"minesweeper/NXN_PROOF.bend").read_text(encoding="utf8")
        declared=set(re.findall(r"^law (\w+):", laws, re.M))
        proved=set(re.findall(r"^def Laws\.(\w+)\(", proof, re.M))
        self.assertEqual(declared,proved)
        self.assertEqual(len(declared),11)

'''
edit("intermediate/tests/test_structure.py",
     "    def test_timeout_lesson_distinguishes_three_outcomes(self):",
     test+"    def test_timeout_lesson_distinguishes_three_outcomes(self):")
edit("intermediate/scripts/test_examples.py",
     '    print("PASS Minesweeper law proof gate (43 laws, including zero cascade)", flush=True)',
     '''    # Preserve the old 4x4 proof gate; N x N contracts are an independent scope.
    nxn = run("bend", str(game / "nxn_layout_demo.bend")).splitlines()
    if nxn != ["128","1","9"]:
        raise AssertionError(f"N x N board expected 128/1/9; got {nxn!r}")
    nxn_verdict = run("bend", str(game / "NXN_PROOF.bend"), "--verdict")
    if "ALL PROOFS CHECK" not in nxn_verdict:
        raise AssertionError(f"N x N laws not fully verified: {nxn_verdict}")
    print("PASS N=10: 128 storage / flag at 99 / padding 100 rejected", flush=True)
    print("PASS 11 N x N laws, independently of 43 existing 4x4 laws", flush=True)
    print("PASS Minesweeper law proof gate (43 laws, including zero cascade)", flush=True)''')
bundle_test=r'''    def test_nxn_core_in_reader_zip_not_proof_solution(self):
        self.assertIn("board_n.bend", INTERMEDIATE_GAME_FILES)
        self.assertIn("nxn_layout_demo.bend", INTERMEDIATE_GAME_FILES)
        self.assertNotIn("NXN_PROOF.bend", INTERMEDIATE_GAME_FILES)
        with zipfile.ZipFile(ROOT / "reader-packages/bend2-intermediate-reader-preview.zip") as z:
            prefix = "bend2-intermediate-reader/examples/minesweeper/"
            for name in ("board_n.bend", "nxn_layout_demo.bend"):
                self.assertEqual(z.read(prefix + name),
                                 (ROOT/"intermediate/minesweeper"/name).read_bytes())

'''
edit("tests/test_reader_bundle.py","    def test_pair_exists_sample_when_bend_is_installed(self):",
     bundle_test+"    def test_pair_exists_sample_when_bend_is_installed(self):")
print("STAGED N x N lesson, full source, requirements, structural/runtime tests, allowlisted reader files; approved cover untouched")
