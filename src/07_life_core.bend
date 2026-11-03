import Base

# In an 8x8 board, x is the column and y is the row (both 0..7).
# This helper assumes the caller has already checked the range.
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

# Fixed 8x8 toroidal Game of Life, B3/S23.
# Cells are U32 values, maintained in {0,1} by seed and rule.
def choose(is_three: Bool, is_two: Bool, alive: U32) -> U32:
  match is_three:
    case True{}:
      1
    case False{}:
      match is_two:
        case True{}:
          alive
        case False{}:
          0

def rule(alive: U32, +n: U32) -> U32:
  choose(U32.is_eq(n, 3), U32.is_eq(n, 2), alive)

# Each read consumes a board and produces a new board plus a cell value.
def at(b: Array<U32>, x: U32, y: U32) -> Array<U32> & U32:
  Array.get(U32, b, index(x, y))

# Returned board, neighbour count and original cell value.
def near_9(r: Array<U32> & U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, alive) = r
  (b, (sum, alive))

def near_8(r: Array<U32> & U32, x: U32, y: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_9(at(b, x, y), (sum + v : U32))

def near_7(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_8(at(b, xr, yb), x, y, (sum + v : U32))

def near_6(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_7(at(b, x, yb), x, y, xl, xr, yt, yb, (sum + v : U32))

def near_5(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_6(at(b, xl, yb), x, y, xl, xr, yt, yb, (sum + v : U32))

def near_4(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_5(at(b, xr, y), x, y, xl, xr, yt, yb, (sum + v : U32))

def near_3(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_4(at(b, xl, y), x, y, xl, xr, yt, yb, (sum + v : U32))

def near_2(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_3(at(b, xr, yt), x, y, xl, xr, yt, yb, (sum + v : U32))

def near_1(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & (U32 & U32):
  (b, v) = r
  near_2(at(b, x, yt), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors(+x: U32, +y: U32, b: Array<U32>) -> Array<U32> & (U32 & U32):
  +xl = ((x + 7 : U32) % 8 : U32)
  +xr = ((x + 1 : U32) % 8 : U32)
  +yt = ((y + 7 : U32) % 8 : U32)
  +yb = ((y + 1 : U32) % 8 : U32)
  near_1(at(b, xl, yt), x, y, xl, xr, yt, yb, 0)

def glider() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0, index(1, 0), 1)
  b2 = Array.set(U32, b1, index(2, 1), 1)
  b3 = Array.set(U32, b2, index(0, 2), 1)
  b4 = Array.set(U32, b3, index(1, 2), 1)
  Array.set(U32, b4, index(2, 2), 1)

# Decreasing Nat argument first: accepted recursive shape.
# Carry a board, neighbour count, and original cell state together.
# Destructuring is allowed here because r is a parameter.
def fill(todo: Nat, +i: U32, r: Array<U32> & (U32 & U32), out: Array<U32>) -> Array<U32>:
  match todo:
    case 0n:
      out
    case 1n+p:
      (old, pair) = r
      (n, alive) = pair
      next = rule(alive, n)
      out1 = Array.set(U32, out, i, next)
      +j = (i + 1 : U32)
      x = (j % 8 : U32)
      y = ((j / 8 : U32) % 8 : U32)
      fill(p, j, neighbors(x, y, old), out1)

def step(board: Array<U32>) -> Array<U32>:
  fill(64n, 0, neighbors(0, 0, board), [0 : U32*64n])

def evolve(steps: Nat, board: Array<U32>) -> Array<U32>:
  match steps:
    case 0n:
      board
    case 1n+p:
      evolve(p, step(board))

# Reading consumes and returns the array, which can be dropped here.
def value_from_pair(r: Array<U32> & U32) -> U32:
  (b, v) = r
  v

def main() -> U32:
  value_from_pair(Array.get(U32, evolve(4n, glider()), index(2, 3)))
