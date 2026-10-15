import Base

# A genuine balanced fork/join benchmark of independent calls.
def pow2(+depth: Nat) -> U32:
  match depth:
    case 0n:
      1
    case 1n+p:
      left right = pow2(p) pow2(p)
      (left + right : U32)

def main() -> U32:
  pow2(12n)
