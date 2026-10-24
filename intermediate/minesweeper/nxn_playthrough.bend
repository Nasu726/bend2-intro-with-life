# Reproducible 10 x 10 game: a variable number M of mines in row y=5.
# 0 <= M <= 10. The main example uses M=10 (indices 50..59).
# M is a parameter of the placement function, not a hard-coded mine count.
# This is a pure game trace, not a GUI or a general no-guess generator.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Game

# Structural recursion places one mine at a time; no manual ten-line setup.
# PRECONDITION: the board is 10 x 10 and 0 <= M <= 10.
def place_row(fuel: Nat, +index: U32, board: Words.MineWords) -> Words.MineWords:
  match fuel:
    case 0n:
      board
    case 1n+k:
      place_row(k, (index + 1 : U32),
                Words.set_checked(board, index, True{}))

def mine_row(m: Nat, board: Words.MineWords) -> Words.MineWords:
  place_row(m, 50, board)

def main() -> U32:
  game = Game.new(mine_row(10n, Words.new(10)))
  game = Game.click(game, 0)
  game = Game.click(game, 99)
  Game.snapshot(game, 99)
