# Public-information local deduction for N x N (2 <= n <= 100).
# Only certified mine/safe indices and a revealed clue are inputs.
# A player's flag is NOT a certified mine. Never import mine truth here.
# One clue alone is incomplete; this is not a full N x N solver.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_neighbors.bend as Neighbors

type Decision is Type:
  Inconsistent{}
  NoMove{}
  Safe{indices: List<U32>}
  Mines{indices: List<U32>}

type Scan is Type:
  Scan{known: U32, unknown_count: U32, unknown: List<U32>, conflict: Bool}

def contains(+items: List<&2, U32>, +target: U32) -> Bool:
  match items:
    case Nil{}:
      False{}
    case first <> rest:
      Bool.or(U32.is_eq(first, target), contains(rest, target))

# Match an earlier parameter before inspecting a later resource binder.
# Bend 2 does not permit matching 'mine' after destructuring 'state'.
def add_mine(safe: Bool, state: Scan) -> Scan:
  match state:
    case Scan{known, unknown_count, unknown, conflict}:
      Scan{(known + 1 : U32), unknown_count, unknown, Bool.or(conflict, safe)}

def add_unknown(+index: U32, state: Scan) -> Scan:
  match state:
    case Scan{known, unknown_count, unknown, conflict}:
      Scan{known, (unknown_count + 1 : U32), index <> unknown, conflict}

def include_safe(+index: U32, safe: Bool, state: Scan) -> Scan:
  match safe:
    case True{}:
      state
    case False{}:
      add_unknown(index, state)

def include(+index: U32, mine: Bool, safe: Bool, state: Scan) -> Scan:
  match mine:
    case True{}:
      add_mine(safe, state)
    case False{}:
      include_safe(index, safe, state)

# Neighbors are ordered; recursion on the tail preserves that order.
def scan(items: List<U32>, +mines: List<&2, U32>, +safe: List<&2, U32>) -> Scan:
  match items:
    case Nil{}:
      Scan{0, 0, Nil{}, False{}}
    # Index is inspected in multiple independent tests; mark it duplicable.
    case +index <> rest:
      include(index, contains(mines, index), contains(safe, index),
              scan(rest, mines, safe))

def all_mines(equal: Bool, unknown: List<U32>) -> Decision:
  match equal:
    case True{}:
      Mines{unknown}
    case False{}:
      NoMove{}

def all_safe(zero: Bool, +remaining: U32, +count: U32, unknown: List<U32>) -> Decision:
  match zero:
    case True{}:
      Safe{unknown}
    case False{}:
      all_mines(U32.is_eq(remaining, count), unknown)

def nonempty(empty: Bool, +remaining: U32, +count: U32, unknown: List<U32>) -> Decision:
  match empty:
    case True{}:
      NoMove{}
    case False{}:
      all_safe(U32.is_eq(remaining, 0), remaining, count, unknown)

def checked(invalid: Bool, +remaining: U32, +count: U32, unknown: List<U32>) -> Decision:
  match invalid:
    case True{}:
      Inconsistent{}
    case False{}:
      nonempty(U32.is_eq(count, 0), remaining, count, unknown)

def from_scan(+clue: U32, state: Scan) -> Decision:
  match state:
    # Both counts feed the consistency checks and the decision boundary.
    # Bend's affine pattern binders must be marked duplicable here.
    case Scan{+known, +unknown_count, unknown, conflict}:
      +remaining = (clue - known : U32)
      checked(Bool.or(conflict, Bool.or(U32.is_lt(clue, known),
              U32.is_lt(unknown_count, remaining))),
              remaining, unknown_count, unknown)

def valid_input(valid: Bool, +n: U32, +index: U32, +clue: U32,
                +mines: List<&2, U32>, +safe: List<&2, U32>) -> Decision:
  match valid:
    case False{}:
      Inconsistent{}
    case True{}:
      from_scan(clue, scan(Neighbors.neighbors(n, index), mines, safe))

# The caller must certify the mine list, not infer it from flags.
# Indices outside this clue's neighborhood are ignored.
# Overlap within the neighborhood and impossible clues are rejected.
def infer(+n: U32, +index: U32, +clue: U32,
          +known_mines: List<&2, U32>, +known_safe: List<&2, U32>) -> Decision:
  valid_input(Bool.and(Geo.valid_index(n, index),
              Bool.and(U32.is_lt(clue, 9),
                       Bool.not(contains(known_mines, index)))),
              n, index, clue, known_mines, known_safe)

def tag(decision: Decision) -> U32:
  match decision:
    case Inconsistent{}:
      4
    case NoMove{}:
      3
    case Safe{indices}:
      1
    case Mines{indices}:
      2

# A 1 at (1,0) makes the other two neighbors of (0,0) safe.
def main() -> U32:
  tag(infer(3, 0, 1, [1], Nil{}))
