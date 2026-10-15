import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reference import SIZE, GLIDER, step, render, transcript


class LifeReferenceTests(unittest.TestCase):
    def test_empty_stays_empty(self):
        self.assertEqual(step(set()), set())

    def test_block_is_still_life(self):
        block = {(3,3),(3,4),(4,3),(4,4)}
        self.assertEqual(step(block), block)

    def test_blinker_oscillates(self):
        horizontal = {(3,3),(4,3),(5,3)}
        vertical = {(4,2),(4,3),(4,4)}
        self.assertEqual(step(horizontal), vertical)
        self.assertEqual(step(vertical), horizontal)

    def test_glider_moves_diagonally_in_four(self):
        b = set(GLIDER)
        for _ in range(4): b = step(b)
        self.assertEqual(b, {((x+1)%SIZE,(y+1)%SIZE) for x,y in GLIDER})
        self.assertIn((2,3), b)

    def test_alive_count_preserved_by_glider_cycle(self):
        b = set(GLIDER)
        for _ in range(12):
            self.assertEqual(len(b),5)
            b = step(b)

    def test_transcript_five_snapshots(self):
        self.assertEqual(transcript().count('generation '), 5)
        self.assertTrue(transcript().endswith('done\n'))


if __name__ == '__main__':
    unittest.main()
