# Finite exact public-information solver for a 3x3 board (9 cells).
# Accepts visible clues and the public total mine count, NEVER a true board.
# Enumerates all 512 candidate masks; this is an educational finite kernel,
# not an efficient N x N solver or a no-guess board generator.
import Base
import ./nxn_neighbors.bend as Neighbors

type Number is Data:
  Number{index: U32, clue: U32}

type Decision is Type:
  Inconsistent{}
  Deduced{safe: U32, mines: U32, models: U32}

type Summary is Data:
  Summary{count: U32, union: U32, intersection: U32}

def bit_for(+index: U32) -> U32:
  U32.shln(1, U32.to_nat(index))

def contains_bit(+mask: U32, +index: U32) -> Bool:
  Bool.not(U32.is_eq(U32.and(mask, bit_for(index)), 0))

def one_if(yes: Bool) -> U32:
  match yes:
    case True{}:
      1
    case False{}:
      0

def mine_count(items: List<U32>, +mask: U32) -> U32:
  match items:
    case Nil{}:
      0
    case index <> rest:
      (one_if(contains_bit(mask, index)) + mine_count(rest, mask) : U32)

def count_all(+mask: U32) -> U32:
  mine_count([0, 1, 2, 3, 4, 5, 6, 7, 8], mask)

def valid_clues(items: List<&2, Number>, +seen: U32) -> Bool:
  match items:
    case Nil{}:
      True{}
    case Number{index, clue} <> rest:
      Bool.and(U32.is_lt(index, 9),
        Bool.and(U32.is_lt(clue, 9),
          Bool.and(Bool.not(contains_bit(seen, index)),
            valid_clues(rest, U32.or(seen, bit_for(index))))))

def matches(items: List<&2, Number>, +mask: U32) -> Bool:
  match items:
    case Nil{}:
      True{}
    case Number{index, clue} <> rest:
      Bool.and(Bool.not(contains_bit(mask, index)),
        Bool.and(U32.is_eq(mine_count(Neighbors.neighbors(3, index), mask), clue),
                 matches(rest, mask)))

def opened_bits(items: List<&2, Number>) -> U32:
  match items:
    case Nil{}:
      0
    case Number{index, clue} <> rest:
      U32.or(bit_for(index), opened_bits(rest))

def add_if(ok: Bool, summary: Summary, +mask: U32) -> Summary:
  match ok:
    case False{}:
      summary
    case True{}:
      match summary:
        case Summary{count, union, intersection}:
          Summary{(count + 1 : U32), U32.or(union, mask),
                  U32.and(intersection, mask)}

def scan(fuel: Nat, +clues: List<&2, Number>, +total: U32,
         summary: Summary) -> Summary:
  match fuel:
    case 0n:
      summary
    case 1n+k:
      +mask = U32.from_nat(k)
      +ok = Bool.and(U32.is_eq(count_all(mask), total), matches(clues, mask))
      scan(k, clues, total, add_if(ok, summary, mask))

def finish(zero: Bool, +opened: U32, +count: U32,
           +union: U32, +intersection: U32) -> Decision:
  match zero:
    case True{}:
      Inconsistent{}
    case False{}:
      Deduced{U32.and(U32.not(U32.or(union, opened)), 511),
              U32.and(intersection, U32.not(opened)), count}

def summarize(summary: Summary, +opened: U32) -> Decision:
  match summary:
    case Summary{count, union, intersection}:
      finish(U32.is_eq(count, 0), opened, count, union, intersection)

def check_input(valid: Bool, +clues: List<&2, Number>, +total: U32) -> Decision:
  match valid:
    case False{}:
      Inconsistent{}
    case True{}:
      summarize(scan(512n, clues, total, Summary{0, 0, 511}),
                opened_bits(clues))

# Clue indices must be distinct and within 0..8; the total is 0..9.
# The returned masks cover only unopened cells; no model => Inconsistent.
def infer(+clues: List<&2, Number>, +total: U32) -> Decision:
  check_input(Bool.and(U32.is_lt(total, 10), valid_clues(clues, 0)),
              clues, total)

# 3x3, clues 0=1, 2=1, 7=1, total mines=2:
# exactly {1,6} and {1,8} remain, so safe={3,4,5}, mines={1}.
def encode(result: Decision) -> U32:
  match result:
    case Inconsistent{}:
      0
    case Deduced{safe, mines, models}:
      U32.or(safe, U32.or(U32.shln(mines, 9n), U32.shln(models, 18n)))

def main() -> U32:
  encode(infer([Number{0, 1}, Number{2, 1}, Number{7, 1}], 2))
