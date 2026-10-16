import Base

def next(n: Nat) -> Nat:
  1n+n

def sum(acc: Nat, n: Nat) -> Nat:
  Nat.add(acc, n)

def main() -> Nat:
  xs = List.range(4n)
  ys = List.map(~Nat, ~Nat, ~next, xs)
  List.foldl(~&2, ~Nat, ~Nat, ~sum, ys, 0n)
