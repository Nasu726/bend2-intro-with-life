import Base

law plus_zero:
  for x: Nat
  {Nat.add(x, 0n) == x : Nat}

def plus_zero(x):
  match x:
    case 0n:
      {==}
    case 1n+p:
      %plus_zero(p) : {1n+Nat.add(p, 0n) == 1n+_ : Nat}
      {==}

def main() -> {Nat.add(2n, 0n) == 2n : Nat}:
  plus_zero(2n)
