# Checked wrapper for arbitrary-count public-clue fixed-point inference.
# The reader ZIP retains its tested original sample; this experimental
# validation layer is repository-only until PDF/ZIP are rebuilt together.
# Only the structure of certified input sets can be verified here. The
# truth of extra certified cells remains the caller's responsibility.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_public_local.bend as Rule
import ./nxn_public_three_fixpoint.bend as Fix
import ./nxn_public_many_fixpoint.bend as Many

# Initial evidence is a sorted strictly increasing list of valid cell indices.
# Check disjointness against the opposite certified set. This rejects
# duplicate, unsorted, out-of-board, or overlapping initial evidence even
# when there are no revealed clues. Certification itself is external.
def after_previous(previous: Maybe<&2, U32>, +item: U32) -> Bool:
  match previous:
    case None{}:
      True{}
    case Some{old}:
      U32.is_lt(old, item)

def valid_initial_list(+n: U32, items: List<&2, U32>,
                       +other: List<&2, U32>, previous: Maybe<&2, U32>) -> Bool:
  match items:
    case Nil{}:
      True{}
    case +item <> rest:
      Bool.and(Geo.valid_index(n, item),
      Bool.and(after_previous(previous, item),
      Bool.and(Bool.not(Rule.contains(other, item)),
               valid_initial_list(n, rest, other, Some{item}))))

def valid_initial(+n: U32, +mines: List<&2, U32>,
                  +safe: List<&2, U32>) -> Bool:
  Bool.and(valid_initial_list(n, mines, safe, None{}),
           valid_initial_list(n, safe, mines, None{}))

def checked(ok: Bool, +n: U32, +clues: List<&2, Many.Clue>,
            fuel: Nat, mines: List<&2, U32>, safe: List<&2, U32>) -> Fix.Propagation:
  match ok:
    case False{}:
      Fix.Inconsistent{}
    case True{}:
      Many.infer_many(n, clues, fuel, mines, safe)

# Validate even when there are zero clues; do not turn bad input into Closure.
def infer_many_checked(+n: U32, +clues: List<&2, Many.Clue>, fuel: Nat,
                       +mines: List<&2, U32>, +safe: List<&2, U32>) -> Fix.Propagation:
  checked(valid_initial(n, mines, safe), n, clues, fuel, mines, safe)

# Same visible result as the learner's four-clue example: 6.
def main() -> U32:
  Fix.score(infer_many_checked(3, [Many.Clue{1, 1}, Many.Clue{2, 0},
                                   Many.Clue{4, 1}, Many.Clue{5, 0}],
                               10n, Nil{}, [1, 2, 4, 5]))
