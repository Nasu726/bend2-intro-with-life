# Fixed-point propagation for any number of revealed public clues.
# Public clues and independently certified mines/safe cells are the ONLY input.
# Flags/hidden mine truth/total mine count must NOT enter this inference rule.
# This is repeatable single-clue deduction, NOT general constraint solving.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_public_local.bend as Rule
import ./nxn_public_three_fixpoint.bend as Fix

type Clue is Type:
  Clue{index: U32, value: U32}

# Reject repeated/out-of-range/unrevealed public digits. Every opened clue
# must appear in the initial safe set; flags are not a substitute.
# The remaining initial evidence must be sorted/unique/in-range/consistent,
# and independently certified by the caller.
def valid_clues(+n: U32, clues: List<&2, Clue>,
                +safe: List<&2, U32>, +seen: List<&2, U32>) -> Bool:
  match clues:
    case Nil{}:
      True{}
    case item <> rest:
      match item:
        case Clue{+index, value}:
          Bool.and(Geo.valid_index(n, index),
          Bool.and(U32.is_lt(value, 9),
          Bool.and(Rule.contains(safe, index),
          Bool.and(Bool.not(Rule.contains(seen, index)),
                   valid_clues(n, rest, safe, index <> seen)))))

# A full round runs the same single-number rule once for each revealed digit.
# Applying the remaining rules first changes only the order of propagation,
# not its fixed-point result. The loop is monotone on certified cell sets.
def one_round(+n: U32, clues: List<&2, Clue>,
              state: Fix.Propagation) -> Fix.Propagation:
  match clues:
    case Nil{}:
      state
    case item <> rest:
      match item:
        case Clue{index, value}:
          Fix.apply(n, index, value, one_round(n, rest, state))

# Terminate as soon as an entire round adds no new certified cells.
# Out of fuel with changes still pending is Limit, never Closure.
def after_round(state: Fix.Propagation, fuel: Nat, +n: U32,
                +clues: List<&2, Clue>) -> Fix.Propagation:
  match state:
    case Fix.Inconsistent{}:
      Fix.Inconsistent{}
    case Fix.Limit{}:
      Fix.Limit{}
    case Fix.Closure{mines, safe, changed}:
      match changed:
        case False{}:
          Fix.Closure{mines, safe, False{}}
        case True{}:
          iterate(fuel, n, clues, Fix.Closure{mines, safe, True{}})

def iterate(fuel: Nat, +n: U32, +clues: List<&2, Clue>,
            state: Fix.Propagation) -> Fix.Propagation:
  match fuel:
    case 0n:
      Fix.Limit{}
    case 1n+k:
      after_round(one_round(n, clues, Fix.reset(state)), k, n, clues)

def checked(ok: Bool, fuel: Nat, +n: U32,
            +clues: List<&2, Clue>,
            mines: List<&2, U32>, safe: List<&2, U32>) -> Fix.Propagation:
  match ok:
    case False{}:
      Fix.Inconsistent{}
    case True{}:
      iterate(fuel, n, clues, Fix.Closure{mines, safe, False{}})

# Fuel is the maximum number of complete clue sweeps; n*n+1 suffices when
# the input evidence is valid (each changing sweep certifies a fresh cell).
# Bad/short fuel is detectable as Limit. Empty clue lists are allowed.
def infer_many(+n: U32, +clues: List<&2, Clue>, fuel: Nat,
               mines: List<&2, U32>, +safe: List<&2, U32>) -> Fix.Propagation:
  checked(Bool.and(Geo.valid_size(n), valid_clues(n, clues, safe, Nil{})),
          fuel, n, clues, mines, safe)

# 3x3 public digits 1/2/4/5: four revealed cells establish safety of 7/8.
# The result is a number for the book: 100*certified_mines+certified_safe = 6.
def main() -> U32:
  Fix.score(infer_many(3, [Clue{1, 1}, Clue{2, 0},
                           Clue{4, 1}, Clue{5, 0}],
                       10n, Nil{}, [1, 2, 4, 5]))
