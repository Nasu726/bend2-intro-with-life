# Non-wrapping N x N clue calculation from PRIVATE mine storage.
# This is game-engine logic, NOT an input to the public-information solver.
# Valid board sizes: 2..100 (Mines.new precondition).
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Mines

def as_u32(value: Bool) -> U32:
  match value:
    case True{}:
      1
    case False{}:
      0

def counted(pair: Mines.MineWords & Bool) -> Mines.MineWords & U32:
  (board, mine) = pair
  (board, as_u32(mine))

# Invalid coordinates (including U32.sub(0,1)) never reach Mines.has.
def inspect(board: Mines.MineWords, +n: U32, +x: U32, +y: U32,
            +u: U32, +v: U32) -> Mines.MineWords & U32:
  match Geo.neighbor(n, x, y, u, v):
    case True{}:
      counted(Mines.has(board, Geo.index(n, u, v)))
    case False{}:
      (board, 0)

# Destructure a pair parameter, not a newly computed expression.
def plus(+total: U32, pair: Mines.MineWords & U32) -> Mines.MineWords & U32:
  (board, value) = pair
  (board, (total + value : U32))

def next(pair: Mines.MineWords & U32, +n: U32, +x: U32, +y: U32,
         +u: U32, +v: U32) -> Mines.MineWords & U32:
  (board, total) = pair
  plus(total, inspect(board, n, x, y, u, v))

# PRECONDITION: Geo.valid_index(n,index). The public entry is checked.
def at_valid(board: Mines.MineWords, +n: U32, +index: U32) ->
  Mines.MineWords & U32:
  x = U32.mod(index, n)
  y = U32.div(index, n)
  nw = inspect(board, n, x, y, U32.sub(x, 1), U32.sub(y, 1))
  north = next(nw, n, x, y, x, U32.sub(y, 1))
  ne = next(north, n, x, y, (x + 1 : U32), U32.sub(y, 1))
  west = next(ne, n, x, y, U32.sub(x, 1), y)
  east = next(west, n, x, y, (x + 1 : U32), y)
  sw = next(east, n, x, y, U32.sub(x, 1), (y + 1 : U32))
  south = next(sw, n, x, y, x, (y + 1 : U32))
  next(south, n, x, y, (x + 1 : U32), (y + 1 : U32))

def wrap(pair: Mines.MineWords & U32) -> Mines.MineWords & Maybe<&2, U32>:
  (board, clue) = pair
  (board, Some{clue})

def when_valid(valid: Bool, board: Mines.MineWords, +n: U32, +index: U32) ->
  Mines.MineWords & Maybe<&2, U32>:
  match valid:
    case True{}:
      wrap(at_valid(board, n, index))
    case False{}:
      (board, None{})

# Invalid indices return None; 100..127 are NOT cells of a 10x10 board.
def checked(board: Mines.MineWords, +index: U32) ->
  Mines.MineWords & Maybe<&2, U32>:
  match board:
    case Mines.MineWords{n, words}:
      when_valid(Geo.valid_index(n, index), Mines.MineWords{n, words}, n, index)

# Display-only helper: 99 is not a real clue value.
def result(pair: Mines.MineWords & Maybe<&2, U32>) -> U32:
  (board, clue) = pair
  match clue:
    case Some{value}:
      value
    case None{}:
      99

# Mines at (0,0) and (1,1) are both adjacent to (1,0).
def main() -> U32:
  result(checked(Mines.set_checked(
    Mines.set_checked(Mines.new(10), 0, True{}), 11, True{}), 1))
