# Two REAL 3x3 public clues whose unknown neighbors overlap but are not nested.
# The single-clue fixed point and the subset-only rule cannot decide any cell.
# Only public clues and their UNKNOWN neighbors are given to the overlap kernel.
# Truth mines and user flags are never passed to the inference functions.
import Base
import ./nxn_public_many_fixpoint.bend as Many
import ./nxn_public_three_fixpoint.bend as Fix
import ./nxn_public_overlap.bend as Overlap

def count(items: List<U32>) -> U32:
  match items:
    case Nil{}:
      0
    case item <> rest:
      (1 + count(rest) : U32)

def extra_score(result: Overlap.Decision) -> U32:
  match result:
    case Overlap.Inconsistent{}:
      0
    case Overlap.Deduced{safe, mines}:
      (10 * count(safe) + count(mines) : U32)

# Revealed 0=1 and 2=2; the two revealed cells are certified safe.
# A={1,3,4}, B={1,4,5}. Shared I={1,4}; X={3}; Y={5}.
# The shared mine count must be one, so 3 is safe and 5 is a mine.
# Output 211 means 2 known safe + 1 additional safe + 1 additional mine.
def main() -> U32:
  +single = Fix.score(Many.infer_many(
    3, [Many.Clue{0, 1}, Many.Clue{2, 2}],
    10n, Nil{}, [0, 2]))
  +extra = extra_score(Overlap.infer([1, 3, 4], [1, 4, 5], 1, 2))
  (100 * single + extra : U32)
