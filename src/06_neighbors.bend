import Base

# Read one cell from an 8x8 torus.
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

def blinker() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0, 27, 1)
  b2 = Array.set(U32, b1, 28, 1)
  Array.set(U32, b2, 29, 1)

def count_from_pair(r: Array<U32> & U32) -> U32:
  (board, count) = r
  count

def main() -> U32:
  count_from_pair(neighbors(4, 4, blinker()))
