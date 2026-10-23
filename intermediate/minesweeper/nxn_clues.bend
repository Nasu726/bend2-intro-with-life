# Internal non-wrapping clue count for N x N mine words (N=2..100).
# This module reads hidden truth; do not pass its board to public solvers.
# An invalid cell returns 0 without reading storage. No game state here.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Mines

# An out-of-bounds coordinate can wrap to a valid linear index in U32.
# Mines.has safely bounds the read; Geo.neighbor masks its contribution.
# No match on a computed neighbor Bool is needed (Bend 2.0.37).
def add_neighbor(board: Mines.MineWords, +n: U32, +x: U32, +y: U32, +u: U32, +v: U32) -> Mines.MineWords & U32:
  (board, present) = Mines.has(board, Geo.index(n, u, v))
  (board, Bool.to_u32(Bool.and(Geo.neighbor(n, x, y, u, v), present)))

def count_neighbors(board: Mines.MineWords, +n: U32, +x: U32, +y: U32) -> Mines.MineWords & U32:
  (board, a) = add_neighbor(board, n, x, y, (x - 1 : U32), (y - 1 : U32))
  (board, b) = add_neighbor(board, n, x, y, x, (y - 1 : U32))
  (board, c) = add_neighbor(board, n, x, y, (x + 1 : U32), (y - 1 : U32))
  (board, d) = add_neighbor(board, n, x, y, (x - 1 : U32), y)
  (board, e) = add_neighbor(board, n, x, y, (x + 1 : U32), y)
  (board, f) = add_neighbor(board, n, x, y, (x - 1 : U32), (y + 1 : U32))
  (board, g) = add_neighbor(board, n, x, y, x, (y + 1 : U32))
  (board, h) = add_neighbor(board, n, x, y, (x + 1 : U32), (y + 1 : U32))
  (board, (a + b + c + d + e + f + g + h : U32))

def count_checked_if(valid: Bool, board: Mines.MineWords, +n: U32, +i: U32) -> Mines.MineWords & U32:
  match valid:
    case True{}:
      count_neighbors(board, n, U32.mod(i, n), U32.div(i, n))
    case False{}:
      (board, 0)

def count_checked(board: Mines.MineWords, +n: U32, +i: U32) -> Mines.MineWords & U32:
  count_checked_if(Geo.valid_index(n, i), board, n, i)

def clue(board: Mines.MineWords, +i: U32) -> Mines.MineWords & U32:
  match board:
    case Mines.MineWords{n, words}:
      count_checked(Mines.MineWords{n, words}, n, i)

def read_count(pair: Mines.MineWords & U32) -> U32:
  (unused, count) = pair
  count

def main() -> U32:
  read_count(clue(Mines.set_checked(Mines.set_checked(Mines.new(10), 0, True{}), 11, True{}), 1))
