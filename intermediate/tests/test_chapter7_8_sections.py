"""Section-level regression for the chapter-7 File and chapter-8 IO lessons.

This checks reader-facing source references and bounded claims, not runtime
correctness, general EOF behavior, or clock precision. The Bend/CI runners
remain responsible for executing the examples.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{[^}\n]+\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")


def chapter_body(source: str, number: int) -> str:
    chapters = list(CHAPTER.finditer(source))
    if len(chapters) != 23:
        raise AssertionError(f"Expected 23 chapters, got {len(chapters)}")
    begin = chapters[number - 1].end()
    end = chapters[number].start() if number < len(chapters) else len(source)
    return source[begin:end]


def sections(body: str) -> list[tuple[str, str]]:
    headers = list(SECTION.finditer(body))
    return [
        (header.group(1),
         body[header.end():headers[i + 1].start() if i + 1 < len(headers) else len(body)])
        for i, header in enumerate(headers)
    ]


class FileClockSectionReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tex = (ROOT / "Intermediate_Textbook.tex").read_text(encoding="utf-8")
        cls.chapter7 = chapter_body(tex, 7)
        cls.chapter8 = chapter_body(tex, 8)
        cls.file_sections = sections(cls.chapter7)
        cls.clock_sections = sections(cls.chapter8)

    def test_chapter7_eight_sections_and_reader_samples(self):
        expected = [
            ("保存するには、どんな順序が必要だろうか", []),
            ("ファイルを開き、書き込んで閉じる", ["12_file_write.bend"]),
            ("成功と失敗を型で追う", []),
            ("読み戻せたら保存を確認できる", ["13_file_read.bend"]),
            ("古い保存を上書きし、失敗も確かめる", []),
            ("文字ではなくバイトを保存する", ["45_binary_file.bend"]),
            ("短いバイト列を分割して終端を確かめる", ["54_binary_chunks.bend"]),
            ("マインスイーパーの保存に応用する", []),
        ]
        self.assertEqual(
            [(title, SAMPLE.findall(body)) for title, body in self.file_sections],
            expected,
        )
        for name in ("12_file_write.bend", "13_file_read.bend",
                     "45_binary_file.bend", "54_binary_chunks.bend"):
            with self.subTest(sample=name):
                self.assertTrue((ROOT / "src" / name).is_file())

    def test_chapter7_outputs_and_finite_eof_boundary(self):
        body = dict(self.file_sections)
        for phrase in ("board-size=4", "mines=1,1"):
            self.assertIn(phrase, body["読み戻せたら保存を確認できる"])
        binary = body["文字ではなくバイトを保存する"]
        for phrase in ("00 0a 0d ff", "ちょうど4バイト", "最大量"):
            self.assertIn(phrase, binary)
        chunks = body["短いバイト列を分割して終端を確かめる"]
        for phrase in ("4回目の空リスト", "0〜5バイトの通常ファイル",
                       "有限の実行検査", "パイプやソケット"):
            self.assertIn(phrase, chunks)
        self.assertIn("2\n2\n0\n0", chunks)

    def test_chapter8_five_sections_and_reader_samples(self):
        expected = [
            ("環境変数は常に存在するとは限らない", ["19_environment.bend"]),
            ("時計と待機を組み合わせる", ["46_elapsed_clock.bend"]),
            ("待機時間の境界を実際に測る", ["55_clock_intervals.bend"]),
            ("乱数の取得と失敗の伝播", ["11_random_io.bend"]),
            ("外部プログラムを起動する", ["20_process_run.bend"]),
        ]
        self.assertEqual(
            [(title, SAMPLE.findall(body)) for title, body in self.clock_sections],
            expected,
        )
        self.assertIn(r"\sample{08_args.bend}", self.chapter8)
        for _, names in expected:
            for name in names:
                with self.subTest(sample=name):
                    self.assertTrue((ROOT / "src" / name).is_file())

    def test_chapter8_variable_results_and_platform_boundary(self):
        body = dict(self.clock_sections)
        self.assertIn("値そのものではなく長さ", body["環境変数は常に存在するとは限らない"])
        elapsed = body["時計と待機を組み合わせる"]
        for phrase in ("IO.now()", "IO.sleep(20)", "固定の期待値ではありません"):
            self.assertIn(phrase, elapsed)
        intervals = body["待機時間の境界を実際に測る"]
        for phrase in ("合計6行", "3回実行", "有限の受入検査",
                       "すべてのOS", "固定の6個の数値"):
            self.assertIn(phrase, intervals)
        self.assertIn("固定して比較するテストには不向き", body["乱数の取得と失敗の伝播"])
        process = body["外部プログラムを起動する"]
        for phrase in ("/usr/bin/true", "Windows", "0以外の終了コード"):
            self.assertIn(phrase, process)

    def test_distributed_samples_match_bend_verified_fixtures(self):
        for sample, fixture in (
            ("54_binary_chunks.bend", "binary_chunks.bend"),
            ("55_clock_intervals.bend", "clock_intervals.bend"),
        ):
            with self.subTest(sample=sample):
                self.assertEqual(
                    (ROOT / "src" / sample).read_bytes(),
                    (ROOT / "scripts" / "fixtures" / fixture).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
