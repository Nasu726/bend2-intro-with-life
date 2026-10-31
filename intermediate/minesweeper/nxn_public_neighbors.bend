# Derive a clue's UNKNOWN neighbors from PUBLIC revealed indices alone.
# The hidden mine layout and unverified player flags are not inputs.
# The revealed list must be unique, in-range, and sorted; the clue itself
# must be revealed. The N x N geometry module enforces 2 <= N <= 100.
import Base
import ./nxn_neighbors.bend as Neighbors
import ./nxn_public_subset.bend as Sets

def keep_hidden(visible: Bool, +index: U32, rest: List<U32>) -> List<U32>:
  match visible:
    case True{}:
      rest
    case False{}:
      index <> rest

def remove_revealed(items: List<U32>, +revealed: List<&2, U32>) -> List<U32>:
  match items:
    case Nil{}:
      Nil{}
    case +index <> rest:
      keep_hidden(Sets.contains(revealed, index), index,
                  remove_revealed(rest, revealed))

def if_revealed(yes: Bool, +n: U32, +index: U32,
                +revealed: List<&2, U32>) -> List<U32>:
  match yes:
    case False{}:
      Nil{}
    case True{}:
      remove_revealed(Neighbors.neighbors(n, index), revealed)

# A hidden clue index or invalid board index yields Nil (not evidence).
# For a revealed clue, the result is a sorted list of unknown neighbors.
# An empty result may also mean that all neighboring cells were opened.
def unknown_neighbors(+n: U32, +index: U32,
                      +revealed: List<&2, U32>) -> List<U32>:
  if_revealed(Sets.contains(revealed, index), n, index, revealed)

# 3 x 3: revealed cells 0, 2, 7. Unknown neighbors of clue 7
# are cells 3, 4, 5, 6, 8 (five cells).
def main() -> U32:
  Neighbors.count(unknown_neighbors(3, 7, [0, 2, 7]))
