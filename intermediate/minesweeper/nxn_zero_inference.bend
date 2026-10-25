# Public-only N x N inference for one revealed zero clue (N=2..100).
# The caller must supply the actual displayed clue, not hidden mine truth.
# This is a sound local rule, NOT the general constraint solver or generator.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_neighbors.bend as Neighbors

def contains(items: List<&2, U32>, +target: U32) -> Bool:
  match items:
    case Nil{}:
      False{}
    case value <> rest:
      Bool.or(U32.is_eq(value, target), contains(rest, target))

def keep(eligible: Bool, +index: U32, rest: List<U32>) -> List<U32>:
  match eligible:
    case True{}:
      index <> rest
    case False{}:
      rest

# Preserve the neighbor list's ascending order, excluding opened/flagged cells.
def candidates(items: List<U32>, +opened: List<&2, U32>,
               +flags: List<&2, U32>) -> List<U32>:
  match items:
    case Nil{}:
      Nil{}
    # Index is inspected in multiple independent tests; mark it duplicable.
    case +index <> tail:
      eligible = Bool.and(
        Bool.not(contains(opened, index)),
        Bool.not(contains(flags, index)))
      keep(eligible, index, candidates(tail, opened, flags))

def if_zero(ok: Bool, +n: U32, +index: U32,
            opened: List<&2, U32>, flags: List<&2, U32>) -> List<U32>:
  match ok:
    case True{}:
      candidates(Neighbors.neighbors(n, index), opened, flags)
    case False{}:
      Nil{}

# opened contains public indices, flags are NOT assumed to be real mines.
# Only a valid, revealed zero produces safe candidates; all other clues do not.
# The input is assumed to be a consistent public view of a real game.
def safe_from_clue(+n: U32, +index: U32, +clue: U32,
                   +opened: List<&2, U32>, flags: List<&2, U32>) -> List<U32>:
  valid = Bool.and(U32.is_eq(clue, 0),
    Bool.and(Geo.valid_index(n, index), contains(opened, index)))
  if_zero(valid, n, index, opened, flags)

def main() -> U32:
  Neighbors.count(safe_from_clue(10, 0, 0, [0], Nil{}))
