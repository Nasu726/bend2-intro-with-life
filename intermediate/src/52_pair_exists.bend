import Base

# Pair carries two independent values.
def coordinate() -> Pair(U32, U32):
  Tuple{1, 2}

def sum_coordinate(p: Pair(U32, U32)) -> U32:
  match p:
    case Tuple{x, y}:
      (x + y : U32)

# Exists carries a witness and a proof about that witness.
def next_is_three() -> Exists(Nat, n => {Nat.add(n, 1n) == 3n : Nat}):
  Tuple{2n, {==}}

def witness_number(w: Exists(Nat, n => {Nat.add(n, 1n) == 3n : Nat})) -> U32:
  match w:
    case Tuple{n, evidence}:
      U32.from_nat(n)

def main() -> U32:
  (sum_coordinate(coordinate()) + witness_number(next_is_three()) : U32)
