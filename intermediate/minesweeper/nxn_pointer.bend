# Pixel-to-cell and mouse-button adapter for the N x N pure game.
# Each tile is 64 x 64 pixels; x is column and y is row.
# This is not an App window, drawing implementation, or GUI acceptance test.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Game

type PointerState is Type:
  PointerState{n: U32, game: Game.Game}

# Read the size from the same mine board used by the game. Callers cannot
# accidentally supply a different N for pointer mapping and game state.
def new(board: Words.MineWords) -> PointerState:
  match board:
    case Words.MineWords{+n, words}:
      PointerState{n, Game.new(Words.MineWords{n, words})}

# checked_index rejects both out-of-window coordinates and Array padding.
# Division by 64 avoids multiplying potentially untrusted pixel coordinates.
def cell_at(+n: U32, +x: U32, +y: U32) -> Maybe<&2, U32>:
  Geo.checked_index(n, U32.div(x, 64), U32.div(y, 64))

# Button 0 reveals; button 1 toggles a flag; other buttons do nothing.
def mouse_mode(left: Bool, right: Bool, game: Game.Game, index: U32) -> Game.Game:
  match left right:
    case True{} _:
      Game.click(game, index)
    case False{} True{}:
      Game.mark(game, index)
    case False{} False{}:
      game

def apply(index: Maybe<&2, U32>, game: Game.Game, +button: U32) -> Game.Game:
  match index:
    case None{}:
      game
    case Some{i}:
      mouse_mode(U32.is_eq(button, 0), U32.is_eq(button, 1), game, i)

def pointer(state: PointerState, +x: U32, +y: U32, +button: U32) -> PointerState:
  match state:
    case PointerState{+n, game}:
      PointerState{n, apply(cell_at(n, x, y), game, button)}

# A one-use inspection helper for the finite tests.
def snapshot(state: PointerState, +index: U32) -> U32:
  match state:
    case PointerState{n, game}:
      Game.snapshot(game, index)

def main() -> U32:
  board = Words.set_checked(Words.new(10), 1, True{})
  state = pointer(new(board), 0, 0, 0)
  snapshot(state, 0)
