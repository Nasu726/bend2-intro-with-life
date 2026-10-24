import Base

# Array.clone returns two independent copies.
def read_value(result: Array<U32> & U32) -> U32:
  (unused_array, value) = result
  value

def compare_clones(pair: Array<U32> & Array<U32>) -> U32:
  (left, right) = pair
  changed = Array.set(U32, left, 0, 17)
  modified = read_value(Array.get(U32, changed, 0))
  original = read_value(Array.get(U32, right, 0))
  (modified + original : U32)

def main() -> U32:
  source = Array.new(U32, 2n, 5)
  compare_clones(Array.clone(U32, source))
