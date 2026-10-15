import Base

# GPU offloading is requested at the root, not with an explicit kernel.
def pow2(+depth: Nat) -> U32:
  match depth:
    case 0n:
      1
    case 1n+p:
      left right = pow2(p) pow2(p)
      (left + right : U32)

def main() -> IO(Unit):
  IO.print(U32.show(pow2!(12n)))
