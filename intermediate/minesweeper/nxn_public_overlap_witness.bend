# A real 3x3 two-revealed-number witness without set containment.
# Revealed clues: cell 0 is 2; cell 2 is 1.
# Unknown neighbors A={1,3,4}, B={1,4,5}.
# Every compatible layout has cell 3 mined and cell 5 safe.
import Base
import ./nxn_public_overlap.bend as Overlap

def count(items: List<U32>) -> U32:
  match items:
    case Nil{}:
      0
    case value <> rest:
      (1 + count(rest) : U32)

def score(result: Overlap.Decision) -> U32:
  match result:
    case Overlap.Inconsistent{}:
      999
    case Overlap.Deduced{safe, mines}:
      (100 * count(safe) + count(mines) : U32)

def main() -> U32:
  score(Overlap.infer([1, 3, 4], [1, 4, 5], 2, 1))
