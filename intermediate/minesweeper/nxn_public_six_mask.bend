# Translate a PUBLIC clue's unknown neighbors to a bounded six-bit mask.
# Universe positions 0..5 correspond to its six distinct, sorted cell IDs.
# A caller must construct this universe from public information only.
# No true mine mask, hidden clue number, or unverified flag is an input.
import Base
import ./nxn_public_neighbors.bend as Public
import ./nxn_public_subset.bend as Sets
import ./nxn_geometry.bend as Geo

type Mask is Type:
  Invalid{}
  Valid{bits: U32}

type Encoded is Data:
  Encoded{bits: U32, valid: Bool}

# A missing cell maps to zero; it is rejected by encode, not ignored.
# The Bool scrutinee is a parameter of this helper, as Bend requires.
def choose_bit(found: Bool, +power: U32, +otherwise: U32) -> U32:
  match found:
    case True{}:
      power
    case False{}:
      otherwise

def bit_of(+target: U32, universe: List<&2, U32>, +power: U32) -> U32:
  match universe:
    case Nil{}:
      0
    case cell <> rest:
      choose_bit(U32.is_eq(cell, target), power,
                 bit_of(target, rest, (power * 2 : U32)))

# Match the computed tail only after passing it as a function parameter.
def encoded_with_bit(+bit: U32, tail: Encoded) -> Encoded:
  match tail:
    case Encoded{bits, valid}:
      Encoded{U32.or(bit, bits),
              Bool.and(valid, Bool.not(U32.is_eq(bit, 0)))}

# Consume each unknown neighbor once. The universe is borrowed for lookup.
def encode(items: List<U32>, +universe: List<&2, U32>) -> Encoded:
  match items:
    case Nil{}:
      Encoded{0, True{}}
    case +index <> rest:
      +bit = bit_of(index, universe, 1)
      encoded_with_bit(bit, encode(rest, universe))

# Reject non-canonical universes: duplicate, revealed or out-of-board cells.
def ordered_hidden(+n: U32, cells: List<&2, U32>,
                   +revealed: List<&2, U32>,
                   +previous: U32, +first: Bool) -> Bool:
  match cells:
    case Nil{}:
      True{}
    case cell <> rest:
      +good = Bool.and(Geo.valid_index(n, cell),
                       Bool.not(Sets.contains(revealed, cell)))
      +ascending = Bool.or(first, U32.is_lt(previous, cell))
      Bool.and(good, Bool.and(ascending,
        ordered_hidden(n, rest, revealed, cell, False{})))

def finish_if(valid: Bool, +bits: U32) -> Mask:
  match valid:
    case True{}:
      Valid{bits}
    case False{}:
      Invalid{}

def finish(ok: Bool, encoded: Encoded) -> Mask:
  match encoded:
    case Encoded{bits, valid}:
      finish_if(Bool.and(ok, valid), bits)

# Precondition: revealed is a sorted, unique, in-range list.
# A clue must be revealed; every unknown neighbor must occur in universe.
# Exactly six universe cells are required (no zero-padding of five cells).
# Invalid and a legitimate empty mask are distinct results.
def mask_for(+n: U32, +clue: U32,
             +revealed: List<&2, U32>,
             +universe: List<&2, U32>) -> Mask:
  +ok = Bool.and(U32.is_eq(Sets.size(universe), 6),
          Bool.and(Geo.valid_index(n, clue),
            Bool.and(Sets.contains(revealed, clue),
              ordered_hidden(n, universe, revealed, 0, True{}))))
  finish(ok, encode(Public.unknown_neighbors(n, clue, revealed), universe))

def tag(mask: Mask) -> U32:
  match mask:
    case Invalid{}:
      64
    case Valid{bits}:
      bits

# Public clues 0, 2, 7 are revealed in a 3x3 board.
# Hidden universe (1,3,4,5,6,8): clue 0 has unknown neighbors 1,3,4.
def main() -> U32:
  tag(mask_for(3, 0, [0, 2, 7], [1, 3, 4, 5, 6, 8]))
