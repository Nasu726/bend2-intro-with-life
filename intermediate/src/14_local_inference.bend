import Base

# Deduce from ONE visible number:
# remaining = displayed clue - mines already established as certain
# unknown   = number of still-unclassified adjacent squares
#
# "Flagged by the player" is NOT automatically "certain mine".

type LocalRule is Data:
  AllSafe{}
  AllMines{}
  Unknown{}
  Inconsistent{}

def infer(remaining: U32, unknown: U32) -> LocalRule:
  match U32.is_lt(unknown, remaining):
    case True{}:
      Inconsistent{}
    case False{}:
      match U32.is_eq(remaining, 0):
        case True{}:
          AllSafe{}
        case False{}:
          match U32.is_eq(remaining, unknown):
            case True{}:
              AllMines{}
            case False{}:
              Unknown{}

# A small observable numeric output for automated testing.
def tag(r: LocalRule) -> U32:
  match r:
    case AllSafe{}:
      1
    case AllMines{}:
      2
    case Unknown{}:
      3
    case Inconsistent{}:
      4

law zero_remaining_is_safe:
  for u: U32
  {infer(0, u) == AllSafe{} : LocalRule}

def zero_remaining_is_safe(u):
  match U32.is_lt(u, 0):
    case True{}:
      {==}
    case False{}:
      match U32.is_eq(0, 0):
        case True{}:
          {==}
        case False{}:
          {==}

def main() -> U32:
  a = tag(infer(0, 3))
  b = tag(infer(3, 3))
  c = tag(infer(1, 3))
  d = tag(infer(4, 2))
  (a + b + c + d : U32)
