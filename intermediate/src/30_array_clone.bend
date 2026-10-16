import Base

# Array.clone makes two independent arrays of the same initial data.
# Updating one clone must not change the other.
def compare_clones(pair: Array<U32> & Array<U32>) -> U32:
  (left, right) = pair
  changed = Array.set(U32, left, 0, 17)
  (changed_again, modified) = Array.get(U32, changed, 0)
  (right_again, original) = Array.get(U32, right, 0)
  (modified + original : U32)

def main() -> U32:
  source = Array.new(U32, 2n, 5)
  copies = Array.clone(U32, source)
  compare_clones(copies)
