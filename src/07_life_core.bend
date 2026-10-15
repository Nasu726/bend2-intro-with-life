import Base

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

def at(b: Array<U32>, x: U32, y: U32) -> Array<U32> & U32:
  Array.get(U32, b, (y * 8 + x : U32))

def neighbors(+x: U32, +y: U32, b: Array<U32>) -> Array<U32> & U32:
  +xl = ((x + 7 : U32) % 8 : U32)
  +xr = ((x + 1 : U32) % 8 : U32)
  +yt = ((y + 7 : U32) % 8 : U32)
  +yb = ((y + 1 : U32) % 8 : U32)
  (b1, a) = at(b,  xl, yt)
  (b2, c) = at(b1, x,  yt)
  (b3, d) = at(b2, xr, yt)
  (b4, e) = at(b3, xl, y)
  (b5, f) = at(b4, xr, y)
  (b6, g) = at(b5, xl, yb)
  (b7, h) = at(b6, x,  yb)
  (b8, i) = at(b7, xr, yb)
  (b8, (a + c + d + e + f + g + h + i : U32))

def glider() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0,  1, 1)
  b2 = Array.set(U32, b1, 10, 1)
  b3 = Array.set(U32, b2, 16, 1)
  b4 = Array.set(U32, b3, 17, 1)
  Array.set(U32, b4, 18, 1)

# Decreasing Nat argument first: accepted recursive shape.
def fill(todo: Nat, +i: U32, old: Array<U32>, out: Array<U32>) -> Array<U32>:
  match todo:
    case 0n:
      out
    case 1n+p:
      x = (i % 8 : U32)
      y = (i / 8 : U32)
      (old1, n) = neighbors(x, y, old)
      (old2, v) = Array.get(U32, old1, i)
      next = rule(v, n)
      out1 = Array.set(U32, out, i, next)
      fill(p, (i + 1 : U32), old2, out1)

def step(board: Array<U32>) -> Array<U32>:
  fill(64n, 0, board, [0 : U32*64n])

def evolve(steps: Nat, board: Array<U32>) -> Array<U32>:
  match steps:
    case 0n:
      board
    case 1n+p:
      evolve(p, step(board))

# Reading consumes and returns the array, which can be dropped here.
def main() -> U32:
  (b, v) = Array.get(U32, evolve(4n, glider()), 26)
  v
