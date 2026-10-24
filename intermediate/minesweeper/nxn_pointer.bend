# Pure N x N pointer adapter for a future GUI; no window is opened here.
# Tiles are 32x32 pixels. n MUST match the engine's board size (2..100).
# This module never reads the mine truth to decide where a pointer lands.
import Base
import ./nxn_full_game.bend as Game
import ./nxn_mine_words.bend as Words

def cell_if_valid(valid: Bool, n: U32, x: U32, y: U32) -> Maybe<&2, U32>:
  match valid:
    case True{}:
      Some{(U32.div(y, 32) * n + U32.div(x, 32) : U32)}
    case False{}:
      None{}

# Reject out-of-window pixels before converting to a logical cell.
# 100 * 32 fits U32, so the valid range never overflows.
def cell_at(+n: U32, +x: U32, +y: U32) -> Maybe<&2, U32>:
  valid = Bool.and(
    Bool.and(U32.is_ge(n, 2), U32.is_lt(n, 101)),
    Bool.and(U32.is_lt(x, (n * 32 : U32)),
             U32.is_lt(y, (n * 32 : U32))))
  cell_if_valid(valid, n, x, y)

# Left button (0) reveals, right button (1) toggles a flag.
# Unknown buttons must not silently become clicks.
def choose_button(left: Bool, right: Bool, game: Game.Game, index: U32) -> Game.Game:
  match left right:
    case True{} _:
      Game.click(game, index)
    case False{} True{}:
      Game.mark(game, index)
    case False{} False{}:
      game

def apply_button(game: Game.Game, index: U32, +button: U32) -> Game.Game:
  choose_button(U32.is_eq(button, 0), U32.is_eq(button, 1), game, index)

def apply_cell(cell: Maybe<&2, U32>, game: Game.Game, button: U32) -> Game.Game:
  match cell:
    case None{}:
      game
    case Some{index}:
      apply_button(game, index, button)

def pointer(game: Game.Game, +n: U32, +x: U32, +y: U32, +button: U32) -> Game.Game:
  apply_cell(cell_at(n, x, y), game, button)

# A mine-free board wins on the first click; 100 + (10 + clue 0) = 110.
def main() -> U32:
  game = pointer(Game.new(Words.new(10)), 10, 0, 0, 0)
  Game.snapshot(game, 0)
