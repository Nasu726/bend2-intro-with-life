import Base

# Kind(&1)=Type, Kind(&2)=Data; List preserves its element kind.
def length(a, -A: Kind(a), xs: List<a, A>) -> Nat:
  match xs:
    case Nil{}:
      0n
    case Con{h, t}:
      (1n + length(a, A, t) : Nat)

def main() -> Nat:
  length(&2, U32, [1, 2, 3])
