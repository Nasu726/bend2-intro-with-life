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
  Closure{mines: List<U32>, safe: List<U32>, changed: Bool}

def prepend(items: List<U32>, rest: List<U32>) -> List<U32>:
  match items:
    case Nil{}:
      rest
    case item <> tail:
      item <> prepend(tail, rest)

# Rule.infer returns only cells not already certified, so prepend cannot
# introduce duplicate decisions if the initial sets are well-formed.
def accept(decision: Rule.Decision, mines: List<U32>, safe: List<U32>,
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

# Lists are affine in Bend 2: explicitly copy each list before passing it to
# the one-clue kernel while retaining the state for the next deduction.
def duplicate_step(+item: U32, copies: List<U32> & List<U32>) -> List<U32> & List<U32>:
  (left, right) = copies
  (item <> left, item <> right)

def duplicate(items: List<U32>) -> List<U32> & List<U32>:
  match items:
    case Nil{}:
      (Nil{}, Nil{})
    case +item <> tail:
      duplicate_step(item, duplicate(tail))

def apply_with_safe(+n: U32, +cell: U32, +clue: U32,
                    mines_for_rule: List<U32>, mines_keep: List<U32>,
                    copies: List<U32> & List<U32>, changed: Bool) -> Propagation:
  (safe_for_rule, safe_keep) = copies
  accept(Rule.infer(n, cell, clue, mines_for_rule, safe_for_rule),
         mines_keep, safe_keep, changed)

def apply_with_mines(+n: U32, +cell: U32, +clue: U32,
                     copies: List<U32> & List<U32>, safe: List<U32>,
                     changed: Bool) -> Propagation:
  (mines_for_rule, mines_keep) = copies
  apply_with_safe(n, cell, clue, mines_for_rule, mines_keep,
                  duplicate(safe), changed)

def apply(+n: U32, +cell: U32, +clue: U32, state: Propagation) -> Propagation:
  match state:
    case Inconsistent{}:
      Inconsistent{}
    case Limit{}:
      Limit{}
    case Closure{mines, safe, changed}:
      apply_with_mines(n, cell, clue, duplicate(mines), safe, changed)

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
            mines: List<U32>, safe: List<U32>) -> Propagation:
  match ok:
    case False{}:
      Inconsistent{}
    case True{}:
      iterate(25n, n, c0, v0, c1, v1, c2, v2,
              Closure{mines, safe, False{}})

# Check three public positions with one traversal of the affine safe list.
def contains_all(items: List<U32>, +c0: U32, +c1: U32, +c2: U32,
                 +seen0: Bool, +seen1: Bool, +seen2: Bool) -> Bool:
  match items:
    case Nil{}:
      Bool.and(seen0, Bool.and(seen1, seen2))
    case +item <> rest:
      contains_all(rest, c0, c1, c2,
                   Bool.or(seen0, U32.is_eq(item, c0)),
                   Bool.or(seen1, U32.is_eq(item, c1)),
                   Bool.or(seen2, U32.is_eq(item, c2)))

# Contract: three DISTINCT revealed clues; known_safe includes their cells.
# Other safe/mine cells are separately certified, sorted/unique/in-range.
# Invalid clues and contradictory local constraints return Inconsistent.
def infer_three_with_safe(+n: U32, +c0: U32, +v0: U32,
                +c1: U32, +v1: U32, +c2: U32, +v2: U32,
                mines: List<U32>, copies: List<U32> & List<U32>) -> Propagation:
  (safe_for_check, safe_keep) = copies
  checked(Bool.and(Geo.valid_index(n, c0),
          Bool.and(Geo.valid_index(n, c1),
          Bool.and(Geo.valid_index(n, c2),
          Bool.and(Bool.not(U32.is_eq(c0, c1)),
          Bool.and(Bool.not(U32.is_eq(c0, c2)),
          Bool.and(Bool.not(U32.is_eq(c1, c2)),
          contains_all(safe_for_check, c0, c1, c2,
                       False{}, False{}, False{}))))))),
          n, c0, v0, c1, v1, c2, v2, mines, safe_keep)

def infer_three(+n: U32, +c0: U32, +v0: U32,
                +c1: U32, +v1: U32, +c2: U32, +v2: U32,
                mines: List<U32>, safe: List<U32>) -> Propagation:
  infer_three_with_safe(n, c0, v0, c1, v1, c2, v2, mines,
                        duplicate(safe))

def size(items: List<U32>) -> U32:
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
