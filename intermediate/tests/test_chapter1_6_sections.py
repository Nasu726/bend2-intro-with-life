"""Chapters 1-6: section/source contracts and independent finite calculations.

Static checks only, not new Bend execution or proof.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{([^}\n]+)\}", re.M)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.M)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")

def chapter_sections(number):
    tex = (ROOT / "Intermediate_Textbook.tex").read_text(encoding="utf-8")
    chapters = list(CHAPTER.finditer(tex))
    if len(chapters) != 23:
        raise AssertionError(f"Expected 23 chapters, got {len(chapters)}")
    body = tex[chapters[number - 1].end():
               chapters[number].start() if number < len(chapters) else len(tex)]
    marks = list(SECTION.finditer(body))
    return [(m.group(1), body[m.end():marks[i+1].start() if i+1 < len(marks) else len(body)])
            for i, m in enumerate(marks)]

def source(name):
    return (ROOT / "src" / name).read_text(encoding="utf-8")

class FirstSixChaptersReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chapters = {n: chapter_sections(n) for n in range(1, 7)}

    def test_34_sections_and_exercise_counts(self):
        self.assertEqual([len(self.chapters[n]) for n in range(1, 7)], [4, 5, 7, 8, 6, 4])
        self.assertEqual(sum(body.count(r"\exercise{") for rows in self.chapters.values()
                             for _, body in rows), 10)

    def test_sample_refs_match_chapter_scope(self):
        expected = {
            1: [],
            2: ["37_u32_dimension.bend", "15_string_parse.bend", "35_string_fields.bend"],
            3: ["03_list.bend", "40_list_map.bend", "17_list_pipeline.bend",
                "38_list_sort.bend", "18_array_mutations.bend",
                "39_array_to_list.bend", "30_array_clone.bend"],
            4: ["01_set.bend", "05_marking.bend", "02_map.bend",
                "36_map_missing.bend", "16_map_set_api.bend",
                "49_map_update_delete.bend", "50_set_from_list.bend"],
            5: ["22_result_and_game.bend", "52_pair_exists.bend", "25_either_case.bend"],
            6: [],
        }
        for n, names in expected.items():
            actual = [name for _, body in self.chapters[n] for name in SAMPLE.findall(body)]
            self.assertEqual(actual, names, f"Chapter {n}")
            for name in names:
                with self.subTest(chapter=n, sample=name):
                    self.assertIn("def main()", source(name))

    def test_chapter1_base_and_affine_return(self):
        text = "\n".join(body for _, body in self.chapters[1])
        for phrase in ("bend base Set.has", "bend base Map.get", "bend base Array.get",
                       "Set() ", "Set.has(s1", "Set.add(again", "失敗の表現"):
            self.assertIn(phrase, text)
        self.assertIn("Set() & Bool", source("01_set.bend"))

    def test_chapter2_numeric_and_parse_boundaries(self):
        text = "\n".join(body for _, body in self.chapters[2])
        for phrase in ("U32.from_nat(4n)", "U32.is_lt(width,16)", "42",
                       "None", "Chr{61}", "board-size=abc", "F32"):
            self.assertIn(phrase, text)
        self.assertIn("U32.read(cleaned)", source("15_string_parse.bend"))
        self.assertIn('String.split("board-size=4", Chr{61})', source("35_string_fields.bend"))
        self.assertEqual(len("board-size=4".split("=")), 2)
        self.assertEqual(len("board-size=4=extra".split("=")), 3)

    def test_chapter3_list_and_array_examples(self):
        text = "\n".join(body for _, body in self.chapters[3])
        for phrase in ("3n", "9", "List.filter", "List.sort", "17", "10", "22",
                       "要素数ではなく深さ", "Array.fork"):
            self.assertIn(phrase, text)
        self.assertIn("List.map(~U32", source("40_list_map.bend"))
        self.assertIn("Nat.is_lt(n, 3n)", source("17_list_pipeline.bend"))
        self.assertIn("Array.new(U32, 3n, 0)", source("18_array_mutations.bend"))
        self.assertIn("Array.clone(U32, source)", source("30_array_clone.bend"))
        self.assertEqual(sum(x + 1 for x in [1, 2, 3]), 9)
        self.assertEqual(sum(x for x in range(4) if x < 3), 3)
        self.assertEqual(sum([7, 1, 1, 1]), 10)
        self.assertEqual(17 + 5, 22)

    def test_chapter4_map_set_results_and_ownership(self):
        text = "\n".join(body for _, body in self.chapters[4])
        for phrase in ("Map.has", "Map.get", "Map.del", "Map.size", "Set.from_list",
                       "Set.to_list", "順序", "False", "9", "2n"):
            self.assertIn(phrase, text)
        code = source("49_map_update_delete.bend")
        self.assertIn('Map.set(&2, U32, m2, "wins", 8)', code)
        self.assertIn('Map.del(&2, U32, m3, "games")', code)
        self.assertEqual(8 + 0 + 1, 9)
        self.assertEqual(12 + 0 + 1, 13)
        self.assertEqual(8 + 1 + 2, 11)
        self.assertEqual(len(set(["0,0", "1,1", "0,0"])), 2)

    def test_chapter5_result_pair_exists_and_either(self):
        text = "\n".join(body for _, body in self.chapters[5])
        for phrase in ("Some{0}", "None{}", "Result", "Pair", "Exists", "Either",
                       "型検査に成功したこと", "5", "Inl", "Inr"):
            self.assertIn(phrase, text)
        self.assertIn('Fail{"an open square cannot be flagged"}',
                      source("22_result_and_game.bend"))
        self.assertIn("Tuple{2n, {==}}", source("52_pair_exists.bend"))
        self.assertIn("meaning(Inl{7})", source("25_either_case.bend"))
        self.assertEqual(1 + 2 + 2, 5)

    def test_chapter6_io_and_pure_game_boundary(self):
        text = "\n".join(body for _, body in self.chapters[6])
        for phrase in ("IO(Unit)", "IO.args()", "IO.try", "Result", "純粋関数",
                       "IO.pure", "第7章", "第8章", "第9章"):
            self.assertIn(phrase, text)
        args = source("08_args.bend")
        for phrase in ("def main() -> IO(Unit):", "do IO<Unit>:",
                       "xs: List<String> <- IO.args()", "IO.print(Nat.show("):
            self.assertIn(phrase, args)
        self.assertNotIn("IO.random_u32", source("22_result_and_game.bend"))

if __name__ == "__main__":
    unittest.main()
