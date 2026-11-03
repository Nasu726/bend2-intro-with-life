# Pure pixel-to-game controller for the N x N lazy first-click engine.
# This is a testable GUI boundary, not an App.run renderer or real-device test.
# Fresh stores only n/count/seed; do not create mines for a pointer preview.
import Base
import ./nxn_lazy_game.bend as Lazy

# One screen tile is 32x32 pixels. N=10 is a 320x320 board.
def index_if_valid(valid: Bool, n: U32, x: U32, y: U32) -> Maybe<&2, U32>:
  match valid:
    case True{}:
      Some{((U32.div(y, 32) * n + U32.div(x, 32)) : U32)}
    case False{}:
      None{}

def cell_at(+n: U32, +x: U32, +y: U32) -> Maybe<&2, U32>:
  index_if_valid(
    Bool.and(U32.is_lt(x, (n * 32 : U32)),
             U32.is_lt(y, (n * 32 : U32))), n, x, y)

# 65535 is outside the 2..100 N x N valid cell index range (0..9999).
def index_or_invalid(index: Maybe<&2, U32>) -> U32:
  match index:
    case Some{i}:
      i
    case None{}:
      65535

def pixel_index(n: U32, x: U32, y: U32) -> U32:
  index_or_invalid(cell_at(n, x, y))

# Mouse button 0 = reveal, 1 = flag; other buttons must do nothing.
def mouse_mode(left: Bool, right: Bool, game: Lazy.Game, index: U32) -> Lazy.Game:
  match left right:
    case True{} _:
      Lazy.click(game, index)
    case False{} True{}:
      Lazy.mark(game, index)
    case False{} False{}:
      game

def mouse_index(index: Maybe<&2, U32>, game: Lazy.Game, +button: U32) -> Lazy.Game:
  match index:
    case None{}:
      game
    case Some{i}:
      mouse_mode(U32.is_eq(button, 0), U32.is_eq(button, 1), game, i)

def pointer_n(game: Lazy.Game, n: U32, x: U32, y: U32, button: U32) -> Lazy.Game:
  mouse_index(cell_at(n, x, y), game, button)

def pointer(game: Lazy.Game, x: U32, y: U32, button: U32) -> Lazy.Game:
  pointer_n(game, 10, x, y, button)

def reset(n: U32, count: U32, seed: U32) -> Lazy.Game:
  Lazy.new(n, count, seed)

def reset_gui(seed: U32) -> Lazy.Game:
  reset(10, 10, seed)

def snapshot(game: Lazy.Game, index: U32) -> U32:
  Lazy.snapshot(game, index)

def main() -> U32:
  snapshot(pointer(reset_gui(20261029), 0, 0, 0), 0)
