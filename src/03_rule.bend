import Base

# The computed comparisons are matched by this helper's parameters.
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

# 3 neighbors => live; 2 => retain; otherwise dead.
def rule(alive: U32, +neighbors: U32) -> U32:
  choose(U32.is_eq(neighbors, 3), U32.is_eq(neighbors, 2), alive)

def main() -> U32:
  # dead cell with exactly three neighbors is born
  rule(0, 3)
