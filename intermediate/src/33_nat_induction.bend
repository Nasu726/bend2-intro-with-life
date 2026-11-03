import Base

# For every natural number x, multiplying by zero gives zero.
# This is an induction, not just a check for a chosen input.
law times_zero:
  for x: Nat
  {Nat.mul(x, 0n) == 0n : Nat}

def times_zero(x):
  match x:
    case 0n:
      {==}
    case 1n+p:
      %times_zero(p) : {Nat.mul(p, 0n) == _ : Nat}
      {==}

def main() -> U32:
  0
