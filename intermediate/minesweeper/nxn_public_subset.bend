# Two-public-clue subset rule for N x N Minesweeper (2 <= N <= 100).
# Inputs are the UNKNOWN neighbors and residual mine counts of TWO revealed
# clues, after subtracting CERTIFIED mines and excluding certified safe cells.
# A flag alone is not a certified mine. Sets must be unique and sorted.
# This is a sound two-constraint kernel, not a complete frontier solver.
import Base

type Decision is Type:
  Inconsistent{}
  NoMove{}
  Safe{indices: List<U32>}
  Mines{indices: List<U32>}

def contains(items: List<&2, U32>, +target: U32) -> Bool:
  match items:
    case Nil{}:
      False{}
    case value <> rest:
      Bool.or(U32.is_eq(value, target), contains(rest, target))

def size(items: List<&2, U32>) -> U32:
  match items:
    case Nil{}:
      0
    case value <> rest:
      (1 + size(rest) : U32)

def subset(items: List<&2, U32>, +superset: List<&2, U32>) -> Bool:
  match items:
    case Nil{}:
      True{}
    case value <> rest:
      Bool.and(contains(superset, value), subset(rest, superset))

def keep(yes: Bool, +index: U32, rest: List<U32>) -> List<U32>:
  match yes:
    case True{}:
      index <> rest
    case False{}:
      rest

def difference(items: List<&2, U32>, +remove: List<&2, U32>) -> List<U32>:
  match items:
    case Nil{}:
      Nil{}
    case +index <> rest:
      keep(Bool.not(contains(remove, index)), index, difference(rest, remove))

# Count directly from the borrowed input. A newly constructed difference
# list has affine elements and cannot be borrowed again as List<&2, U32>.
def plus_if(yes: Bool, rest: U32) -> U32:
  match yes:
    case True{}:
      (1 + rest : U32)
    case False{}:
      rest

def difference_size(items: List<&2, U32>, +remove: List<&2, U32>) -> U32:
  match items:
    case Nil{}:
      0
    case value <> rest:
      plus_if(Bool.not(contains(remove, value)), difference_size(rest, remove))

def all_mines(yes: Bool, indices: List<U32>) -> Decision:
  match yes:
    case True{}:
      Mines{indices}
    case False{}:
      NoMove{}

def all_safe(yes: Bool, +delta: U32, +count: U32, indices: List<U32>) -> Decision:
  match yes:
    case True{}:
      Safe{indices}
    case False{}:
      all_mines(U32.is_eq(delta, count), indices)

def nonempty(empty: Bool, +delta: U32, +count: U32, indices: List<U32>) -> Decision:
  match empty:
    case True{}:
      NoMove{}
    case False{}:
      all_safe(U32.is_eq(delta, 0), delta, count, indices)

def feasible(ok: Bool, +delta: U32, +count: U32, indices: List<U32>) -> Decision:
  match ok:
    case False{}:
      Inconsistent{}
    case True{}:
      nonempty(U32.is_eq(count, 0), delta, count, indices)

# If A is contained in B, subtract the two public equations:
# mines(B \ A) = residual(B) - residual(A).
def nested(+small_remaining: U32, +large_remaining: U32,
           +small: List<&2, U32>, +large: List<&2, U32>) -> Decision:
  indices = difference(large, small)
  +count = difference_size(large, small)
  +delta = (large_remaining - small_remaining : U32)
  ok = Bool.and(Bool.not(U32.is_lt(large_remaining, small_remaining)),
                Bool.not(U32.is_lt(count, delta)))
  feasible(ok, delta, count, indices)

def reverse(yes: Bool, +a: List<&2, U32>, +b: List<&2, U32>,
            +ra: U32, +rb: U32) -> Decision:
  match yes:
    case True{}:
      nested(rb, ra, b, a)
    case False{}:
      NoMove{}

def forward(yes: Bool, +a: List<&2, U32>, +b: List<&2, U32>,
            +ra: U32, +rb: U32) -> Decision:
  match yes:
    case True{}:
      nested(ra, rb, a, b)
    case False{}:
      reverse(subset(b, a), a, b, ra, rb)

def checked(ok: Bool, +a: List<&2, U32>, +b: List<&2, U32>,
            +ra: U32, +rb: U32) -> Decision:
  match ok:
    case True{}:
      forward(subset(a, b), a, b, ra, rb)
    case False{}:
      Inconsistent{}

# Only valid, unique unknown-neighbor sets derived from PUBLIC clues are inputs.
# Non-nested constraints return NoMove even if a stronger solver could deduce
# something or detect a contradiction.
def infer(+a: List<&2, U32>, +b: List<&2, U32>,
          +ra: U32, +rb: U32) -> Decision:
  checked(Bool.and(Bool.not(U32.is_lt(size(a), ra)),
                   Bool.not(U32.is_lt(size(b), rb))),
          a, b, ra, rb)

def tag(decision: Decision) -> U32:
  match decision:
    case Safe{indices}:
      1
    case Mines{indices}:
      2
    case NoMove{}:
      3
    case Inconsistent{}:
      4

# 3x3: clue at 0 and clue at 1 are both 1; both clues are revealed.
# Unknown neighbors: {3,4} and {2,3,4,5}; hence 2 and 5 are safe.
def main() -> U32:
  tag(infer([3, 4], [2, 3, 4, 5], 1, 1))
