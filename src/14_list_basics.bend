import Base

# A List is an inductive structure. The tail is smaller.
def count(xs: List<U32>) -> Nat:
  match xs:
    case Nil{}:
      0n
    case Con{h, t}:
      (1n + count(t) : Nat)

def main() -> Nat:
  count([1, 10, 16, 17, 18])
