import Base

# Read one cell from an 8x8 torus.
def at(b: Array<U32>, x: U32, y: U32) -> Array<U32> & U32:
  Array.get(U32, b, (y * 8 + x : U32))

# The input board is threaded through all eight reads.
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

# A blinker horizontally crosses the centre of the board.
def blinker() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0, 27, 1)
  b2 = Array.set(U32, b1, 28, 1)
  Array.set(U32, b2, 29, 1)

def main() -> U32:
  (board, count) = neighbors(4, 4, blinker())
  count
