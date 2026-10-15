import Base

# Same algorithm as 07_life_core, now with a text renderer.
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
  Array.get(U32, b, (y * 8 + x : U32))

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
  b1 = Array.set(U32, b0,  1, 1)
  b2 = Array.set(U32, b1, 10, 1)
  b3 = Array.set(U32, b2, 16, 1)
  b4 = Array.set(U32, b3, 17, 1)
  Array.set(U32, b4, 18, 1)

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

# The recursion itself receives the array and the value as a parameter.
def read_cells(todo: Nat, +i: U32, text: String, r: Array<U32> & U32) -> Array<U32> & String:
  match todo:
    case 0n:
      (board, v) = r
      (board, text ++ U32.show(v))
    case 1n+p:
      (board, v) = r
      newer = text ++ U32.show(v)
      read_cells(p, (i + 1 : U32), newer, Array.get(U32, board, (i + 1 : U32)))

def render_cells(n: Nat, +i: U32, board: Array<U32>) -> Array<U32> & String:
  match n:
    case 0n:
      (board, "")
    case 1n+p:
      read_cells(p, i, "", Array.get(U32, board, i))

def read_rows(todo: Nat, +i: U32, text: String, r: Array<U32> & String) -> Array<U32> & String:
  match todo:
    case 0n:
      (board, line) = r
      (board, text ++ line ++ "\n")
    case 1n+p:
      (board, line) = r
      newer = text ++ line ++ "\n"
      read_rows(p, (i + 8 : U32), newer, render_cells(8n, (i + 8 : U32), board))

def render_rows(n: Nat, +i: U32, board: Array<U32>) -> Array<U32> & String:
  match n:
    case 0n:
      (board, "")
    case 1n+p:
      read_rows(p, i, "", render_cells(8n, i, board))

def show_rendered(todo: Nat, +generation: U32, r: Array<U32> & String) -> IO(Unit):
  match todo:
    case 0n:
      (board, picture) = r
      do IO<Unit>:
        IO.print("generation " ++ U32.show(generation))
        IO.print(picture)
        IO.print("done")
    case 1n+p:
      (board, picture) = r
      do IO<Unit>:
        IO.print("generation " ++ U32.show(generation))
        IO.print(picture)
        show_rendered(p, (generation + 1 : U32), render_rows(8n, 0, step(board)))

def main() -> IO(Unit):
  show_rendered(4n, 0, render_rows(8n, 0, glider()))
