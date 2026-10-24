import Base

# In an 8x8 board, x is the column and y is the row (both 0..7).
# This helper assumes the caller has already checked the range.
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

# 8x8, row major; alive at (1,0),(2,1),(0,2),(1,2),(2,2)
def glider() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0, index(1, 0), 1)
  b2 = Array.set(U32, b1, index(2, 1), 1)
  b3 = Array.set(U32, b2, index(0, 2), 1)
  b4 = Array.set(U32, b3, index(1, 2), 1)
  Array.set(U32, b4, index(2, 2), 1)

def read_value(r: Array<U32> & U32) -> U32:
  (b, v) = r
  v

def main() -> U32:
  read_value(Array.get(U32, glider(), index(2, 2)))
