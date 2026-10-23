"""Finite public-state replay fixtures; not Bend execution or a general proof."""
from collections import deque
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solutions"))
from nxn_replay_vectors import render_replay, replay_vectors
import nxn_board_oracle as board

MINES_10 = frozenset({4, 29, 34, 36, 37, 49, 50, 56, 72, 77})
CLICKS_10 = (0, 14, 5, 6, 24, 35, 38, 39, 46, 47, 48, 57, 67)


def independent_replay(n, mines, clicks):
    """A queue-based, coordinate-oriented independent public-state oracle."""
    opened = {}
    for click in clicks:
        queue = deque([click])
        while queue:
            cell = queue.popleft()
            if cell in opened:
                continue
            y, x = divmod(cell, n)
            near = {yy * n + xx for yy in range(n) for xx in range(n)
                    if max(abs(xx - x), abs(yy - y)) == 1}
            clue = len(near & mines)
            opened[cell] = clue
            if clue == 0:
                queue.extend(sorted(near - mines - opened.keys()))
        yield tuple(sorted(opened.items()))


class ReplayVectorTests(unittest.TestCase):
    def test_ten_by_ten_public_frames_against_independent_queue(self):
        frames = replay_vectors(10, MINES_10, CLICKS_10)
        self.assertEqual(len(frames), 13)
        previous = set()
        for frame, expected in zip(frames, independent_replay(10, MINES_10, CLICKS_10)):
            self.assertEqual(frame.opened, expected)
            current = dict(frame.opened)
            self.assertEqual(dict(frame.newly_opened),
                             {i: clue for i, clue in current.items() if i not in previous})
            self.assertFalse(current.keys() & MINES_10)
            self.assertEqual(set(current),
                             {i for word, bits in enumerate(frame.opened_words)
                              for bit in range(32) if bits & (1 << bit) for i in [word * 32 + bit]})
            self.assertEqual(frame.phase, "Won" if len(current) == 90 else "Playing")
            previous = set(current)
        self.assertEqual(len(frames[0].opened), 66)
        self.assertEqual(frames[0].opened_words,
                         (0xc0f03c0f, 0xfcf83f03, 0xffffdef7, 0x0000000f))
        self.assertEqual(len(frames[-1].opened), 90)
        self.assertEqual(frames[-1].opened_words,
                         (0xdfffffef, 0xfef9ffcb, 0xffffdeff, 0x0000000f))
        self.assertEqual(frames[-1].phase, "Won")
        self.assertEqual(len(frames[-1].opened_words), 4)
        self.assertEqual(frames[-1].opened_words[-1] >> 4, 0)  # 100 logical cells.

    def test_ten_by_ten_matches_existing_game_oracle_every_step(self):
        frames = replay_vectors(10, MINES_10, CLICKS_10)
        state = board.new_game(10, MINES_10)
        for frame in frames:
            state = board.click(state, frame.click)
            self.assertEqual(state.opened, frame.opened)
            self.assertEqual(state.phase, frame.phase)
            self.assertEqual(state.mines, MINES_10)
            self.assertEqual(board.public_view(state).opened, frame.opened)

    def test_four_by_four_small_board_and_empty_mines(self):
        frames = replay_vectors(4, frozenset({13, 15}), (0, 12, 14))
        self.assertEqual(frames[-1].phase, "Won")
        self.assertEqual(len(frames[-1].opened), 14)
        self.assertEqual(frames[-1].opened_words, (0x5fff,))
        self.assertEqual(replay_vectors(10, frozenset(), (0,))[0].phase, "Won")

    def test_packed_words_across_32_bit_and_padding_boundaries(self):
        for n in (2, 3, 4, 10, 17, 100):
            last = n * n - 1
            frame = replay_vectors(n, frozenset({last}), (0, 1, 2) if n == 2 else (0,))[-1]
            self.assertEqual(frame.phase, "Won")
            self.assertEqual(len(frame.opened), last)
            self.assertEqual(len(frame.opened_words), (n * n + 31) // 32)
            self.assertEqual(sum(w.bit_count() for w in frame.opened_words), last)
            self.assertEqual(frame.opened_words[last // 32] & (1 << (last % 32)), 0)
            self.assertEqual(frame.opened_words[-1] >> (n * n % 32 or 32), 0)

    def test_rejects_invalid_and_incomplete_trace(self):
        for args in ((10, MINES_10, CLICKS_10[:-1]),
                     (10, MINES_10, (0, 4)),
                     (10, MINES_10, (0, 99)),
                     (10, MINES_10, CLICKS_10 + (67,)),
                     (10, MINES_10, (0, True)),
                     (True, frozenset(), (0,)),
                     (10, frozenset({True}), (0,)),
                     (10, frozenset(), [0]),
                     (10, frozenset(), ()),
                     (10, frozenset(range(100)), (0,))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                replay_vectors(*args)

    def test_render_is_deterministic_and_public_only(self):
        frames = replay_vectors(10, MINES_10, CLICKS_10)
        lines = render_replay(frames).splitlines()
        self.assertEqual(len(lines), 13)
        self.assertTrue(lines[0].startswith("step=0;click=0;opened="))
        self.assertIn("phase=Won", lines[-1])
        self.assertNotIn("mines=", render_replay(frames))
        # Reconstruct every public clue from the wire-format delta alone.
        reconstructed = {}
        for line, frame in zip(lines, frames):
            additions = line.split(";new=", 1)[1]
            for entry in additions.split(","):
                i, clue = entry.split(":")
                self.assertNotIn(int(i), reconstructed)
                reconstructed[int(i)] = int(clue)
            self.assertEqual(tuple(sorted(reconstructed.items())), frame.opened)
        self.assertEqual(render_replay(frames),
                         render_replay(replay_vectors(10, MINES_10, CLICKS_10)))
        with self.assertRaises(ValueError):
            render_replay(())


if __name__ == "__main__":
    unittest.main()
