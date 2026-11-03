# N x N neighbor mine counts over checked U32-word storage.
# Valid n is 2..100. This is a game-internal primitive, not a public solver.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words

def mined_number(mined: Bool) -> U32:
  match mined:
    case True{}:
      1
    case False{}:
      0

def as_count(sum: U32, pair: Words.MineWords & Bool) -> Words.MineWords & U32:
  (board, mined) = pair
  (board, (sum + mined_number(mined) : U32))

def add_if_neighbor(valid: Bool, n: U32, u: U32, v: U32, pair: Words.MineWords & U32) -> Words.MineWords & U32:
  match valid:
    case True{}:
      (board, sum) = pair
      as_count(sum, Words.has(board, Geo.index(n, u, v)))
    case False{}:
      pair

# Offsets 0..8 cover a 3x3 square. Underflow at x=0/y=0 wraps
# in U32, but Geo.neighbor rejects it before accessing mine storage.
def add_one(+n: U32, +x: U32, +y: U32, +dx: U32, +dy: U32, pair: Words.MineWords & U32) -> Words.MineWords & U32:
  +u = (x + dx - 1 : U32)
  +v = (y + dy - 1 : U32)
  add_if_neighbor(Geo.neighbor(n, x, y, u, v), n, u, v, pair)

# Structural descent on Nat bounds this scan to exactly nine positions.
def count_loop(fuel: Nat, +n: U32, +x: U32, +y: U32, +pos: U32, pair: Words.MineWords & U32) -> Words.MineWords & U32:
  match fuel:
    case 0n:
      pair
    case 1n+k:
      dx = U32.mod(pos, 3)
      dy = U32.div(pos, 3)
      count_loop(k, n, x, y, (pos - 1 : U32), add_one(n, x, y, dx, dy, pair))

# PRECONDITION: Geo.valid_index(n, index).
def count_inside(+n: U32, board: Words.MineWords, +index: U32) -> Words.MineWords & U32:
  count_loop(9n, n, U32.mod(index, n), U32.div(index, n), 8, (board, 0))

def wrap_count(pair: Words.MineWords & U32) -> Words.MineWords & Maybe<&2, U32>:
  (board, count) = pair
  (board, Some{count})

def count_if_valid(valid: Bool, n: U32, board: Words.MineWords, index: U32) -> Words.MineWords & Maybe<&2, U32>:
  match valid:
    case True{}:
      wrap_count(count_inside(n, board, index))
    case False{}:
      (board, None{})

# Reject out-of-bounds logical cells, including Array padding slots.
def count_checked(board: Words.MineWords, +index: U32) -> Words.MineWords & Maybe<&2, U32>:
  match board:
    case Words.MineWords{+n, words}:
      count_if_valid(Geo.valid_index(n, index), n, Words.MineWords{n, words}, index)

def read_result(result: Maybe<&2, U32>) -> U32:
  match result:
    case Some{value}:
      value
    case None{}:
      999

def read_count(pair: Words.MineWords & Maybe<&2, U32>) -> U32:
  (board, result) = pair
  read_result(result)

def main() -> U32:
  read_count(count_checked(Words.set_checked(Words.new(10), 1, True{}), 0))
