import Base

# Array.new(d) produces an array of 2^d elements.
def read_and_sum(r: Array<U32> & U32) -> U32:
  (a, x) = r
  x

def main() -> U32:
  a = Array.new(U32, 3n, 0)
  b = Array.set(U32, a, 2, 17)
  c = Array.set(U32, b, 7, 25)
  x = read_and_sum(Array.get(U32, c, 2))
  x
