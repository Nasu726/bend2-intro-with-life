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

def at(b: Array<U32>, x: U32, y: U32) -> Array<U32> & U32:
  Array.get(U32, b, (y * 8 + x : U32))

def neighbors_1(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_2(at(b, x, yt), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_2(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_3(at(b, xr, yt), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_3(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_4(at(b, xl, y), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_4(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_5(at(b, xr, y), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_5(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_6(at(b, xl, yb), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_6(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_7(at(b, x, yb), x, y, xl, xr, yt, yb, (sum + v : U32))

def neighbors_7(r: Array<U32> & U32, +x: U32, +y: U32, +xl: U32, +xr: U32, +yt: U32, +yb: U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  neighbors_8(at(b, xr, yb), (sum + v : U32))

def neighbors_8(r: Array<U32> & U32, sum: U32) -> Array<U32> & U32:
  (b, v) = r
  (b, (sum + v : U32))

def neighbors(+x: U32, +y: U32, b: Array<U32>) -> Array<U32> & U32:
  +xl = ((x + 7 : U32) % 8 : U32)
  +xr = ((x + 1 : U32) % 8 : U32)
  +yt = ((y + 7 : U32) % 8 : U32)
  +yb = ((y + 1 : U32) % 8 : U32)
  neighbors_1(at(b, xl, yt), x, y, xl, xr, yt, yb, 0)

def glider() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0,  1, 1)
  b2 = Array.set(U32, b1, 10, 1)
  b3 = Array.set(U32, b2, 16, 1)
  b4 = Array.set(U32, b3, 17, 1)
  Array.set(U32, b4, 18, 1)

# Match on a parameter, not a computed pair: each adapter takes ownership
# of the returned board and forwards it to the next operation.
def fill_after_current(todo: Nat, +i: U32, n: U32, out: Array<U32>, r: Array<U32> & U32) -> Array<U32>:
  (old, alive) = r
  next = rule(alive, n)
  out1 = Array.set(U32, out, i, next)
  fill(todo, (i + 1 : U32), old, out1)

def fill_after_neighbors(todo: Nat, +i: U32, out: Array<U32>, r: Array<U32> & U32) -> Array<U32>:
  (old, n) = r
  fill_after_current(todo, i, n, out, Array.get(U32, old, i))

def fill(todo: Nat, +i: U32, old: Array<U32>, out: Array<U32>) -> Array<U32>:
  match todo:
    case 0n:
      out
    case 1n+p:
      x = (i % 8 : U32)
      y = (i / 8 : U32)
      fill_after_neighbors(p, i, out, neighbors(x, y, old))

def step(board: Array<U32>) -> Array<U32>:
  fill(64n, 0, board, [0 : U32*64n])

# Matching a computed tuple is not permitted. These small adapter
# functions take pairs as parameters and unpack them safely.
def render_cells_after_tail(v: U32, r: Array<U32> & String) -> Array<U32> & String:
  (board, tail) = r
  (board, U32.show(v) ++ tail)

def render_cells_after_get(n: Nat, +i: U32, r: Array<U32> & U32) -> Array<U32> & String:
  (board, v) = r
  render_cells_after_tail(v, render_cells(n, (i + 1 : U32), board))

def render_cells(n: Nat, +at_index: U32, board: Array<U32>) -> Array<U32> & String:
  match n:
    case 0n:
      (board, "")
    case 1n+p:
      render_cells_after_get(p, at_index, Array.get(U32, board, at_index))

def render_rows_after_tail(line: String, r: Array<U32> & String) -> Array<U32> & String:
  (board, tail) = r
  (board, line ++ "\n" ++ tail)

def render_rows_after_line(n: Nat, +i: U32, r: Array<U32> & String) -> Array<U32> & String:
  (board, line) = r
  render_rows_after_tail(line, render_rows(n, (i + 8 : U32), board))

def render_rows(n: Nat, +at_index: U32, board: Array<U32>) -> Array<U32> & String:
  match n:
    case 0n:
      (board, "")
    case 1n+p:
      render_rows_after_line(p, at_index, render_cells(8n, at_index, board))

def show_after_render(p: Nat, +generation: U32, r: Array<U32> & String) -> IO(Unit):
  (board, picture) = r
  do IO<Unit>:
    IO.print("generation " ++ U32.show(generation))
    IO.print(picture)
    show(p, (generation + 1 : U32), step(board))

def show(remaining: Nat, +generation: U32, board: Array<U32>) -> IO(Unit):
  match remaining:
    case 0n:
      IO.print("done")
    case 1n+p:
      show_after_render(p, generation, render_rows(8n, 0, board))

def main() -> IO(Unit):
  show(5n, 0, glider())
