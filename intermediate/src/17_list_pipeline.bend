import Base

# List.range returns List<&2, Nat>. Filter keeps that quantity.
def small(n: Nat) -> Bool:
  Nat.is_lt(n, 3n)

def sum(acc: Nat, n: Nat) -> Nat:
  Nat.add(acc, n)

def main() -> Nat:
  xs = List.range(4n)
  ys = List.filter(~Nat, ~small, xs)
  List.foldl(~&2, ~Nat, ~Nat, ~sum, ys, 0n)
