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

# Render 8 cells; the Array is returned for the next row.
def render_cells(n: Nat, +at_index: U32, board: Array<U32>) -> Array<U32> & String:
  match n:
    case 0n:
      (board, "")
    case 1n+p:
      (board1, cell) = Array.get(U32, board, at_index)
      (board2, tail) = render_cells(p, (at_index + 1 : U32), board1)
      (board2, U32.show(cell) ++ tail)

def render_rows(rows: Nat, +at_index: U32, board: Array<U32>) -> Array<U32> & String:
  match rows:
    case 0n:
      (board, "")
    case 1n+p:
      (board1, line) = render_cells(8n, at_index, board)
      (board2, tail) = render_rows(p, (at_index + 8 : U32), board1)
      (board2, line ++ "\n" ++ tail)

# IO runs on the CPU; every generation is a pure new board.
def show(remaining: Nat, +generation: U32, board: Array<U32>) -> IO(Unit):
  match remaining:
    case 0n:
      IO.print("done")
    case 1n+p:
      (board1, picture) = render_rows(8n, 0, board)
      do IO<Unit>:
        IO.print("generation " ++ U32.show(generation))
        IO.print(picture)
        show(p, (generation + 1 : U32), step(board1))

def main() -> IO(Unit):
  show(5n, 0, glider())
