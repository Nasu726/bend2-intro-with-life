import Base

# In an 8x8 board, x is the column and y is the row (both 0..7).
# This helper assumes the caller has already checked the range.
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

# Read one cell from an 8x8 torus.
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

def blinker() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0, index(3, 3), 1)
  b2 = Array.set(U32, b1, index(4, 3), 1)
  Array.set(U32, b2, index(5, 3), 1)

def count_from_pair(r: Array<U32> & (U32 & U32)) -> U32:
  (board, values) = r
  (n, alive) = values
  n

def main() -> U32:
  count_from_pair(neighbors(4, 4, blinker()))
