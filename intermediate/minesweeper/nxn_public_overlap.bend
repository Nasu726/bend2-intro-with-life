# Exact two-clue region bounds for public N x N Minesweeper constraints.
# A and B are distinct sorted unknown-neighbor indices from revealed clues.
# ra/rb are residual mine counts after CERTIFIED mine deductions, never flags.
# No hidden mine board enters this pure inference kernel.
import Base
import ./nxn_public_subset.bend as Subset

type Decision is Type:
  Inconsistent{}
  Deduced{safe: List<U32>, mines: List<U32>}

type Scan is Type:
  Scan{safe: List<U32>, mines: List<U32>}

def plus_if(yes: Bool, rest: U32) -> U32:
  match yes:
    case True{}:
      (1 + rest : U32)
    case False{}:
      rest

def intersection_size(items: List<&2, U32>, +other: List<&2, U32>) -> U32:
  match items:
    case Nil{}:
      0
    case value <> rest:
      plus_if(Subset.contains(other, value), intersection_size(rest, other))

# Match on a function parameter, not on a computed/local scrutinee.
# Bend 2.0.39 requires the parameter in a separate helper definition.
def minimum_if(less: Bool, +a: U32, +b: U32) -> U32:
  match less:
    case True{}:
      a
    case False{}:
      b

def minimum(+a: U32, +b: U32) -> U32:
  minimum_if(U32.is_lt(a, b), a, b)

def maximum_if(less: Bool, +a: U32, +b: U32) -> U32:
  match less:
    case True{}:
      b
    case False{}:
      a

def maximum(+a: U32, +b: U32) -> U32:
  maximum_if(U32.is_lt(a, b), a, b)

def nonnegative_difference_if(less: Bool, +a: U32, +b: U32) -> U32:
  match less:
    case True{}:
      0
    case False{}:
      (a - b : U32)

def nonnegative_difference(+a: U32, +b: U32) -> U32:
  nonnegative_difference_if(U32.is_lt(a, b), a, b)

def add_safe(+index: U32, state: Scan) -> Scan:
  match state:
    case Scan{safe, mines}:
      Scan{index <> safe, mines}

def add_mine(+index: U32, state: Scan) -> Scan:
  match state:
    case Scan{safe, mines}:
      Scan{safe, index <> mines}

# All cells in a region are safe if its maximum mine count is zero.
# All cells are mines if its minimum equals the region size.
def classify_mine(yes: Bool, +index: U32, state: Scan) -> Scan:
  match yes:
    case True{}:
      add_mine(index, state)
    case False{}:
      state

def classify_safe(yes: Bool, +index: U32, +minimum_mines: U32,
                  +count: U32, state: Scan) -> Scan:
  match yes:
    case True{}:
      add_safe(index, state)
    case False{}:
      classify_mine(U32.is_eq(minimum_mines, count), index, state)

def classify(+index: U32, +minimum_mines: U32, +maximum_mines: U32,
             +count: U32, state: Scan) -> Scan:
  classify_safe(U32.is_eq(maximum_mines, 0), index,
                minimum_mines, count, state)

# Process B-only cells first; then A. Output order is A followed by B-only.
def scan_b_if(belongs_to_a: Bool, +index: U32,
              +y_min: U32, +y_max: U32, +y_count: U32,
              state: Scan) -> Scan:
  match belongs_to_a:
    case True{}:
      state
    case False{}:
      classify(index, y_min, y_max, y_count, state)

def scan_b(items: List<&2, U32>, +a: List<&2, U32>,
           +y_min: U32, +y_max: U32, +y_count: U32, state: Scan) -> Scan:
  match items:
    case Nil{}:
      state
    case +index <> rest:
      scan_b_if(Subset.contains(a, index), index,
                y_min, y_max, y_count,
                scan_b(rest, a, y_min, y_max, y_count, state))

def scan_a_if(belongs_to_b: Bool, +index: U32,
              +x_min: U32, +x_max: U32, +x_count: U32,
              +i_min: U32, +i_max: U32, +i_count: U32,
              state: Scan) -> Scan:
  match belongs_to_b:
    case True{}:
      classify(index, i_min, i_max, i_count, state)
    case False{}:
      classify(index, x_min, x_max, x_count, state)

def scan_a(items: List<&2, U32>, +b: List<&2, U32>,
           +x_min: U32, +x_max: U32, +x_count: U32,
           +i_min: U32, +i_max: U32, +i_count: U32, state: Scan) -> Scan:
  match items:
    case Nil{}:
      state
    case +index <> rest:
      scan_a_if(Subset.contains(b, index), index,
                x_min, x_max, x_count, i_min, i_max, i_count,
                scan_a(rest, b, x_min, x_max, x_count,
                       i_min, i_max, i_count, state))

def finish(state: Scan) -> Decision:
  match state:
    case Scan{safe, mines}:
      Deduced{safe, mines}

# Let t be the number of mines in I=A intersection B.
# max(0, ra-|A\B|, rb-|B\A|) <= t <= min(|I|, ra, rb).
# Bounds are exact because every integer t in this interval is realizable.
def bounds_if(contradiction: Bool, +a: List<&2, U32>,
              +b: List<&2, U32>, +ra: U32, +rb: U32,
              +lower: U32, +upper: U32, +i_count: U32,
              +x_count: U32, +y_count: U32) -> Decision:
  match contradiction:
    case True{}:
      Inconsistent{}
    case False{}:
      +x_min = (ra - upper : U32)
      +x_max = (ra - lower : U32)
      +y_min = (rb - upper : U32)
      +y_max = (rb - lower : U32)
      finish(scan_a(a, b, x_min, x_max, x_count,
                    lower, upper, i_count,
                    scan_b(b, a, y_min, y_max, y_count,
                           Scan{Nil{}, Nil{}})))

def bounds(+a: List<&2, U32>, +b: List<&2, U32>,
           +ra: U32, +rb: U32, +i_count: U32,
           +x_count: U32, +y_count: U32) -> Decision:
  +lower = maximum(nonnegative_difference(ra, x_count),
                   nonnegative_difference(rb, y_count))
  +upper = minimum(i_count, minimum(ra, rb))
  bounds_if(U32.is_lt(upper, lower), a, b, ra, rb,
            lower, upper, i_count, x_count, y_count)

def valid(ok: Bool, +a: List<&2, U32>, +b: List<&2, U32>,
          +ra: U32, +rb: U32, +i_count: U32,
          +x_count: U32, +y_count: U32) -> Decision:
  match ok:
    case False{}:
      Inconsistent{}
    case True{}:
      bounds(a, b, ra, rb, i_count, x_count, y_count)

# Input lists must be duplicate-free, sorted, and derived from PUBLIC clues.
# Unlike the subset-only kernel, A and B need not contain each other.
def infer(+a: List<&2, U32>, +b: List<&2, U32>,
          +ra: U32, +rb: U32) -> Decision:
  +i_count = intersection_size(a, b)
  +a_count = Subset.size(a)
  +b_count = Subset.size(b)
  +x_count = (a_count - i_count : U32)
  +y_count = (b_count - i_count : U32)
  valid(Bool.and(Bool.not(U32.is_lt(a_count, ra)),
                 Bool.not(U32.is_lt(b_count, rb))),
        a, b, ra, rb, i_count, x_count, y_count)

def tag(decision: Decision) -> U32:
  match decision:
    case Inconsistent{}:
      4
    case Deduced{safe, mines}:
      1

# A={1,2,3}, B={2,3,4}, residual counts 1 and 2:
# cell 1 is safe, cell 4 is a mine, while 2 and 3 remain uncertain.
def main() -> U32:
  tag(infer([1, 2, 3], [2, 3, 4], 1, 2))
