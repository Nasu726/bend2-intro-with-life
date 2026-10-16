import Base

def choose(is_three: Bool, is_two: Bool, alive: U32) -> U32:
  match is_three:
    case True{}:
      1
    case False{}:
      match is_two:
        case True{}:
          alive
        case False{}:
          0

def rule(alive: U32, +n: U32) -> U32:
  choose(U32.is_eq(n, 3), U32.is_eq(n, 2), alive)

law three_is_alive:
  for cell: U32
  {rule(cell, 3) == 1 : U32}

def three_is_alive(cell):
  {==}

law two_preserves:
  for cell: U32
  {rule(cell, 2) == cell : U32}

def two_preserves(cell):
  {==}

law zero_is_dead:
  for cell: U32
  {rule(cell, 0) == 0 : U32}

def zero_is_dead(cell):
  {==}

# A proof file can omit main. Run: bend 11_rule_proofs.bend --verdict
