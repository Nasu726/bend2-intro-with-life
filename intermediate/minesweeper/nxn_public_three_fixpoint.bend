# Automatic fixed-point propagation across exactly THREE public clues.
# Each clue index MUST appear in initially_known_safe (revealed is safe).
# Other initial entries must be independently certified; flags are not proof.
# No hidden mine layout or global mine count is supplied to this module.
# This is single-clue propagation, NOT arbitrary frontier inference.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_public_local.bend as Rule

type Propagation is Type:
  Inconsistent{}
  Limit{}
  Closure{mines: List<&2, U32>, safe: List<&2, U32>, changed: Bool}

def prepend(items: List<U32>, rest: List<&2, U32>) -> List<&2, U32>:
  match items:
    case Nil{}:
      rest
    case +item <> tail:
      item <> prepend(tail, rest)

# Rule.infer returns only cells not already certified, so prepend cannot
# introduce duplicate decisions if the initial sets are well-formed.
def accept(decision: Rule.Decision, mines: List<&2, U32>, safe: List<&2, U32>,
           changed: Bool) -> Propagation:
  match decision:
    case Rule.Inconsistent{}:
      Inconsistent{}
    case Rule.NoMove{}:
      Closure{mines, safe, changed}
    case Rule.Safe{indices}:
      Closure{mines, prepend(indices, safe), True{}}
    case Rule.Mines{indices}:
      Closure{prepend(indices, mines), safe, True{}}

# The state stores reusable List<&2,U32> values. Unlike an affine List,
# they can be passed to Rule.infer and retained for the next clue.
def apply(+n: U32, +cell: U32, +clue: U32, state: Propagation) -> Propagation:
  match state:
    case Inconsistent{}:
      Inconsistent{}
    case Limit{}:
      Limit{}
    case Closure{+mines, +safe, changed}:
      accept(Rule.infer(n, cell, clue, mines, safe), mines, safe, changed)

def one_round(+n: U32, +c0: U32, +v0: U32, +c1: U32, +v1: U32,
              +c2: U32, +v2: U32, state: Propagation) -> Propagation:
  apply(n, c2, v2, apply(n, c1, v1, apply(n, c0, v0, state)))

def exhausted(state: Propagation) -> Propagation:
  match state:
    case Inconsistent{}:
      Inconsistent{}
    case Limit{}:
      Limit{}
    case Closure{mines, safe, changed}:
      match changed:
        case False{}:
          Closure{mines, safe, False{}}
        case True{}:
          Limit{}

# At most three clues, each with at most eight neighbors, can certify at
# most 24 previously unknown cells. After 25 complete rounds the last round
# must be unchanged. A Nat fuel guarantees termination even for bad inputs.
def reset(state: Propagation) -> Propagation:
  match state:
    case Inconsistent{}:
      Inconsistent{}
    case Limit{}:
      Limit{}
    case Closure{mines, safe, changed}:
      Closure{mines, safe, False{}}

def iterate(fuel: Nat, +n: U32, +c0: U32, +v0: U32,
            +c1: U32, +v1: U32, +c2: U32, +v2: U32,
            state: Propagation) -> Propagation:
  match fuel:
    case 0n:
      exhausted(state)
    case 1n+k:
      iterate(k, n, c0, v0, c1, v1, c2, v2,
              one_round(n, c0, v0, c1, v1, c2, v2, reset(state)))

def checked(ok: Bool, +n: U32, +c0: U32, +v0: U32,
            +c1: U32, +v1: U32, +c2: U32, +v2: U32,
            mines: List<&2, U32>, safe: List<&2, U32>) -> Propagation:
  match ok:
    case False{}:
      Inconsistent{}
    case True{}:
      iterate(25n, n, c0, v0, c1, v1, c2, v2,
              Closure{mines, safe, False{}})

# Contract: three DISTINCT revealed clues; known_safe includes their cells.
# Other safe/mine cells are separately certified, sorted/unique/in-range.
# Invalid clues and contradictory local constraints return Inconsistent.
def infer_three(+n: U32, +c0: U32, +v0: U32,
                +c1: U32, +v1: U32, +c2: U32, +v2: U32,
                mines: List<&2, U32>, +safe: List<&2, U32>) -> Propagation:
  checked(Bool.and(Geo.valid_index(n, c0),
          Bool.and(Geo.valid_index(n, c1),
          Bool.and(Geo.valid_index(n, c2),
          Bool.and(Bool.not(U32.is_eq(c0, c1)),
          Bool.and(Bool.not(U32.is_eq(c0, c2)),
          Bool.and(Bool.not(U32.is_eq(c1, c2)),
          Bool.and(Rule.contains(safe, c0),
          Bool.and(Rule.contains(safe, c1),
                   Rule.contains(safe, c2))))))))),
          n, c0, v0, c1, v1, c2, v2, mines, safe)

def size(items: List<&2, U32>) -> U32:
  match items:
    case Nil{}:
      0
    case item <> rest:
      (1 + size(rest) : U32)

def score(result: Propagation) -> U32:
  match result:
    case Inconsistent{}:
      0
    case Limit{}:
      1
    case Closure{mines, safe, changed}:
      ((100 * size(mines) + size(safe) : U32))

# Public: 0 -> 0 mines, 2 -> 1 mine, 6 -> 1 mine.
# The first clue certifies safe 1/3/4, then clues 2/6 certify mines 5/7.
# Safe includes the three revealed clue cells, so score = 2*100+6=206.
def main() -> U32:
  score(infer_three(3, 0, 0, 2, 1, 6, 1, Nil{}, [0, 2, 6]))
