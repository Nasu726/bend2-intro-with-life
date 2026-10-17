# Exact public-information solver for a fixed 4x4 board with TWO mines.
# It examines all C(16,2) = 120 candidate mine pairs, NEVER the true board mask.
# Input: only revealed (index,clue) records. Output: proven-safe hidden bits.
# If the constraints are inconsistent, return None rather than invent moves.
import Base
import ./board4.bend as Board4

type Number is Data:
  Number{index: U32, clue: U32}

type Public is Data:
  Public{opened: List<&2, Number>}

type Summary is Data:
  Summary{count: U32, union: U32}

def test_numbers(+entries: List<&2, Number>, +candidate: U32) -> Bool:
  match entries:
    case Nil{}:
      True{}
    case Number{index, clue} <> rest:
      ok = Bool.and(U32.is_lt(index, 16),
        Bool.and(
          Bool.not(Board4.bit_is_set(candidate, U32.shln(1, U32.to_nat(index)))),
          U32.is_eq(Board4.clue(candidate, U32.mod(index, 4), U32.div(index, 4)), clue)))
      Bool.and(ok, test_numbers(rest, candidate))

def valid(view: Public, candidate: U32) -> Bool:
  match view:
    case Public{opened}:
      test_numbers(opened, candidate)

def add_if(ok: Bool, summary: Summary, +candidate: U32) -> Summary:
  match ok:
    case False{}:
      summary
    case True{}:
      match summary:
        case Summary{count, union}:
          Summary{(count + 1 : U32), U32.or(union, candidate)}

# Structural descent on the FIRST Nat argument.
def columns(+fuel: Nat, +i: U32, +view: Public, summary: Summary) -> Summary:
  match fuel:
    case 0n:
      summary
    case 1n+k:
      j = U32.from_nat(k)
      mask = U32.or(U32.shln(1, U32.to_nat(i)), U32.shln(1, k))
      ok = Bool.and(U32.is_lt(i, j), valid(view, mask))
      columns(k, i, view, add_if(ok, summary, mask))

def rows(+fuel: Nat, +view: Public, summary: Summary) -> Summary:
  match fuel:
    case 0n:
      summary
    case 1n+k:
      i = U32.from_nat(k)
      rows(k, view, columns(16n, i, view, summary))

def opened_bits(entries: List<&2, Number>) -> U32:
  match entries:
    case Nil{}:
      0
    case Number{index, clue} <> rest:
      U32.or(U32.shln(1, U32.to_nat(index)), opened_bits(rest))

def safe_for_count(zero: Bool, union: U32, already: U32) -> Maybe<&2, U32>:
  match zero:
    case True{}:
      None{}
    case False{}:
      Some{U32.and(U32.not(U32.or(union, already)), 65535)}

def safe_result(result: Summary, already: U32) -> Maybe<&2, U32>:
  match result:
    case Summary{count, union}:
      safe_for_count(U32.is_eq(count, 0), union, already)

def provably_safe(+view: Public) -> Maybe<&2, U32>:
  match view:
    case Public{+opened}:
      safe_result(rows(16n, Public{opened}, Summary{0, 0}),
        opened_bits(opened))

def value_or_zero(m: Maybe<&2, U32>) -> U32:
  match m:
    case Some{bits}:
      bits
    case None{}:
      0

# For clue 0 at top-left, 1,4,5 are necessarily safe.
def main() -> U32:
  value_or_zero(provably_safe(Public{[Number{0, 0}]}))
