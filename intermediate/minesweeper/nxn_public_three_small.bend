# Exact bounded THREE-clue public deduction on at most six unknown cells.
# Each bit 0..5 is one public unknown-neighbor index, mapped by the caller.
# No true mine board or unverified player flags enter this function.
# This is a six-variable kernel, NOT a general N x N frontier solver.
import Base

type Decision is Type:
  Inconsistent{}
  Forced{safe: U32, mines: U32, models: U32}

type Summary is Data:
  Summary{models: U32, union: U32, common: U32}

# Count bits in the lowest six positions, using structural Nat recursion.
def count_bits(+fuel: Nat, +bits: U32) -> U32:
  match fuel:
    case 0n:
      0
    case 1n+k:
      (U32.mod(bits, 2) + count_bits(k, U32.div(bits, 2)) : U32)

def fits(+bits: U32, +a: U32, +b: U32, +c: U32,
         +ra: U32, +rb: U32, +rc: U32,
         +total: U32, +use_total: Bool) -> Bool:
  Bool.and(U32.is_eq(count_bits(6n, U32.and(bits, a)), ra),
    Bool.and(U32.is_eq(count_bits(6n, U32.and(bits, b)), rb),
      Bool.and(U32.is_eq(count_bits(6n, U32.and(bits, c)), rc),
        Bool.or(Bool.not(use_total),
                U32.is_eq(count_bits(6n, bits), total)))))

def add_if(ok: Bool, +bits: U32, summary: Summary) -> Summary:
  match ok:
    case False{}:
      summary
    case True{}:
      match summary:
        case Summary{models, union, common}:
          Summary{(models + 1 : U32), U32.or(union, bits),
                  U32.and(common, bits)}

# Visit all 64 assignments. No search cutoff may masquerade as a proof.
def scan(+fuel: Nat, +a: U32, +b: U32, +c: U32,
         +ra: U32, +rb: U32, +rc: U32,
         +total: U32, +use_total: Bool, summary: Summary) -> Summary:
  match fuel:
    case 0n:
      summary
    case 1n+k:
      +bits = U32.from_nat(k)
      scan(k, a, b, c, ra, rb, rc, total, use_total,
           add_if(fits(bits, a, b, c, ra, rb, rc, total, use_total),
                  bits, summary))

def finish_empty(empty: Bool, +models: U32,
                 +union: U32, +common: U32) -> Decision:
  match empty:
    case True{}:
      Inconsistent{}
    case False{}:
      Forced{U32.and(U32.not(union), 63), common, models}

def finish(summary: Summary) -> Decision:
  match summary:
    case Summary{+models, union, common}:
      finish_empty(U32.is_eq(models, 0), models, union, common)

def valid_input(valid: Bool, +a: U32, +b: U32, +c: U32,
                +ra: U32, +rb: U32, +rc: U32,
                +total: U32, +use_total: Bool) -> Decision:
  match valid:
    case False{}:
      Inconsistent{}
    case True{}:
      finish(scan(64n, a, b, c, ra, rb, rc, total, use_total,
                  Summary{0, 0, 63}))

# a/b/c are six-bit SET masks of UNKNOWN neighbors, not cell indices.
# ra/rb/rc are residual mines after independently CERTIFIED deductions.
# use_total=False ignores total (which then has no evidential meaning).
# Out-of-range masks are rejected, not silently truncated.
def infer(+a: U32, +b: U32, +c: U32,
          +ra: U32, +rb: U32, +rc: U32,
          +total: U32, +use_total: Bool) -> Decision:
  valid_input(Bool.and(U32.is_lt(a, 64),
                Bool.and(U32.is_lt(b, 64), U32.is_lt(c, 64))),
              a, b, c, ra, rb, rc, total, use_total)

def score(decision: Decision) -> U32:
  match decision:
    case Inconsistent{}:
      0
    case Forced{safe, mines, models}:
      ((models * 100 + safe * 10 + mines) : U32)

# Hidden indices (1,3,4,5,6,8) map to bits (0,1,2,3,4,5).
# Revealed clues 0,2,7 each show 1; there are exactly two mines.
# A=000111 (7), B=001101 (13), C=111110 (62).
# Two models, safe mask 14 (3,4,5), mine mask 1 (cell 1): 341.
def main() -> U32:
  score(infer(7, 13, 62, 1, 1, 1, 2, True{}))
