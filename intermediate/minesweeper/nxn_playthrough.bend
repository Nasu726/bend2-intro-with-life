# Reproducible 10 x 10 full-game playthrough (not yet a GUI).
# Row y=5 contains ten mines (indices 50..59), separating two zero regions.
# Click 0 opens the top region; click 99 opens the bottom and wins.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Game

def mine_wall(board: Words.MineWords) -> Words.MineWords:
  board = Words.set_checked(board, 50, True{})
  board = Words.set_checked(board, 51, True{})
  board = Words.set_checked(board, 52, True{})
  board = Words.set_checked(board, 53, True{})
  board = Words.set_checked(board, 54, True{})
  board = Words.set_checked(board, 55, True{})
  board = Words.set_checked(board, 56, True{})
  board = Words.set_checked(board, 57, True{})
  board = Words.set_checked(board, 58, True{})
  Words.set_checked(board, 59, True{})

# A flag must prevent revealing a safe zero; removing it permits victory.
def flag_block_then_win() -> U32:
  game = Game.new(mine_wall(Words.new(10)))
  game = Game.click(game, 0)
  game = Game.mark(game, 99)
  game = Game.click(game, 99)
  game = Game.mark(game, 99)
  game = Game.click(game, 99)
  Game.snapshot(game, 99)

# A first-click mine moves to the first free index (0); a later hit loses.
def relocated_mine_loss() -> U32:
  game = Game.new(mine_wall(Words.new(10)))
  game = Game.click(game, 50)
  game = Game.click(game, 0)
  Game.snapshot(game, 0)

def main() -> U32:
  game = Game.new(mine_wall(Words.new(10)))
  game = Game.click(game, 0)
  game = Game.click(game, 99)
  Game.snapshot(game, 99)
