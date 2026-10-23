# Internal non-wrapping clue count for N x N mine words (N=2..100).
# This module reads hidden truth; do not pass its board to public solvers.
# An invalid cell returns 0 without reading storage. No game state here.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Mines

# Convert both Boolean parameters before combining them. An out-of-bounds
# coordinate may wrap to a valid U32 linear index; the geometric mask must
# prevent that unrelated mine from contributing to the clue.
def masked_bit(near: Bool, present: Bool) -> U32:
  U32.and(Bool.to_u32(near), Bool.to_u32(present))

# Bend matches a parameter, not a computed function result. Pass the
# resource-bearing read pair into this helper before destructuring it.
def accumulate_read(pair: Mines.MineWords & Bool, near: Bool, +total: U32) -> Mines.MineWords & U32:
  (board, present) = pair
  (board, (total + masked_bit(near, present) : U32))

# Likewise, the running (board, count) pair is a parameter here. Do not
# destructure a computed result in count_neighbors itself.
def add_neighbor_acc(pair: Mines.MineWords & U32, +n: U32, +x: U32, +y: U32, +u: U32, +v: U32) -> Mines.MineWords & U32:
  (board, total) = pair
  accumulate_read(Mines.has(board, Geo.index(n, u, v)), Geo.neighbor(n, x, y, u, v), total)

def count_neighbors(board: Mines.MineWords, +n: U32, +x: U32, +y: U32) -> Mines.MineWords & U32:
  p0 = add_neighbor_acc((board, 0), n, x, y, (x - 1 : U32), (y - 1 : U32))
  p1 = add_neighbor_acc(p0, n, x, y, x, (y - 1 : U32))
  p2 = add_neighbor_acc(p1, n, x, y, (x + 1 : U32), (y - 1 : U32))
  p3 = add_neighbor_acc(p2, n, x, y, (x - 1 : U32), y)
  p4 = add_neighbor_acc(p3, n, x, y, (x + 1 : U32), y)
  p5 = add_neighbor_acc(p4, n, x, y, (x - 1 : U32), (y + 1 : U32))
  p6 = add_neighbor_acc(p5, n, x, y, x, (y + 1 : U32))
  add_neighbor_acc(p6, n, x, y, (x + 1 : U32), (y + 1 : U32))

def count_checked_if(valid: Bool, board: Mines.MineWords, +n: U32, +i: U32) -> Mines.MineWords & U32:
  match valid:
    case True{}:
      count_neighbors(board, n, U32.mod(i, n), U32.div(i, n))
    case False{}:
      (board, 0)

def count_checked(board: Mines.MineWords, +n: U32, +i: U32) -> Mines.MineWords & U32:
  count_checked_if(Geo.valid_index(n, i), board, n, i)

# The size extracted from MineWords is affine. Pass it once to a helper
# that explicitly accepts a reusable U32 before using it both to rebuild
# the board and to check the requested cell.
def count_checked_parts(+n: U32, words: Array<U32>, +i: U32) -> Mines.MineWords & U32:
  count_checked(Mines.MineWords{n, words}, n, i)

def clue(board: Mines.MineWords, +i: U32) -> Mines.MineWords & U32:
  match board:
    case Mines.MineWords{n, words}:
      count_checked_parts(n, words, i)

def read_count(pair: Mines.MineWords & U32) -> U32:
  (unused, count) = pair
  count

def main() -> U32:
  read_count(clue(Mines.set_checked(Mines.set_checked(Mines.new(10), 0, True{}), 11, True{}), 1))
