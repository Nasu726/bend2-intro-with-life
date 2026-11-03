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

# Definition order matters: each helper is available to those below it.
# Computed conditions are passed as function parameters to pattern matches.
def infer_equal(remaining: U32, unknown: U32, equal: Bool) -> LocalRule:
  match equal:
    case True{}:
      AllMines{}
    case False{}:
      Unknown{}

def infer_zero(+remaining: U32, +unknown: U32, empty: Bool) -> LocalRule:
  match empty:
    case True{}:
      AllSafe{}
    case False{}:
      infer_equal(remaining, unknown, U32.is_eq(remaining, unknown))

def infer_limit(+remaining: U32, +unknown: U32, over: Bool) -> LocalRule:
  match over:
    case True{}:
      Inconsistent{}
    case False{}:
      infer_zero(remaining, unknown, U32.is_eq(remaining, 0))

def infer(+remaining: U32, +unknown: U32) -> LocalRule:
  infer_limit(remaining, unknown, U32.is_lt(unknown, remaining))

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

law zero_remaining_is_safe_for_three:
  {infer(0, 3) == AllSafe{} : LocalRule}

def zero_remaining_is_safe_for_three():
  {==}

def main() -> U32:
  a = tag(infer(0, 3))
  b = tag(infer(3, 3))
  c = tag(infer(1, 3))
  d = tag(infer(4, 2))
  (a + b + c + d : U32)
