#!/usr/bin/env python3
"""One-off, validation-branch-only integration of issue #6 into intermediate lessons."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def edit(path, before, after):
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    assert source.count(before) == 1, (path, "expected exactly one anchor", source.count(before))
    file.write_text(source.replace(before, after), encoding="utf-8")

lesson = r"""\section{空のチャネルを試して、受信待ちを見分ける}
チャネルからまだ値が届かないとき、そこで待ち続けると画面の更新など別の仕事へ戻れません。しかし、\code{まだ届かない}ことと、\code{もう届かない}ことは違います。実際に\code{Chan.try_recv}を二度呼び出して確かめましょう。

\sample{53_chan_poll.bend}{空のチャネルを調べ、9を送ってから再び受信する}
\begin{lstlisting}[language={},caption={Pollの受信を試す}]
bend examples/53_chan_poll.bend
\end{lstlisting}

\begin{lstlisting}[language={},caption={実行結果}]
0
9
\end{lstlisting}

最初に\code{Chan.new(U32,1)}で容量1のチャネルを作ります。何も送っていない状態で\code{Chan.try_recv(U32,chan,0)}を呼ぶと、待機時間0ミリ秒の試行は\code{Wait{Unit{}}}になります。そこで9を送った後の二度目の試行は\code{Ready{Some{9}}}となり、受信した9を取り出せます。二行の表示は、この二つの状態に対応します。

サンプル内の\code{poll_number}は、\code{Wait}なら表示用に0を返し、\code{Ready{Some{number}}}ならその数値を返します。\textbf{0はPollの返り値そのものではありません。}受信した数値0でも表示は0になるため、実際のアプリケーションでは\code{match}の分岐を保ったまま扱いましょう。また、\code{Ready{None{}}}はチャネルが閉じて受信できる値が残っていない状態ですが、このプログラムは閉じた後の受信を試していません。

\exercise{\code{53_chan_poll.bend}で送る9を17に変えて実行してみましょう。最初の0はなぜ変わらないのでしょうか。次に、表示用の0と、本当に数値0を受信した場合を区別するには、\code{poll_number}をどう変更すればよいか考えてみましょう。}

\begin{pointbox}
この実習で確認したのは、\textbf{空のチャネルでの\code{Wait}と送信後の\code{Ready{Some}}}です。閉鎖後の受信、送信側の待機、時間の競合、仕事の取り消しまで検証したわけではありません。
\end{pointbox}

"""
edit("intermediate/Intermediate_Textbook.tex", r"\section{いつ使うべきか}", lesson+r"\section{いつ使うべきか}")
fixture = ROOT / "intermediate/tests/fixtures/chan_poll.bend"
sample = ROOT / "intermediate/src/53_chan_poll.bend"
assert fixture.is_file() and not sample.exists()
sample.write_bytes(fixture.read_bytes())
fixture.unlink()
edit("intermediate/scripts/test_examples.py",
'    poll_output = run("bend", str(ROOT / "tests/fixtures/chan_poll.bend"))\n    if poll_output.splitlines() != ["0", "9"]:\n        raise AssertionError(f"Poll mismatch: {poll_output!r}")',
'    # Reader-facing Poll example: check BOTH observed lines.\n    poll_output = run("bend", str(SAMPLES / "53_chan_poll.bend"))\n    if poll_output.splitlines() != ["0", "9"]:\n        raise AssertionError(f"Poll expected Wait=0 and Ready(Some(9))=9; got {poll_output!r}")\n    print("PASS Chan.try_recv Wait then Ready(Some(9)) = 0,9", flush=True)')
structure = r'''    def test_poll_lesson_has_executable_source_and_limits(self):
        book = BOOK.read_text(encoding="utf-8")
        chapter9 = re.split(r"\\chapter\{[^}]+\}", book)[9]
        self.assertEqual(book.count(r"\sample{53_chan_poll.bend}"), 1)
        for phrase in (r"\section{空のチャネルを試して、受信待ちを見分ける}",
                       "bend examples/53_chan_poll.bend", "0\n9",
                       "Wait{Unit{}}", "Ready{Some{9}}", "閉じた後の受信を試していません"):
            self.assertIn(phrase, chapter9)
        code = (SRC / "53_chan_poll.bend").read_text(encoding="utf-8")
        self.assertIn("Chan.try_recv(U32, chan, 0)", code)
        self.assertIn("Chan.send(U32, chan, 9)", code)

'''
edit("intermediate/tests/test_structure.py",
     "    def test_timeout_lesson_distinguishes_three_outcomes(self):",
     structure+"    def test_timeout_lesson_distinguishes_three_outcomes(self):")
edit("scripts/build_reader_bundle.py",
     '    "51_atomic_counter.bend", "52_pair_exists.bend",',
     '    "51_atomic_counter.bend", "52_pair_exists.bend",\n    "53_chan_poll.bend",')
edit("intermediate/README.md",
     "bend examples/02_map.bend\nbend examples/04_flag_laws.bend --verdict",
     "bend examples/02_map.bend\nbend examples/53_chan_poll.bend\nbend examples/04_flag_laws.bend --verdict")
edit("intermediate/README.md",
     "通常サンプル52本（import用補助モジュール1本を含む）",
     "通常サンプル53本（import用補助モジュール1本を含む）")
with (ROOT/"intermediate/README.md").open("a",encoding="utf-8") as f:
    f.write("\n## 第9章：値を待つPollの実習\n\n"+
    "`53_chan_poll.bend` は空のチャネルへの `Chan.try_recv` と、9を送った後の再受信を比較します。出力は二行で `0` と `9`。表示の0は `Wait` に対応させた便宜的な値です。受信データ0とは区別して扱ってください。閉鎖後の受信や送信側の待機は未検証です。\n")
edit("intermediate/COVERAGE.md",
'| `IO.fork/join`, `Chan` | 第9章 | `21_io_fork.bend`、`28_chan_roundtrip.bend` | fork/joinとChan送受信・closeの実行照合。失敗・時間制限の実践は今後 |',
'| `IO.fork/join`, `Chan` | 第9章 | `21_io_fork.bend`、`28_chan_roundtrip.bend`、`53_chan_poll.bend` | fork/join、送受信・close、空の受信/送信後のPollを実行照合。閉鎖後の受信・送信待機・取消は今後 |')
edit("intermediate/COVERAGE.md",
'| `IO.within`, `Poll` | 第9章（時間切れ・仕事の非取消・Ready/Waitを型に沿って解説） | `29_io_within.bend` | withinのSome/None処理は型検査済み。PollはBaseのtry_send/try_recvの返り値を解説した段階で、実行サンプルと時間制限の実機挙動は未検証 |',
'| `IO.within`, `Poll` | 第9章（時間切れ・仕事の非取消・Ready/Waitを型に沿って解説） | `29_io_within.bend`、`53_chan_poll.bend` | withinのSome/None処理は型検査済み。Pollは空のWaitと9のReady{Some}を実行照合済み。閉鎖後のReady{None}、try_sendの待機、時間の競合は未検証 |')
edit("intermediate/COVERAGE.md",
"## 第9章のPoll補稿（2026-10-18）\n\n検証用 `tests/fixtures/chan_poll.bend` で空の受信と送信後の受信を実行照合する。補稿は `manuscript/09_Poll実習.md`。読者PDFとZIPには未収録であり、完成とは扱わない。",
"## 第9章のPoll実行教材（2026-10-19）\n\n`53_chan_poll.bend` は空の受信の `Wait` と9送信後の `Ready{Some{9}}` を二行の `0`・`9` で照合。TeX第9章へ必要性・コード・結果・説明・演習を統合。表示用0と実際の受信値0を混同しない。閉鎖後の `Ready{None}`、`try_send` の待機、時間競合は未検証。")
with (ROOT/"intermediate/manuscript/STATUS.md").open("a",encoding="utf-8") as f:
    f.write("\n## 2026-10-19：第9章Poll実行例を本編へ統合（Issue #6）\n\n"+
    "- 検証用 `chan_poll.bend` を読者向け `src/53_chan_poll.bend` として整理。空の受信と9送信後の再受信を0・9の二行で照合。表示用0は `Wait` の便宜的表現で、受信値0とは別。\n"+
    "- 第9章へ必要性→実行コード→実測結果→返り値の仕組み→演習を追加。`Ready{None}`・送信側の待機・時間競合は未検証。\n"+
    "- 読者ZIPは通常サンプル53本・ゲーム実習12本・PDF/README/LICENSE、合計68エントリ。解答・内部テストはZIP外。\n"+
    "- 表紙 `cover_art.tex`（blob `ba9b5c4c...`）は不変更。TeX・PDF・ZIPを検証ブランチで検収後にPRへ一括反映。\n")
edit("intermediate/manuscript/09_Poll実習.md",
     "この補稿は本文への統合前の実行教材です。採用済み表紙と配布PDF・ZIPは変更しません。",
     "この補稿の要点は教科書第9章と読者ZIPへ統合済みです。補足確認用の資料として残します。採用済み表紙は変更しません。")
edit("intermediate/manuscript/09_Poll実習.md",
     "`intermediate/tests/fixtures/chan_poll.bend` を使います。",
     "読者ZIPの `examples/53_chan_poll.bend`（リポジトリでは `intermediate/src/53_chan_poll.bend`）を使います。")
edit("intermediate/manuscript/09_Poll実習.md",
     "bend intermediate/tests/fixtures/chan_poll.bend",
     "bend examples/53_chan_poll.bend")
with (ROOT/"intermediate/solutions/05_10_io_exercises.md").open("a",encoding="utf-8") as f:
    f.write("\n## 第9章補足：Pollの実行例\n\n"+
    "- `53_chan_poll.bend` で9を17に変えると出力は0と17です。送信前の受信は `Wait` なので一行目は不変。\n"+
    "- 受信値0と `Wait` を同じ0に写すと情報を失います。`Poll` / `Maybe` の分岐を保持するか、`Waiting`・`Received 0`・`Closed` と表示を分けます。\n"+
    "- この実習は閉鎖後の `Ready{None}` や送信側の待機を実行検証していません。\n")
bundle_test = r'''    def test_poll_example_is_learner_material(self):
        self.assertIn("53_chan_poll.bend", INTERMEDIATE_EXAMPLES)
        with zipfile.ZipFile(ROOT / "reader-packages/bend2-intermediate-reader-preview.zip") as z:
            name = "bend2-intermediate-reader/examples/53_chan_poll.bend"
            self.assertEqual(z.read(name),
                             (ROOT / "intermediate/src/53_chan_poll.bend").read_bytes())

'''
edit("tests/test_reader_bundle.py",
     "    def test_pair_exists_sample_when_bend_is_installed(self):",
     bundle_test+"    def test_pair_exists_sample_when_bend_is_installed(self):")
print("STAGED: chapter 9, source, tests, allowlist, notes and reference answers; cover untouched")
