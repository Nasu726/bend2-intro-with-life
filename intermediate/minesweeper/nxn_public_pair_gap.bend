# Two public clues show a deduction missed by the single-clue fixed point.
# Only public digits 1=1 and 4=1 and their UNKNOWN neighbor sets are used.
# The hidden mine layout and flags are never input to either solver.
import Base
import ./nxn_public_many_fixpoint.bend as Many
import ./nxn_public_three_fixpoint.bend as Fix
import ./nxn_public_subset.bend as Subset

def count(items: List<U32>) -> U32:
  match items:
    case Nil{}:
      0
    case item <> rest:
      (1 + count(rest) : U32)

def safe_count(result: Subset.Decision) -> U32:
  match result:
    case Subset.Safe{indices}:
      count(indices)
    case Subset.Mines{indices}:
      0
    case Subset.NoMove{}:
      0
    case Subset.Inconsistent{}:
      0

# Revealed cells are 1 and 4, each displaying 1.
# Unknown neighbors of 1: {0,2,3,5}; of 4: {0,2,3,5,6,7,8}.
# Their equal mine counts force the difference {6,7,8} to be safe.
# The first two digits of 203 mean single-rule certified-safe count = 2.
# The last digit means the subset rule adds 3 certified-safe cells.
def main() -> U32:
  +single = Fix.score(Many.infer_many(
    3, [Many.Clue{1, 1}, Many.Clue{4, 1}],
    10n, Nil{}, [1, 4]))
  +extra = safe_count(Subset.infer(
    [0, 2, 3, 5], [0, 2, 3, 5, 6, 7, 8], 1, 1))
  (100 * single + extra : U32)
