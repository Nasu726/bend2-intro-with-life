import Base

# Convert between Nat and U32 for valid, small board dimensions.
def as_number(b: Bool) -> U32:
  match b:
    case True{}:
      1
    case False{}:
      0

def main() -> U32:
  width: U32 = U32.from_nat(4n)
  safe: Bool = U32.is_lt(width, 16)
  as_number(safe)
