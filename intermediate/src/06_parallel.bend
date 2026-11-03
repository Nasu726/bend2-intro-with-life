import Base

# Independent branches form a balanced fork/join computation.
def count_leaves(+level: Nat) -> U32:
  match level:
    case 0n:
      1
    case 1n+k:
      x y = count_leaves(k) count_leaves(k)
      (x + y : U32)

def main() -> U32:
  count_leaves(8n)
