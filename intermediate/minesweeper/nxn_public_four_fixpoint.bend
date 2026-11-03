# Four distinct public clues: repeat the existing certified single-clue rule.
# Input safe cells must contain all four revealed clue positions. Flags and
# hidden mine truth are not evidence. This is NOT full frontier inference.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_public_local.bend as Rule
import ./nxn_public_three_fixpoint.bend as Fix

# Reuse the established three-clue round, then visit the fourth clue.
def one_round(+n: U32, +c0: U32, +v0: U32, +c1: U32, +v1: U32,
              +c2: U32, +v2: U32, +c3: U32, +v3: U32,
              state: Fix.Propagation) -> Fix.Propagation:
  Fix.apply(n, c3, v3, Fix.one_round(n, c0, v0, c1, v1, c2, v2, state))

# Four clue neighborhoods contain at most 4*8=32 cells. Every round that
# changes the state certifies at least one previously unknown cell. Round 33
# must therefore be unchanged. Limit is not interpreted as a solution.
def iterate(fuel: Nat, +n: U32, +c0: U32, +v0: U32,
            +c1: U32, +v1: U32, +c2: U32, +v2: U32,
            +c3: U32, +v3: U32, state: Fix.Propagation) -> Fix.Propagation:
  match fuel:
    case 0n:
      Fix.exhausted(state)
    case 1n+k:
      iterate(k, n, c0, v0, c1, v1, c2, v2, c3, v3,
              one_round(n, c0, v0, c1, v1, c2, v2, c3, v3,
                        Fix.reset(state)))

def run(valid: Bool, +n: U32, +c0: U32, +v0: U32,
        +c1: U32, +v1: U32, +c2: U32, +v2: U32,
        +c3: U32, +v3: U32,
        mines: List<&2, U32>, safe: List<&2, U32>) -> Fix.Propagation:
  match valid:
    case False{}:
      Fix.Inconsistent{}
    case True{}:
      iterate(33n, n, c0, v0, c1, v1, c2, v2, c3, v3,
              Fix.Closure{mines, safe, False{}})

# Caller contract: initial evidence is unique, in-range, and independently
# certified. Explicitly reject invalid/duplicate/unrevealed clue positions;
# Rule.infer rejects impossible local numbers and conflicting known neighbors.
def infer_four(+n: U32, +c0: U32, +v0: U32,
               +c1: U32, +v1: U32, +c2: U32, +v2: U32,
               +c3: U32, +v3: U32,
               mines: List<&2, U32>, +safe: List<&2, U32>) -> Fix.Propagation:
  run(Bool.and(Geo.valid_index(n, c0),
      Bool.and(Geo.valid_index(n, c1),
      Bool.and(Geo.valid_index(n, c2),
      Bool.and(Geo.valid_index(n, c3),
      Bool.and(Bool.not(U32.is_eq(c0, c1)),
      Bool.and(Bool.not(U32.is_eq(c0, c2)),
      Bool.and(Bool.not(U32.is_eq(c0, c3)),
      Bool.and(Bool.not(U32.is_eq(c1, c2)),
      Bool.and(Bool.not(U32.is_eq(c1, c3)),
      Bool.and(Bool.not(U32.is_eq(c2, c3)),
      Bool.and(Rule.contains(safe, c0),
      Bool.and(Rule.contains(safe, c1),
      Bool.and(Rule.contains(safe, c2),
               Rule.contains(safe, c3)))))))))))))),
      n, c0, v0, c1, v1, c2, v2, c3, v3, mines, safe)

# 3x3: clues (1,1), (2,0), (4,1), (5,0) certify 7 and 8 as safe.
# No mine becomes certain; safe contains 1,2,4,5,7,8 (score = 6).
def main() -> U32:
  Fix.score(infer_four(3, 1, 1, 2, 0, 4, 1, 5, 0, Nil{}, [1, 2, 4, 5]))
