import Base

# 8x8, row major; alive at (1,0),(2,1),(0,2),(1,2),(2,2)
def glider() -> Array<U32>:
  b0 = [0 : U32*64n]
  b1 = Array.set(U32, b0,  1, 1)
  b2 = Array.set(U32, b1, 10, 1)
  b3 = Array.set(U32, b2, 16, 1)
  b4 = Array.set(U32, b3, 17, 1)
  Array.set(U32, b4, 18, 1)

def read_value(r: Array<U32> & U32) -> U32:
  (b, v) = r
  v

def main() -> U32:
  read_value(Array.get(U32, glider(), 18))
